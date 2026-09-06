import os
import re
import pickle
import numpy as np
import spacy
from rapidfuzz import fuzz, process
from sentence_transformers import SentenceTransformer, util

NEGATION_TRIGGERS = [
    r"\bno\b", r"\bnot\b", r"\bdenies\b", r"\bdenied\b",
    r"\bwithout\b", r"\babsence of\b", r"\bnegative for\b",
    r"\bnever had\b", r"\bfree of\b"
]

# ── Clinical Paraphrase Aliases ──
# Maps common clinical language to canonical symptom names.
# Applied during Layer 1a (exact substring matching) to bridge gaps
# that the embedding model cannot resolve above the 0.70 threshold.
SYMPTOM_ALIASES = {
    "nasal congestion": [
        "stuffiness in nose", "stuffy nose", "blocked nose",
        "nose blocked", "nasal stuffiness", "congested nose",
        "nose stuffed up", "nose feels stuffy", "nose feels blocked",
    ],
    "plugged feeling in ear": [
        "ear feels blocked", "ear feels plugged", "ear feels clogged",
        "blocked ear", "clogged ear", "plugged ear",
        "ear feels full", "fullness in ear",
    ],
    "sinus congestion": [
        "sinus pressure", "pressure in sinuses",
    ],
    "fainting": [
        "loss of consciousness", "lost consciousness", "passed out",
        "blacked out", "fainted",
    ],
    "seizures": [
        "convulsions", "seizure episode", "epileptic episode",
    ],
    "sweating": [
        "excessive sweating", "profuse sweating", "cold sweat",
    ],
    "wheezing": [
        "wheezy breathing", "whistling breath",
    ],
    "chest tightness": [
        "tightness in chest", "tight chest", "chest feels tight",
    ],
    "difficulty breathing": [
        "trouble breathing", "hard to breathe", "can not breathe",
        "difficulty with breathing", "breathing difficulty",
    ],
    "itchiness of eye": [
        "itchy eyes", "itchy watery eyes", "eyes itchy",
        "itching eyes", "itching of eyes", "itching in eyes",
    ],
    "skin dryness, peeling, scaliness, or roughness": [
        "peeling skin", "skin peeling", "dry peeling skin",
        "flaking skin", "scaly skin",
    ],
    "skin rash": [
        "red rash", "itchy rash", "itchy red rash",
        "rash on skin", "rash spreading",
    ],
    "diminished hearing": [
        "decreased hearing", "hearing loss", "reduced hearing",
        "hard of hearing", "can not hear",
    ],
    "heartburn": [
        "acid reflux", "burning behind breastbone",
        "burning pain behind breastbone",
    ],
}

# Noun chunks in this set are too generic to produce reliable semantic matches.
# They are excluded from Layer 2 embedding to prevent hallucinated symptom mappings.
GENERIC_STOP_CHUNKS = {
    "pain", "sharp pain", "mild pain", "severe pain", "acute pain",
    "dull pain", "chronic pain", "constant pain", "sudden pain",
    "side", "right side", "left side", "right", "left",
    "area", "region", "part", "spot", "problem", "problems",
    "feeling", "sensation", "thing", "stuff",
    "morning", "evening", "night", "day", "week", "month",
    "time", "times", "condition", "symptom", "issue",
    "history", "onset", "episode",
}

MAX_INPUT_LENGTH = 1000


class SecureSemanticExtractor:
    """
    Two-layer clinical NLP extractor with forward-index negation tracking.

    Layer 1: Exact substring matching (longest-first) + rapidfuzz token-fuzzy
             matching (≥90 ratio) for typo tolerance.
    Layer 2: spaCy noun-chunk semantic search via SentenceTransformer embeddings.
             Noun chunks are extended with prepositional complements and
             adjectival predicates from the dependency tree for richer semantics.

    Negation is tracked per-clause using a forward-index approach: a negation
    trigger (e.g., "denies") negates every symptom whose string position
    occurs strictly after the trigger's end position within the same clause.
    """

    def __init__(self, models_dir=None):
        if models_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            models_dir = os.path.join(base_dir, "models")

        # ── Symptom vocabulary ──
        # Keep ORIGINAL order (aligned with precomputed embeddings)
        with open(os.path.join(models_dir, "symptom_features.pkl"), "rb") as f:
            self.symptoms = pickle.load(f)

        # Sorted by descending length for greedy longest-first exact matching
        self.symptoms_by_length = sorted(self.symptoms, key=len, reverse=True)

        # ── Unified phrase→symptom mapping (base names + clinical aliases) ──
        self.phrase_to_symptom = {}
        for sym in self.symptoms:
            self.phrase_to_symptom[sym] = sym
        for sym, aliases in SYMPTOM_ALIASES.items():
            if sym in set(self.symptoms):
                for alias in aliases:
                    if alias not in self.phrase_to_symptom:
                        self.phrase_to_symptom[alias] = sym
        self.phrases_by_length = sorted(
            self.phrase_to_symptom.keys(), key=len, reverse=True
        )

        # ── Precomputed symptom embeddings (aligned with self.symptoms order) ──
        emb_path = os.path.join(models_dir, "symptom_embeddings.npy")
        if not os.path.exists(emb_path):
            raise FileNotFoundError(f"Missing '{emb_path}'. Run generate_embeddings.py first.")
        self.symptom_embeddings = np.load(emb_path)

        # ── Sentence encoder for noun-chunk embedding ──
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")

        # ── Negation detection ──
        self.neg_patterns = [re.compile(p, re.IGNORECASE) for p in NEGATION_TRIGGERS]
        self.neg_regex = re.compile("|".join(NEGATION_TRIGGERS), re.IGNORECASE)

        # ── spaCy linguistic parser ──
        try:
            self.spacy_nlp = spacy.load("en_core_web_sm")
        except OSError:
            from spacy.cli import download
            download("en_core_web_sm")
            self.spacy_nlp = spacy.load("en_core_web_sm")

    # ──────────────────────────────────────────────────────────
    #  Input Sanitisation
    # ──────────────────────────────────────────────────────────

    def _sanitize_input(self, text):
        if not isinstance(text, str):
            return ""
        cleaned = text[:MAX_INPUT_LENGTH]
        return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned).strip()

    # ──────────────────────────────────────────────────────────
    #  Clause Splitting (preserves and/or scope for negation)
    # ──────────────────────────────────────────────────────────

    def _split_clauses(self, text):
        """
        Split on sentence-ending punctuation (.!?;\\n) and contrastive
        conjunctions (but, however).  Do NOT split on 'and', 'or', or
        commas — those must stay inside the clause so that negation scope
        is preserved across coordinated items like "denies X or Y".
        """
        delimiters = r'[.!?;\n]|\bbut\b|\bhowever\b'
        parts = re.split(delimiters, text, flags=re.IGNORECASE)
        return [p.strip() for p in parts if len(p.strip()) >= 2]

    # ──────────────────────────────────────────────────────────
    #  Forward-Index Negation
    # ──────────────────────────────────────────────────────────

    def _find_negation_end_positions(self, clause_lower):
        """Return sorted list of character END-positions of negation triggers."""
        positions = []
        for pat in self.neg_patterns:
            for m in pat.finditer(clause_lower):
                positions.append(m.end())
        return sorted(positions)

    def _is_negated_at(self, char_pos, neg_end_positions):
        """True if *char_pos* falls at or after any negation trigger's end."""
        return any(char_pos >= ne for ne in neg_end_positions)

    # ──────────────────────────────────────────────────────────
    #  Span Helpers
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _spans_overlap(start, end, spans):
        """Check if [start, end) overlaps with any existing span."""
        return any(not (end <= s or start >= e) for s, e in spans)

    @staticmethod
    def _get_remaining_text(text, spans):
        """Blank out matched spans with spaces, collapse whitespace."""
        if not spans:
            return text
        chars = list(text)
        for s, e in spans:
            for i in range(s, min(e, len(chars))):
                chars[i] = ' '
        return re.sub(r'\s+', ' ', ''.join(chars)).strip()

    # ──────────────────────────────────────────────────────────
    #  spaCy Noun-Chunk Extraction with Dependency Extensions
    # ──────────────────────────────────────────────────────────

    def _extract_noun_chunks(self, text):
        """
        Use spaCy to extract noun chunks and extend them with:
          • prepositional complements  ("stuffiness" → "stuffiness in nose")
          • adjectival predicates       ("right ear" → "right ear blocked")
          • verb + adjective phrases    ("right ear" → "right ear feels blocked")

        Returns list of (lowered_text, char_start_in_doc) tuples.
        """
        doc = self.spacy_nlp(text)
        chunks = []

        for nc in doc.noun_chunks:
            ct = nc.text.strip()
            # Skip pronouns, single-char tokens, and generic non-medical subjects
            if len(ct) < 2 or nc.root.pos_ == 'PRON':
                continue
            if nc.root.text.lower() in ('patient', 'doctor', 'person', 'one'):
                continue

            base_start = nc.start_char
            chunks.append((ct.lower(), base_start))
            root = nc.root

            # ── Prepositional phrases: "stuffiness" → "stuffiness in nose" ──
            for child in root.children:
                if child.dep_ == 'prep':
                    sub = sorted(child.subtree, key=lambda t: t.i)
                    prep = ' '.join(t.text for t in sub)
                    chunks.append((f"{ct} {prep}".lower(), base_start))

            # ── Adjectival / verbal complements via head verb ──
            head = root.head
            if head.pos_ in ('VERB', 'AUX') and head.i != root.i:
                for child in head.children:
                    if child.dep_ in ('acomp', 'attr', 'oprd', 'ccomp', 'xcomp'):
                        if child.pos_ in ('ADJ', 'VERB', 'NOUN'):
                            # "noun + adj" variant: "right ear blocked"
                            chunks.append((f"{ct} {child.text}".lower(), base_start))
                            # "noun + verb + adj" variant: "right ear feels blocked"
                            chunks.append(
                                (f"{ct} {head.text} {child.text}".lower(), base_start)
                            )

        # Deduplicate by text, preserve insertion order
        seen = set()
        unique = []
        for text_lower, pos in chunks:
            if text_lower not in seen:
                seen.add(text_lower)
                unique.append((text_lower, pos))

        # Keep only the longest chunk per start position to maximise
        # semantic context and prevent short generic fragments
        # (e.g. "pain") from hallucinating unrelated symptoms.
        from collections import defaultdict
        pos_groups = defaultdict(list)
        for text_lower, pos in unique:
            pos_groups[pos].append((text_lower, pos))
        result = []
        for pos in sorted(pos_groups):
            group = pos_groups[pos]
            longest = max(group, key=lambda x: len(x[0]))
            result.append(longest)
        return result

    # ──────────────────────────────────────────────────────────
    #  Main Extraction Pipeline
    # ──────────────────────────────────────────────────────────

    def extract_symptoms(self, raw_text, similarity_threshold=0.70):
        safe_text = self._sanitize_input(raw_text)
        if not safe_text:
            return {"present": [], "negated": []}

        clauses = self._split_clauses(safe_text)
        present = set()
        negated = set()

        for clause in clauses:
            clause_lower = clause.lower()
            neg_ends = self._find_negation_end_positions(clause_lower)
            matched_spans = []          # character ranges already consumed

            # ═══════════════════════════════════════════════════════
            #  LAYER 1a — Exact Substring Match (longest-first)
            # ═══════════════════════════════════════════════════════
            for phrase in self.phrases_by_length:
                sym = self.phrase_to_symptom[phrase]
                pos = 0
                while True:
                    idx = clause_lower.find(phrase, pos)
                    if idx == -1:
                        break
                    end = idx + len(phrase)
                    if not self._spans_overlap(idx, end, matched_spans):
                        target = negated if self._is_negated_at(idx, neg_ends) else present
                        target.add(sym)
                        matched_spans.append((idx, end))
                    pos = idx + 1

            # ═══════════════════════════════════════════════════════
            #  LAYER 1b — Token-Fuzzy Match (typo tolerance, ≥ 90)
            # ═══════════════════════════════════════════════════════
            remaining = self._get_remaining_text(clause_lower, matched_spans)
            # Strip negation triggers so they don't pollute fuzzy comparison
            remaining_clean = self.neg_regex.sub(' ', remaining)
            remaining_clean = re.sub(r'\s+', ' ', remaining_clean).strip()

            if remaining_clean and len(remaining_clean) >= 4:
                words = remaining_clean.split()
                for wsize in range(min(4, len(words)), 0, -1):
                    for i in range(len(words) - wsize + 1):
                        ngram = ' '.join(words[i:i + wsize])
                        if len(ngram) < 4:
                            continue
                        result = process.extractOne(
                            ngram, self.symptoms,
                            scorer=fuzz.ratio,
                            score_cutoff=90
                        )
                        if result:
                            sym = result[0]
                            if sym not in present and sym not in negated:
                                gpos = clause_lower.find(ngram)
                                if gpos == -1:
                                    gpos = clause_lower.find(words[i])
                                is_neg = self._is_negated_at(
                                    gpos if gpos >= 0 else 0, neg_ends
                                )
                                target = negated if is_neg else present
                                target.add(sym)
                                if gpos >= 0:
                                    matched_spans.append((gpos, gpos + len(ngram)))

            # ═══════════════════════════════════════════════════════
            #  LAYER 2 — spaCy Noun-Chunk Semantic Search
            # ═══════════════════════════════════════════════════════
            noun_chunks = self._extract_noun_chunks(clause)

            # Keep only chunks whose base position doesn't overlap
            # with already-matched spans
            unmatched = []
            for ct, cstart in noun_chunks:
                # For extended chunks (longer than what's in the text),
                # use the base noun-chunk start for overlap detection
                cend = cstart + len(ct)
                if not self._spans_overlap(cstart, cend, matched_spans):
                    unmatched.append((ct, cstart))

            if unmatched:
                # Filter out overly generic chunks before embedding
                unmatched = [
                    (ct, cs) for ct, cs in unmatched
                    if ct not in GENERIC_STOP_CHUNKS
                ]

            if unmatched:
                texts = [u[0] for u in unmatched]
                embs = self.encoder.encode(texts, convert_to_tensor=True)
                cos = util.cos_sim(embs, self.symptom_embeddings).cpu().numpy()

                for i, (ct, cstart) in enumerate(unmatched):
                    best_idx = int(np.argmax(cos[i]))
                    best_sc = float(cos[i][best_idx])

                    if best_sc >= similarity_threshold:
                        sym = self.symptoms[best_idx]
                        if sym not in present and sym not in negated:
                            is_neg = self._is_negated_at(cstart, neg_ends)
                            target = negated if is_neg else present
                            target.add(sym)

        # Negated symptoms always override active
        present = sorted(present - negated)
        negated = sorted(negated)
        return {"present": present, "negated": negated}
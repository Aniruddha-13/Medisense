"""Diagnostic: check semantic similarity scores and spaCy noun chunks."""
import os, sys, pickle, numpy as np, spacy
from sentence_transformers import SentenceTransformer, util

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(BASE_DIR, "models")

with open(os.path.join(models_dir, "symptom_features.pkl"), "rb") as f:
    symptoms = pickle.load(f)

embs = np.load(os.path.join(models_dir, "symptom_embeddings.npy"))
encoder = SentenceTransformer("all-MiniLM-L6-v2")
nlp = spacy.load("en_core_web_sm")

text = "Patient reports headache, stuffiness in nose and right ear feels blocked"
doc = nlp(text)

print("=== SPACY NOUN CHUNKS ===")
for nc in doc.noun_chunks:
    root = nc.root
    head = root.head
    print(f"  chunk='{nc.text}' root='{root.text}' pos={root.pos_} dep={root.dep_} head='{head.text}' head.pos={head.pos_}")
    for child in root.children:
        print(f"    root-child: '{child.text}' dep={child.dep_} pos={child.pos_}")
    for child in head.children:
        print(f"    head-child: '{child.text}' dep={child.dep_} pos={child.pos_}")

print("\n=== DEP PARSE ===")
for tok in doc:
    print(f"  {tok.i}: '{tok.text}' pos={tok.pos_} dep={tok.dep_} head='{tok.head.text}' head.i={tok.head.i}")

test_phrases = [
    "stuffiness", "stuffiness in nose", "nose", "stuffy nose", "nasal stuffiness",
    "right ear", "right ear blocked", "right ear feels blocked",
    "ear feels blocked", "blocked ear", "plugged ear",
    "cold", "suspects cold",
]

# Find indices of target symptoms
nc_idx = symptoms.index("nasal congestion") if "nasal congestion" in symptoms else -1
pf_idx = symptoms.index("plugged feeling in ear") if "plugged feeling in ear" in symptoms else -1
ep_idx = symptoms.index("ear pain") if "ear pain" in symptoms else -1

print(f"\nTarget symptom indices: nasal_congestion={nc_idx}, plugged_feeling_in_ear={pf_idx}, ear_pain={ep_idx}")

test_embs = encoder.encode(test_phrases, convert_to_tensor=True)
cos = util.cos_sim(test_embs, embs).cpu().numpy()

print("\n=== COSINE SIMILARITY SCORES ===")
for i, phrase in enumerate(test_phrases):
    best_idx = int(np.argmax(cos[i]))
    best_sc = float(cos[i][best_idx])
    nc_sc = float(cos[i][nc_idx]) if nc_idx >= 0 else -1
    pf_sc = float(cos[i][pf_idx]) if pf_idx >= 0 else -1
    ep_sc = float(cos[i][ep_idx]) if ep_idx >= 0 else -1

    print(f"\n  '{phrase}':")
    print(f"    BEST: '{symptoms[best_idx]}' = {best_sc:.4f}")
    print(f"    nasal congestion    = {nc_sc:.4f}")
    print(f"    plugged feeling ear = {pf_sc:.4f}")
    print(f"    ear pain            = {ep_sc:.4f}")
    # top 3
    top3 = np.argsort(cos[i])[::-1][:3]
    for rank, tidx in enumerate(top3):
        print(f"    top-{rank+1}: '{symptoms[tidx]}' = {float(cos[i][tidx]):.4f}")

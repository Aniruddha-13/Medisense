# MediSense Clinical Pipeline QA & Architecture Audit Report

## 1. Executive Summary
- Overall Test Cases Run: 25
- Pass Rate: 76% (19/25)
- Critical Failures (Level 1/Safety): 3
- High-Priority Regressions: 3

## 2. Detailed Test Matrix by Category
| Test ID | Category | Narrative Input | Demographic Profile | Expected Output | Actual Output | Status (PASS/FAIL) | Severity |
|---|---|---|---|---|---|---|---|
| T1.1 | 1. Entity Extraction | I have a blocked nose. | {} | Active symptoms include 'nasal congestion' | ['nasal congestion'] | PASS | P1 |
| T1.2 | 1. Entity Extraction | feels like my head is in a vice | {} | Active symptoms include 'headache' | Error | FAIL | P2 |
| T1.3 | 1. Entity Extraction | heart is racing like a horse | {} | Active symptoms include 'palpitations' | Error | FAIL | P2 |
| T1.4 | 1. Entity Extraction | feeling under the weather | {} | No specific clinical entity extracted, or minimal matches (should not hallucinate serious illness) | Properly caught as no symptoms | PASS | P2 |
| T1.5 | 1. Entity Extraction | I passed out yesterday | {} | Active symptoms include 'fainting' or 'loss of consciousness' | ['fainting'] | PASS | P1 |
| T2.1 | 2. Negation Tracking | Denies nausea, vomiting, chest tightness, or chills. | {} | Negated symptoms include nausea, vomiting, chest tightness, chills | Error | FAIL | P0 |
| T2.2 | 2. Negation Tracking | Patient denies fever and cough, but reports severe dyspnea. | {} | fever and cough in negated, shortness of breath (dyspnea) in active | Error | FAIL | P0 |
| T2.3 | 2. Negation Tracking | Patient has fever and cough; denies nausea. | {} | fever and cough in active, nausea negated | Active: ['cough', 'fever'], Negated: ['nausea'] | PASS | P1 |
| T2.4 | 2. Negation Tracking | No headache. | {} | active is empty, headache is negated | Active: [], Negated: ['headache'] | PASS | P0 |
| T2.5 | 2. Negation Tracking | free of skin rash | {} | rash is negated | Negated: ['skin rash'] | PASS | P1 |
| T3.1 | 3. Guardrails | severe lower pelvic and abdominal pain | {'sex': 'Male'} | No female obstetric conditions in differential | Differential: ['diverticulitis', 'cystitis', 'appendicitis'] | PASS | P0 |
| T3.2 | 3. Guardrails | severe lower pelvic and abdominal pain | {'sex': 'Female', 'is_pregnant': False} | Female obstetric conditions allowed for female | Differential: ['diverticulitis', 'cystitis', 'appendicitis'] | PASS | P1 |
| T3.3 | 3. Guardrails | severe nausea and vomiting in morning | {'sex': 'Female', 'is_pregnant': False} | No gestational conditions in differential if not pregnant | Differential: ['pain after an operation', 'chronic constipation', 'appendicitis'] | PASS | P0 |
| T3.4 | 3. Guardrails | severe nausea and vomiting in morning | {'sex': 'Female', 'is_pregnant': True} | Gestational conditions allowed if pregnant | Differential: ['pain after an operation', 'chronic constipation', 'appendicitis'] | PASS | P1 |
| T3.5 | 3. Guardrails | severe nausea and vomiting | {'sex': 'Male'} | Check differential doesn't return empty for male with pregnancy symptoms (should return non-pregnancy diseases) | Differential: ['pain after an operation', 'chronic constipation', 'appendicitis'] | PASS | P1 |
| T4.1 | 4. Triage Calibration | sharp chest pain and shortness of breath | {} | EMERGENCY (Level 1) triage level | EMERGENCY (Level 1) | PASS | P0 |
| T4.2 | 4. Triage Calibration | patient lost consciousness and is coughing up blood | {} | EMERGENCY (Level 1) triage level | ROUTINE CONSULT (Level 3) | FAIL | P0 |
| T4.3 | 4. Triage Calibration | fever, vomiting, and abdominal pain | {} | URGENT CARE (Level 2) triage level | URGENT CARE (Level 2) | PASS | P1 |
| T4.4 | 4. Triage Calibration | mild headache and nasal congestion | {} | ROUTINE CONSULT (Level 3) triage level | ROUTINE CONSULT (Level 3) | PASS | P1 |
| T4.5 | 4. Triage Calibration | patient denies sharp chest pain and shortness of breath | {} | Negated red flags do NOT trigger EMERGENCY. Should be error (no active) or Routine. |  | PASS | P0 |
| T5.1 | 5. Adversarial/Edge Cases |  | {} | Handles empty string without crashing, returns error status | error | PASS | P1 |
| T5.2 | 5. Adversarial/Edge Cases |       | {} | Handles whitespace-only string without crashing | error | PASS | P1 |
| T5.3 | 5. Adversarial/Edge Cases | pain pain... (2000 times) | {} | Handles long input correctly (truncates or processes) without crashing | error | PASS | P2 |
| T5.4 | 5. Adversarial/Edge Cases | no, none, denied, neither, not at all | {} | Pure negation strings return no active symptoms | [] | PASS | P1 |
| T5.5 | 5. Adversarial/Edge Cases | Patient presents with acute myocardial infarction indicators, severe diaphoresis, and angina pectoris. | {} | Heavy clinical jargon test | Error | FAIL | P2 |

## 3. Root Cause Analysis of Identified Bugs
- **Bug Description**: Colloquial metaphors and heavy jargon are not mapped to clinical entities.
- **Failing Input**: "feels like my head is in a vice" (T1.2), "heart is racing like a horse" (T1.3), "Patient presents with acute myocardial infarction indicators..." (T5.5)
- **Observed Behavior**: Returns empty active symptoms, yielding an error status from the pipeline.
- **Underlying Root Cause**: `nlp_extractor.py` relies on `SYMPTOM_ALIASES` for exact substrings, and generic noun chunking with SentenceTransformers. Highly figurative language or complex clinical jargon fails to hit the 0.70 similarity threshold for any standard symptom.

- **Bug Description**: Multi-symptom forward scoping and bidirectional transitions with missing entities break pipeline status.
- **Failing Input**: "Denies nausea, vomiting, chest tightness, or chills." (T2.1), "Patient denies fever and cough, but reports severe dyspnea." (T2.2)
- **Observed Behavior**: The pipeline evaluates to `error` and fails to continue triage.
- **Underlying Root Cause**: In `pipeline.py`, lines 46-52 short-circuit with an "error" if `active_symptoms` is empty, completely discarding valid negation tracking. Furthermore, in T2.2, "dyspnea" is not in the `SYMPTOM_ALIASES` map or doesn't match above threshold, so it extracts no active symptoms, triggering the same pipeline short-circuit.

- **Bug Description**: Critical red flags downgraded to Routine Consult.
- **Failing Input**: "patient lost consciousness and is coughing up blood" (T4.2)
- **Observed Behavior**: Triage engine maps to ROUTINE CONSULT (Level 3) rather than EMERGENCY.
- **Underlying Root Cause**: `triage_engine.py` explicitly lists `"loss of consciousness"` and `"coughing up blood"`, but the `nlp_extractor.py` maps these to `"fainting"` and `"cough"`. Since `"fainting"` and `"cough"` are not in `triage_engine.py`'s `emergency_symptoms` set, the urgency is completely miscalibrated.

## 4. Edge Cases & Safety Gaps
- **Negation Scope Boundary Failures**: The pipeline aborts entirely when only negated symptoms are identified. This is a poor architectural decision in `pipeline.py` because negated symptoms are valid clinical signals (e.g., confirming a patient *doesn't* have chest pain is vital context).
- **Semantic Similarity Score Distribution**: The 0.70 threshold is too rigid for highly figurative language (false negatives) and medical jargon.
- **Demographic Filtering Gaps**: Guardrails work as expected for removing impossible conditions (e.g., ovarian cysts in males).

## 5. Prioritized Engineering Action Items
- **P0 (Immediate Safety/Accuracy Fixes)**: 
  - Fix `triage_engine.py` to synchronize its `emergency_symptoms` set with the canonical outputs of `nlp_extractor.py` (e.g., map "fainting" to emergency flags if "loss of consciousness" is the intended trigger).
  - Remove the short-circuit error in `pipeline.py` when `active_symptoms` is empty. Allow the pipeline to return successfully with just `negated_symptoms`.
- **P1 (NLP & Embedding Optimization)**: 
  - Expand `SYMPTOM_ALIASES` in `nlp_extractor.py` to include clinical jargon (e.g., "dyspnea" -> "shortness of breath", "diaphoresis" -> "sweating").
  - Fine-tune or lower the semantic similarity threshold slightly to capture colloquialisms.
- **P2 (UX/UI & Diagnostics)**: 
  - Add telemetry to log out-of-vocabulary terms (like "dyspnea") to continuously improve the aliases map.

"""
Reproducer for the NLP hallucination + negation-leakage bug.

Input text:
  "Patient reports headache, stuffiness in nose and right ear feels blocked.
   Suspects cold, but denies chest pain or vomiting."

Expected behaviour after the fix:
  Active:   headache, nasal congestion, plugged feeling in ear
  Negated:  chest pain / sharp chest pain, vomiting
  No hallucinations: delusions or hallucinations, regurgitation,
                     regurgitation.1, temper problems must NOT be active.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from nlp_extractor import SecureSemanticExtractor

# ── Setup ──
extractor = SecureSemanticExtractor()

INPUT_TEXT = (
    "Patient reports headache, stuffiness in nose and right ear feels blocked. "
    "Suspects cold, but denies chest pain or vomiting."
)

# ── Run extraction ──
result = extractor.extract_symptoms(INPUT_TEXT)
active = result["present"]
neg = result["negated"]

print("=" * 65)
print("  TEST BUG REPRODUCER — Hallucination & Negation-Leak Check")
print("=" * 65)
print(f"\n  Input:   \"{INPUT_TEXT}\"")
print(f"  Active:  {active}")
print(f"  Negated: {neg}\n")

# ── Assertions ──
errors = []

# 1. Expected ACTIVE symptoms must be present
EXPECTED_ACTIVE = ["headache", "nasal congestion", "plugged feeling in ear"]
for sym in EXPECTED_ACTIVE:
    if sym not in active:
        errors.append(f"MISSING ACTIVE: '{sym}' not in active list")

# 2. Expected NEGATED symptoms must be in negated list
if "vomiting" not in neg:
    errors.append("MISSING NEGATED: 'vomiting' not found in negated list")
if "vomiting" in active:
    errors.append("NEGATION LEAK: 'vomiting' leaked into active list")

# 3. Chest-pain variants must be negated, never active
chest_pain_in_negated = any("chest pain" in s for s in neg)
chest_pain_in_active = any("chest pain" in s for s in active)

if not chest_pain_in_negated:
    errors.append("MISSING NEGATED: no 'chest pain' variant in negated list")
if chest_pain_in_active:
    errors.append("NEGATION LEAK: a 'chest pain' variant leaked into active list")

# 4. Hallucinated symptoms must NOT appear in active
HALLUCINATIONS = [
    "delusions or hallucinations",
    "regurgitation",
    "regurgitation.1",
    "temper problems",
    "sharp chest pain",        # should be negated, not active
]
for h in HALLUCINATIONS:
    if h in active:
        errors.append(f"HALLUCINATION: '{h}' found in active list")

# ── Report ──
if errors:
    print("[FAIL] TEST FAILED")
    for e in errors:
        print(f"   • {e}")
    print()
    sys.exit(1)
else:
    print("[PASS] ALL ASSERTIONS PASSED -- no hallucinations, no negation leaks\n")
    sys.exit(0)

import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from pipeline import MediSensePipeline

pipeline = MediSensePipeline()

# Test cases simulating real clinical variations
test_scenarios = [
    {
        "case_name": "1. Respiratory / Cold (Colloquial language)",
        "note": "Patient has stuffness in nose, headache, and blocked feeling in ear. Denies chest pain and vomiting.",
        "profile": {"sex": "Male", "is_pregnant": False},
        "expected_active": ["nasal congestion", "plugged feeling in ear"],
        "expected_negated": ["chest pain", "vomiting"],
        "should_not_contain": ["pregnancy"]
    },
    {
        "case_name": "2. Acute Cardiac Emergency (Red-flag triage)",
        "note": "Sudden onset of sharp chest pain, shortness of breath, and palpitations. No fever.",
        "profile": {"sex": "Male", "is_pregnant": False},
        "expected_triage": "EMERGENCY (Level 1)",
        "expected_active": ["sharp chest pain", "shortness of breath", "palpitations"]
    },
    {
        "case_name": "3. Female Demographic Guardrail Check",
        "note": "Headache, nausea, and morning sickness.",
        "profile": {"sex": "Male", "is_pregnant": False},
        "should_not_contain": ["pregnancy", "vulvodynia", "vaginal cyst"]
    }
]

print("\n=======================================================")
print("     🔬 RUNNING END-TO-END PIPELINE ACCURACY TESTS     ")
print("=======================================================\n")

for case in test_scenarios:
    print(f"Running: {case['case_name']}")
    result = pipeline.analyze(case["note"], patient_profile=case["profile"])

    if result.get("status") == "error":
        print(f"  ❌ FAILED: {result['message']}\n")
        continue

    active = result.get("active_symptoms", [])
    negated = result.get("negated_symptoms", [])
    triage_level = result["triage"]["triage_level"]
    top_preds = [p["disease"] for p in result["predictions"]]

    print(f"  - Input Note:        \"{case['note']}\"")
    print(f"  - Extracted Active:  {active}")
    print(f"  - Extracted Negated: {negated}")
    print(f"  - Triage Level:      {triage_level}")
    print(f"  - Top Predictions:   {top_preds}")

    # Assertions / Checks
    passed = True
    if "expected_triage" in case and case["expected_triage"] not in triage_level:
        print(f"  ⚠️ Warning: Expected triage {case['expected_triage']}, got {triage_level}")
        passed = False

    if "should_not_contain" in case:
        for forbidden in case["should_not_contain"]:
            if any(forbidden in p.lower() for p in top_preds):
                print(f"  ❌ Failed guardrail: Found '{forbidden}' in predictions for a male profile!")
                passed = False

    if passed:
        print("  ✅ Status: PASSED")
    print("-" * 55)
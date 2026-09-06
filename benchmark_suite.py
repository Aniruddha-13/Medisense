import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from pipeline import MediSensePipeline

pipeline = MediSensePipeline()

# 20 diverse, realistic clinical intake notes across specialties and edge cases
BENCHMARK_CASES = [
    # --- CARDIOLOGY & EMERGENCY ---
    {
        "id": "CARD-01",
        "category": "Cardiology",
        "note": "Sudden onset crushing chest pain, shortness of breath, and excessive sweating. Denies cough or fever.",
        "profile": {"sex": "Male", "age": 58, "is_pregnant": False},
        "expected_triage": "EMERGENCY (Level 1)",
        "expected_disease_keywords": ["Heart Attack", "Angina", "Myocardial", "Coronary"]
    },
    {
        "id": "CARD-02",
        "category": "Cardiology",
        "note": "Palpitations, irregular heartbeat, and mild dizziness after climbing stairs. No chest pain.",
        "profile": {"sex": "Female", "age": 64, "is_pregnant": False},
        "expected_triage": "URGENT CARE (Level 2)",
        "expected_disease_keywords": ["Arrhythmia", "Atrial", "Fibrillation", "Bradycardia", "Heart"]
    },

    # --- PULMONOLOGY & RESPIRATORY ---
    {
        "id": "RESP-01",
        "category": "Pulmonology",
        "note": "High fever, productive cough with yellow sputum, and sharp chest pain when breathing deeply.",
        "profile": {"sex": "Male", "age": 45, "is_pregnant": False},
        "expected_triage": "EMERGENCY (Level 1)",
        "expected_disease_keywords": ["Pneumonia", "Bronchitis", "Pleurisy"]
    },
    {
        "id": "RESP-02",
        "category": "Pulmonology",
        "note": "Wheezing, shortness of breath, and tightness in chest triggered by cold air. Denies fever.",
        "profile": {"sex": "Female", "age": 22, "is_pregnant": False},
        "expected_triage": "EMERGENCY (Level 1)",
        "expected_disease_keywords": ["Asthma", "Bronchitis"]
    },

    # --- ENT & ALLERGY ---
    {
        "id": "ENT-01",
        "category": "ENT / Allergy",
        "note": "Runny nose, nasal congestion, sneezing, and itchy watery eyes for past two weeks. No fever.",
        "profile": {"sex": "Male", "age": 29, "is_pregnant": False},
        "expected_triage": "ROUTINE CONSULT (Level 3)",
        "expected_disease_keywords": ["Allergies", "Rhinitis", "Sinusitis", "Cold"]
    },
    {
        "id": "ENT-02",
        "category": "ENT / Allergy",
        "note": "Sharp pain in right ear, feeling of plugged ear, and decreased hearing. Denies headache or nausea.",
        "profile": {"sex": "Male", "age": 35, "is_pregnant": False},
        "expected_triage": "ROUTINE CONSULT (Level 3)",
        "expected_disease_keywords": ["Otitis", "Ear", "Eustachian"]
    },

    # --- GASTROENTEROLOGY ---
    {
        "id": "GASTRO-01",
        "category": "Gastroenterology",
        "note": "Acute sharp abdominal pain in lower right quadrant, high fever, and vomiting. No chest pain.",
        "profile": {"sex": "Female", "age": 19, "is_pregnant": False},
        "expected_triage": "URGENT CARE (Level 2)",
        "expected_disease_keywords": ["Appendicitis", "Gastroenteritis", "Abdominal"]
    },
    {
        "id": "GASTRO-02",
        "category": "Gastroenterology",
        "note": "Burning pain behind breastbone after meals, acid reflux, and difficulty swallowing. Denies shortness of breath.",
        "profile": {"sex": "Male", "age": 42, "is_pregnant": False},
        "expected_triage": "ROUTINE CONSULT (Level 3)",
        "expected_disease_keywords": ["Gerd", "Reflux", "Esophagitis", "Hiatal Hernia", "Heartburn"]
    },

    # --- NEUROLOGY ---
    {
        "id": "NEURO-01",
        "category": "Neurology",
        "note": "Severe throbbing frontal headache on left side with nausea and sensitivity to light. Denies fever or neck stiffness.",
        "profile": {"sex": "Female", "age": 31, "is_pregnant": False},
        "expected_triage": "URGENT CARE (Level 2)",
        "expected_disease_keywords": ["Migraine", "Headache"]
    },
    {
        "id": "NEURO-02",
        "category": "Neurology",
        "note": "Loss of consciousness for two minutes followed by confusion and abnormal involuntary movements.",
        "profile": {"sex": "Male", "age": 50, "is_pregnant": False},
        "expected_triage": "EMERGENCY (Level 1)",
        "expected_disease_keywords": ["Seizure", "Syncope", "Epilepsy", "Stroke", "Concussion"]
    },

    # --- DEMOGRAPHIC & PREGNANCY GUARDRAIL VALIDATION ---
    {
        "id": "GUARD-01",
        "category": "Demographic Guardrail",
        "note": "Severe morning nausea, vomiting, and fatigue for 3 consecutive weeks.",
        "profile": {"sex": "Male", "age": 28, "is_pregnant": False},
        "forbidden_conditions": ["pregnancy", "hyperemesis gravidarum", "ovarian", "cervicitis"],
        "expected_triage": "URGENT CARE (Level 2)"
    },
    {
        "id": "GUARD-02",
        "category": "Demographic Guardrail",
        "note": "Severe morning nausea, vomiting, and fatigue for 3 consecutive weeks.",
        "profile": {"sex": "Female", "age": 28, "is_pregnant": True},
        "expected_disease_keywords": ["Pregnancy", "Hyperemesis", "Gastroenteritis"]
    },

    # --- COMPLEX NEGATION DRILLS ---
    {
        "id": "NEG-01",
        "category": "Negation Drill",
        "note": "Patient presents with headache. Completely denies chest pain, denies shortness of breath, and free of fever.",
        "profile": {"sex": "Female", "age": 40, "is_pregnant": False},
        "expected_active": ["headache"],
        "forbidden_active": ["chest pain", "shortness of breath", "fever"]
    },
    {
        "id": "NEG-02",
        "category": "Negation Drill",
        "note": "Negative for vomiting, negative for nausea, negative for diarrhea. Complaining of severe sore throat and fever.",
        "profile": {"sex": "Male", "age": 24, "is_pregnant": False},
        "expected_active": ["sore throat", "fever"],
        "forbidden_active": ["vomiting", "nausea", "diarrhea"]
    },

    # --- DERMATOLOGY & MUSCULOSKELETAL ---
    {
        "id": "DERM-01",
        "category": "Dermatology",
        "note": "Itchy red rash spreading over arms and torso with peeling skin. Denies difficulty breathing or facial swelling.",
        "profile": {"sex": "Male", "age": 33, "is_pregnant": False},
        "expected_triage": "ROUTINE CONSULT (Level 3)",
        "expected_disease_keywords": ["Dermatitis", "Eczema", "Psoriasis", "Skin", "Allergy"]
    },
    {
        "id": "MSK-01",
        "category": "Musculoskeletal",
        "note": "Sharp joint pain, swelling, and morning stiffness in both knees and fingers. No fever.",
        "profile": {"sex": "Female", "age": 55, "is_pregnant": False},
        "expected_triage": "ROUTINE CONSULT (Level 3)",
        "expected_disease_keywords": ["Arthritis", "Osteoarthritis", "Gout", "Joint"]
    },

    # --- ENDOCRINE / SYSTEMIC ---
    {
        "id": "ENDO-01",
        "category": "Endocrine",
        "note": "Excessive thirst, frequent urination, unexplained weight loss, and extreme fatigue.",
        "profile": {"sex": "Male", "age": 48, "is_pregnant": False},
        "expected_triage": "ROUTINE CONSULT (Level 3)",
        "expected_disease_keywords": ["Diabetes", "Hyperglycemia", "Thyroid"]
    },

    # --- RED-FLAG EMERGENCY SAFETY DRILL ---
    {
        "id": "EMERG-01",
        "category": "Emergency Safety",
        "note": "Patient coughing up blood with acute chest tightness and rapid breathing.",
        "profile": {"sex": "Male", "age": 60, "is_pregnant": False},
        "expected_triage": "EMERGENCY (Level 1)",
        "expected_active": ["coughing up blood"]
    },
    {
        "id": "EMERG-02",
        "category": "Emergency Safety",
        "note": "Sudden sharp tearing chest pain radiating to the back with severe shortness of breath.",
        "profile": {"sex": "Female", "age": 67, "is_pregnant": False},
        "expected_triage": "EMERGENCY (Level 1)"
    },
    {
        "id": "ROUTINE-01",
        "category": "Routine Follow-up",
        "note": "Mild fatigue and dry skin during winter months. Denies weight change or fever.",
        "profile": {"sex": "Male", "age": 25, "is_pregnant": False},
        "expected_triage": "ROUTINE CONSULT (Level 3)"
    }
]

def run_benchmark():
    print("=" * 80)
    print("      MEDISENSE CLINICAL BENCHMARK & STRESS-TEST SUITE (20 CASES)")
    print("=" * 80)

    results_table = []
    passed_count = 0

    for case in BENCHMARK_CASES:
        res = pipeline.analyze(case["note"], patient_profile=case["profile"])

        if res.get("status") == "error":
            print(f"[{case['id']}] [FAIL] ERROR: {res.get('message')}")
            results_table.append({
                "ID": case["id"],
                "Category": case["category"],
                "Triage Match": "ERROR",
                "Entity Extraction": "FAIL",
                "Differential Match": "FAIL",
                "Overall": "FAIL"
            })
            continue

        active = res.get("active_symptoms", [])
        negated = res.get("negated_symptoms", [])
        triage = res["triage"]["triage_level"]
        preds = [p["disease"] for p in res["predictions"]]
        top_pred = preds[0] if preds else "None"

        # Evaluation criteria
        triage_pass = True
        if "expected_triage" in case:
            triage_pass = case["expected_triage"].split()[0] in triage

        entity_pass = True
        if "forbidden_active" in case:
            for bad in case["forbidden_active"]:
                if any(bad in a for a in active):
                    entity_pass = False

        differential_pass = True
        if "forbidden_conditions" in case:
            for bad in case["forbidden_conditions"]:
                if any(bad in p.lower() for p in preds):
                    differential_pass = False

        if "expected_disease_keywords" in case:
            has_match = any(
                any(kw.lower() in p.lower() for kw in case["expected_disease_keywords"])
                for p in preds
            )
            if not has_match:
                differential_pass = False

        case_passed = triage_pass and entity_pass and differential_pass
        if case_passed:
            passed_count += 1

        status_str = "[PASS]" if case_passed else "[REVIEW]"

        print(f"\n[{case['id']}] {case['category']} -> {status_str}")
        print(f"  Note:      \"{case['note'][:75]}...\"")
        print(f"  Active:    {active}")
        print(f"  Negated:   {negated}")
        print(f"  Triage:    {triage} (Expected: {case.get('expected_triage', 'N/A')})")
        print(f"  Top Preds: {preds[:3]}")

        results_table.append({
            "ID": case["id"],
            "Category": case["category"],
            "Triage Match": "PASS" if triage_pass else "FAIL",
            "Entity/Negation": "PASS" if entity_pass else "FAIL",
            "Differential Match": "PASS" if differential_pass else "WARN",
            "Result": status_str
        })

    # Summary Report Table
    df_res = pd.DataFrame(results_table)
    summary_path = os.path.join(BASE_DIR, "benchmark_results.csv")
    df_res.to_csv(summary_path, index=False)

    print("\n" + "=" * 80)
    print(f"               BENCHMARK SUMMARY: {passed_count} / {len(BENCHMARK_CASES)} PASSED ({(passed_count/len(BENCHMARK_CASES))*100:.1f}%)")
    print("=" * 80)
    print(df_res.to_string(index=False))
    print(f"\nDetailed CSV benchmark exported to: '{summary_path}'")

if __name__ == "__main__":
    run_benchmark()
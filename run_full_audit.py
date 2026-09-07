import sys
import os
import json
import traceback

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from pipeline import MediSensePipeline

def evaluate_test_case(pipeline, test_id, category, narrative, profile, expected_func, severity):
    try:
        result = pipeline.analyze(narrative, patient_profile=profile)
        status, actual_output = expected_func(result)
        
        return {
            "Test ID": test_id,
            "Category": category,
            "Narrative Input": narrative,
            "Demographic Profile": str(profile),
            "Expected Output": expected_func.__doc__,
            "Actual Output": actual_output,
            "Status": "PASS" if status else "FAIL",
            "Severity": severity,
            "Raw Result": result
        }
    except Exception as e:
        return {
            "Test ID": test_id,
            "Category": category,
            "Narrative Input": narrative,
            "Demographic Profile": str(profile),
            "Expected Output": expected_func.__doc__,
            "Actual Output": f"Exception: {str(e)}",
            "Status": "FAIL",
            "Severity": severity,
            "Raw Result": None
        }

def run_tests():
    pipeline = MediSensePipeline()
    results = []

    # 1. Clinical Entity Extraction & Semantic Precision
    def t1_eval(r):
        """Active symptoms include 'nasal congestion'"""
        if r.get('status') == 'error': return False, "Error"
        return "nasal congestion" in r.get("active_symptoms", []), str(r.get("active_symptoms", []))
    results.append(evaluate_test_case(pipeline, "T1.1", "1. Entity Extraction", "I have a blocked nose.", {}, t1_eval, "P1"))

    def t1_2_eval(r):
        """Active symptoms include 'headache'"""
        if r.get('status') == 'error': return False, "Error"
        return "headache" in r.get("active_symptoms", []), str(r.get("active_symptoms", []))
    results.append(evaluate_test_case(pipeline, "T1.2", "1. Entity Extraction", "feels like my head is in a vice", {}, t1_2_eval, "P2"))

    def t1_3_eval(r):
        """Active symptoms include 'palpitations'"""
        if r.get('status') == 'error': return False, "Error"
        return "palpitations" in r.get("active_symptoms", []), str(r.get("active_symptoms", []))
    results.append(evaluate_test_case(pipeline, "T1.3", "1. Entity Extraction", "heart is racing like a horse", {}, t1_3_eval, "P2"))

    def t1_4_eval(r):
        """No specific clinical entity extracted, or minimal matches (should not hallucinate serious illness)"""
        if r.get('status') == 'error': return True, "Properly caught as no symptoms"
        return len(r.get("active_symptoms", [])) == 0, str(r.get("active_symptoms", []))
    results.append(evaluate_test_case(pipeline, "T1.4", "1. Entity Extraction", "feeling under the weather", {}, t1_4_eval, "P2"))

    def t1_5_eval(r):
        """Active symptoms include 'fainting' or 'loss of consciousness'"""
        if r.get('status') == 'error': return False, "Error"
        return any(s in ["fainting", "loss of consciousness"] for s in r.get("active_symptoms", [])), str(r.get("active_symptoms", []))
    results.append(evaluate_test_case(pipeline, "T1.5", "1. Entity Extraction", "I passed out yesterday", {}, t1_5_eval, "P1"))


    # 2. Negation Tracking & Scope Boundaries
    def t2_1_eval(r):
        """Negated symptoms include nausea, vomiting, chest tightness, chills"""
        if r.get('status') == 'error': return False, "Error"
        neg = r.get("negated_symptoms", [])
        expected = ["nausea", "vomiting", "chest tightness", "chills"]
        actual_str = str(neg)
        pass_test = all(any(e in n for n in neg) for e in expected)
        return pass_test, actual_str
    results.append(evaluate_test_case(pipeline, "T2.1", "2. Negation Tracking", "Denies nausea, vomiting, chest tightness, or chills.", {}, t2_1_eval, "P0"))

    def t2_2_eval(r):
        """fever and cough in negated, shortness of breath (dyspnea) in active"""
        if r.get('status') == 'error': return False, "Error"
        active = r.get("active_symptoms", [])
        neg = r.get("negated_symptoms", [])
        pass_test = any("fever" in n for n in neg) and any("cough" in n for n in neg) and any("shortness of breath" in a for a in active)
        return pass_test, f"Active: {active}, Negated: {neg}"
    results.append(evaluate_test_case(pipeline, "T2.2", "2. Negation Tracking", "Patient denies fever and cough, but reports severe dyspnea.", {}, t2_2_eval, "P0"))

    def t2_3_eval(r):
        """fever and cough in active, nausea negated"""
        if r.get('status') == 'error': return False, "Error"
        active = r.get("active_symptoms", [])
        neg = r.get("negated_symptoms", [])
        pass_test = any("fever" in a for a in active) and any("cough" in a for a in active) and any("nausea" in n for n in neg)
        return pass_test, f"Active: {active}, Negated: {neg}"
    results.append(evaluate_test_case(pipeline, "T2.3", "2. Negation Tracking", "Patient has fever and cough; denies nausea.", {}, t2_3_eval, "P1"))

    def t2_4_eval(r):
        """active is empty, headache is negated"""
        neg = r.get("negated_symptoms", [])
        active = r.get("active_symptoms", [])
        pass_test = len(active) == 0 and any("headache" in n for n in neg)
        return pass_test, f"Active: {active}, Negated: {neg}"
    results.append(evaluate_test_case(pipeline, "T2.4", "2. Negation Tracking", "No headache.", {}, t2_4_eval, "P0"))

    def t2_5_eval(r):
        """rash is negated"""
        neg = r.get("negated_symptoms", [])
        pass_test = any("rash" in n for n in neg)
        return pass_test, f"Negated: {neg}"
    results.append(evaluate_test_case(pipeline, "T2.5", "2. Negation Tracking", "free of skin rash", {}, t2_5_eval, "P1"))


    # 3. Biological & Demographic Guardrails
    def t3_1_eval(r):
        """No female obstetric conditions in differential"""
        diff = [d['disease'].lower() for d in r.get("predictions", [])]
        female_conds = {"endometriosis", "ovarian cyst", "polycystic ovarian syndrome (pcos)", "pelvic inflammatory disease", "ectopic pregnancy"}
        pass_test = len(set(diff).intersection(female_conds)) == 0
        return pass_test, f"Differential: {diff}"
    results.append(evaluate_test_case(pipeline, "T3.1", "3. Guardrails", "severe lower pelvic and abdominal pain", {"sex": "Male"}, t3_1_eval, "P0"))

    def t3_2_eval(r):
        """Female obstetric conditions allowed for female"""
        diff = [d['disease'].lower() for d in r.get("predictions", [])]
        return True, f"Differential: {diff}"
    results.append(evaluate_test_case(pipeline, "T3.2", "3. Guardrails", "severe lower pelvic and abdominal pain", {"sex": "Female", "is_pregnant": False}, t3_2_eval, "P1"))

    def t3_3_eval(r):
        """No gestational conditions in differential if not pregnant"""
        diff = [d['disease'].lower() for d in r.get("predictions", [])]
        gestational = {"hyperemesis gravidarum", "gestational diabetes", "preeclampsia"}
        pass_test = len(set(diff).intersection(gestational)) == 0
        return pass_test, f"Differential: {diff}"
    results.append(evaluate_test_case(pipeline, "T3.3", "3. Guardrails", "severe nausea and vomiting in morning", {"sex": "Female", "is_pregnant": False}, t3_3_eval, "P0"))

    def t3_4_eval(r):
        """Gestational conditions allowed if pregnant"""
        diff = [d['disease'].lower() for d in r.get("predictions", [])]
        return True, f"Differential: {diff}"
    results.append(evaluate_test_case(pipeline, "T3.4", "3. Guardrails", "severe nausea and vomiting in morning", {"sex": "Female", "is_pregnant": True}, t3_4_eval, "P1"))

    def t3_5_eval(r):
        """Check differential doesn't return empty for male with pregnancy symptoms (should return non-pregnancy diseases)"""
        diff = [d['disease'].lower() for d in r.get("predictions", [])]
        pass_test = len(diff) > 0
        return pass_test, f"Differential: {diff}"
    results.append(evaluate_test_case(pipeline, "T3.5", "3. Guardrails", "severe nausea and vomiting", {"sex": "Male"}, t3_5_eval, "P1"))


    # 4. Triage Urgency Calibration
    def t4_1_eval(r):
        """EMERGENCY (Level 1) triage level"""
        if r.get('status') == 'error': return False, "Error"
        triage = r.get("triage", {}).get("triage_level", "")
        return "EMERGENCY" in triage, triage
    results.append(evaluate_test_case(pipeline, "T4.1", "4. Triage Calibration", "sharp chest pain and shortness of breath", {}, t4_1_eval, "P0"))

    def t4_2_eval(r):
        """EMERGENCY (Level 1) triage level"""
        if r.get('status') == 'error': return False, "Error"
        triage = r.get("triage", {}).get("triage_level", "")
        return "EMERGENCY" in triage, triage
    results.append(evaluate_test_case(pipeline, "T4.2", "4. Triage Calibration", "patient lost consciousness and is coughing up blood", {}, t4_2_eval, "P0"))

    def t4_3_eval(r):
        """URGENT CARE (Level 2) triage level"""
        if r.get('status') == 'error': return False, "Error"
        triage = r.get("triage", {}).get("triage_level", "")
        return "URGENT CARE" in triage, triage
    results.append(evaluate_test_case(pipeline, "T4.3", "4. Triage Calibration", "fever, vomiting, and abdominal pain", {}, t4_3_eval, "P1"))

    def t4_4_eval(r):
        """ROUTINE CONSULT (Level 3) triage level"""
        if r.get('status') == 'error': return False, "Error"
        triage = r.get("triage", {}).get("triage_level", "")
        return "ROUTINE" in triage, triage
    results.append(evaluate_test_case(pipeline, "T4.4", "4. Triage Calibration", "mild headache and nasal congestion", {}, t4_4_eval, "P1"))

    def t4_5_eval(r):
        """Negated red flags do NOT trigger EMERGENCY. Should be error (no active) or Routine."""
        triage = r.get("triage", {}).get("triage_level", "")
        pass_test = "EMERGENCY" not in triage
        return pass_test, triage
    results.append(evaluate_test_case(pipeline, "T4.5", "4. Triage Calibration", "patient denies sharp chest pain and shortness of breath", {}, t4_5_eval, "P0"))


    # 5. Adversarial & Edge-Case Stress Testing
    def t5_1_eval(r):
        """Handles empty string without crashing, returns error status"""
        return r.get("status") == "error", str(r.get("status"))
    results.append(evaluate_test_case(pipeline, "T5.1", "5. Adversarial/Edge Cases", "", {}, t5_1_eval, "P1"))

    def t5_2_eval(r):
        """Handles whitespace-only string without crashing"""
        return r.get("status") == "error", str(r.get("status"))
    results.append(evaluate_test_case(pipeline, "T5.2", "5. Adversarial/Edge Cases", "     ", {}, t5_2_eval, "P1"))

    def t5_3_eval(r):
        """Handles long input correctly (truncates or processes) without crashing"""
        return r.get("status") != "exception", str(r.get("status"))
    results.append(evaluate_test_case(pipeline, "T5.3", "5. Adversarial/Edge Cases", "pain " * 2000, {}, t5_3_eval, "P2"))

    def t5_4_eval(r):
        """Pure negation strings return no active symptoms"""
        return len(r.get("active_symptoms", [])) == 0, str(r.get("active_symptoms", []))
    results.append(evaluate_test_case(pipeline, "T5.4", "5. Adversarial/Edge Cases", "no, none, denied, neither, not at all", {}, t5_4_eval, "P1"))

    def t5_5_eval(r):
        """Heavy clinical jargon test"""
        if r.get('status') == 'error': return False, "Error"
        active = r.get("active_symptoms", [])
        return len(active) > 0, str(active)
    results.append(evaluate_test_case(pipeline, "T5.5", "5. Adversarial/Edge Cases", "Patient presents with acute myocardial infarction indicators, severe diaphoresis, and angina pectoris.", {}, t5_5_eval, "P2"))

    with open("audit_results.json", "w") as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    run_tests()

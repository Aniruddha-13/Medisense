# ─────────────────────────────────────────────────────────────────────────────
# CLINICAL GUARDRAIL DEFINITIONS
# These are hard-coded, model-agnostic safety overrides. They fire before any
# ML-derived triage logic to catch life-threatening presentations that may fall
# outside the model's training distribution (e.g., Stroke, Anaphylaxis).
# Threshold: ANY 2+ symptoms from a red-flag set triggers an EMERGENCY override.
# ─────────────────────────────────────────────────────────────────────────────

# Stroke / TIA — FAST criteria mapped to NLP feature names
# Fires when ≥2 of these co-occur (e.g., slurred speech + facial drooping)
STROKE_RED_FLAGS = {
    "difficulty speaking",    # "slurred speech", "dysarthria"
    "symptoms of the face",   # "facial drooping", "facial palsy"
    "arm weakness",           # "weakness in right/left arm"
    "focal weakness",         # focal neurological deficit
    "loss of sensation",      # hemisensory loss
    "double vision",          # cranial nerve involvement
    "blindness",              # amaurosis fugax / visual field loss
}

# Anaphylaxis — systemic allergic emergency
# Fires when ≥2 of these co-occur (e.g., skin reaction + breathing difficulty)
ANAPHYLAXIS_RED_FLAGS = {
    "itching of skin",        # urticaria / pruritus
    "skin rash",              # hives / welts
    "allergic reaction",      # direct allergen exposure
    "shortness of breath",    # airway compromise
    "difficulty breathing",   # bronchospasm
    "throat swelling",        # angioedema (airway)
    "lip swelling",           # angioedema (face)
    "wheezing",               # bronchospasm
    "dizziness",              # hypotension / distributive shock
    "fainting",               # anaphylactic shock
}

# ─────────────────────────────────────────────────────────────────────────────

GUARDRAIL_EMERGENCY_COLOR = "#FF0000"   # Pure red — visually distinct from
                                        # standard emergency (#FF4B4B)


class ClinicalTriageEngine:
    def __init__(self):
        # Critical red-flag symptoms requiring emergency intervention
        self.emergency_symptoms = {
            "sharp chest pain", "chest tightness", "shortness of breath",
            "coughing up blood", "breathing fast", "abnormal involuntary movements",
            "loss of consciousness", "fainting", "hemoptysis", "seizures",
            "difficulty breathing", "hurts to breath",
        }

        # Moderate-risk symptoms needing evaluation within 24 hours
        self.urgent_symptoms = {
            "sharp abdominal pain", "irregular heartbeat", "fever",
            "palpitations", "vomiting", "dizziness", "nausea", "cough",
            "arm weakness", "weakness", "focal weakness",
        }

    def assess_urgency(self, active_symptoms, top_disease, top_confidence):
        """
        Determines the clinical triage tier and recommended action plan.

        Evaluation order (highest priority first):
          0. Hard-coded Clinical Guardrails (model-agnostic, patient safety)
          1. Emergency red-flag symptom set intersection
          2. Urgent care symptom set intersection
          3. Default routine consultation
        """
        active_set = set(active_symptoms)

        # ═══════════════════════════════════════════════════════════════════
        #  GUARDRAIL 0a — STROKE / TIA (FAST Criteria)
        #  Fires when ≥2 neurological red flags co-occur.
        #  Completely bypasses the ML model prediction.
        # ═══════════════════════════════════════════════════════════════════
        stroke_hits = active_set.intersection(STROKE_RED_FLAGS)
        if len(stroke_hits) >= 2:
            hit_list = ", ".join(sorted(stroke_hits))
            return {
                "triage_level": "EMERGENCY (Level 1)",
                "color": GUARDRAIL_EMERGENCY_COLOR,
                "justification": (
                    f"CLINICAL GUARDRAIL — Critical neurological symptoms detected "
                    f"({hit_list}). High risk of acute stroke or TIA. "
                    f"Time-sensitive: thrombolysis window is 4.5 hours from onset."
                ),
                "action_recommendation": (
                    "Seek immediate emergency medical attention "
                    "(Call 112 / 108 / 911 immediately). Do NOT drive yourself."
                ),
            }

        # ═══════════════════════════════════════════════════════════════════
        #  GUARDRAIL 0b — ANAPHYLAXIS
        #  Fires when ≥2 systemic allergic red flags co-occur.
        #  Catches allergen-triggered presentations not in model training set.
        # ═══════════════════════════════════════════════════════════════════
        anaphylaxis_hits = active_set.intersection(ANAPHYLAXIS_RED_FLAGS)
        if len(anaphylaxis_hits) >= 2:
            hit_list = ", ".join(sorted(anaphylaxis_hits))
            return {
                "triage_level": "EMERGENCY (Level 1)",
                "color": GUARDRAIL_EMERGENCY_COLOR,
                "justification": (
                    f"CLINICAL GUARDRAIL — Systemic allergic emergency detected "
                    f"({hit_list}). High risk of anaphylaxis. "
                    f"Airway compromise may be imminent."
                ),
                "action_recommendation": (
                    "Seek immediate emergency medical attention "
                    "(Call 112 / 108 / 911 immediately). "
                    "Administer epinephrine (EpiPen) if available."
                ),
            }

        # ═══════════════════════════════════════════════════════════════════
        #  1. Standard Emergency Red-Flag Check
        # ═══════════════════════════════════════════════════════════════════
        emergency_flags = active_set.intersection(self.emergency_symptoms)
        if emergency_flags:
            return {
                "triage_level": "EMERGENCY (Level 1)",
                "color": "#FF4B4B",
                "justification": f"Patient exhibits critical red-flag symptoms: {', '.join(sorted(emergency_flags))}.",
                "action_recommendation": "Seek immediate emergency medical attention (Call 112 / 108).",
            }

        # ═══════════════════════════════════════════════════════════════════
        #  2. Urgent Care Criteria
        # ═══════════════════════════════════════════════════════════════════
        urgent_flags = active_set.intersection(self.urgent_symptoms)
        if urgent_flags:
            return {
                "triage_level": "URGENT CARE (Level 2)",
                "color": "#FFA500",
                "justification": (
                    f"Moderate-risk symptoms detected ({', '.join(sorted(urgent_flags))}) "
                    f"with significant clinical indicator for {top_disease}."
                ),
                "action_recommendation": "Consult a physician or urgent care clinic within 12 to 24 hours.",
            }

        # ═══════════════════════════════════════════════════════════════════
        #  3. Default — Routine Consultation
        # ═══════════════════════════════════════════════════════════════════
        return {
            "triage_level": "ROUTINE CONSULT (Level 3)",
            "color": "#00C04B",
            "justification": "Symptoms appear non-acute based on current screening profiles.",
            "action_recommendation": "Schedule a routine visit with a primary care provider or teleconsult.",
        }


if __name__ == "__main__":
    triage = ClinicalTriageEngine()
    test_symptoms = ["palpitations", "sharp chest pain", "shortness of breath"]
    assessment = triage.assess_urgency(test_symptoms, top_disease="Angina", top_confidence=65.0)

    print("--- TRIAGE TEST ASSESSMENT ---")
    print(f"Level:  {assessment['triage_level']}")
    print(f"Reason: {assessment['justification']}")
    print(f"Action: {assessment['action_recommendation']}")
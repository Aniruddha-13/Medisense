class ClinicalTriageEngine:
    def __init__(self):
        # Critical red-flag symptoms requiring emergency intervention
        self.emergency_symptoms = {
            "sharp chest pain", "chest tightness", "shortness of breath", 
            "coughing up blood", "breathing fast", "abnormal involuntary movements", 
            "loss of consciousness"
        }
        
        # Moderate-risk symptoms needing evaluation within 24 hours
        self.urgent_symptoms = {
            "sharp abdominal pain", "irregular heartbeat", "fever", 
            "palpitations", "vomiting", "dizziness", "nausea"
        }

    def assess_urgency(self, active_symptoms, top_disease, top_confidence):
        """
        Determines the clinical triage tier and recommended action plan.
        """
        active_set = set(active_symptoms)
        
        # 1. Check for Emergency Red Flags
        emergency_flags = active_set.intersection(self.emergency_symptoms)
        if emergency_flags:
            return {
                "triage_level": "EMERGENCY (Level 1)",
                "color": "#FF4B4B",
                "justification": f"Patient exhibits critical red-flag symptoms: {', '.join(emergency_flags)}.",
                "action_recommendation": "Seek immediate emergency medical attention (Call 911 / ER)."
            }

        # 2. Check for Urgent Care criteria
        urgent_flags = active_set.intersection(self.urgent_symptoms)
        if urgent_flags:
            return {
                "triage_level": "URGENT CARE (Level 2)",
                "color": "#FFA500",
                "justification": f"Moderate-risk symptoms detected ({', '.join(urgent_flags)}) with significant clinical indicator for {top_disease}.",
                "action_recommendation": "Consult a physician or urgent care clinic within 12 to 24 hours."
            }

        # 3. Default to Routine Consultation
        return {
            "triage_level": "ROUTINE CONSULT (Level 3)",
            "color": "#00C04B",
            "justification": "Symptoms appear non-acute based on current screening profiles.",
            "action_recommendation": "Schedule a routine visit with a primary care provider or teleconsult."
        }


if __name__ == "__main__":
    triage = ClinicalTriageEngine()
    test_symptoms = ["palpitations", "sharp chest pain", "shortness of breath"]
    assessment = triage.assess_urgency(test_symptoms, top_disease="Angina", top_confidence=65.0)
    
    print("--- TRIAGE TEST ASSESSMENT ---")
    print(f"Level:  {assessment['triage_level']}")
    print(f"Reason: {assessment['justification']}")
    print(f"Action: {assessment['action_recommendation']}")
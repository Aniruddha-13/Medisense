import os
import sys
import pickle
import numpy as np
import pandas as pd

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from nlp_extractor import SecureSemanticExtractor
from triage_engine import ClinicalTriageEngine

# Comprehensive biological exclusions for non-female / non-pregnant patients
FEMALE_OBSTETRIC_CONDITIONS = {
    "problem during pregnancy", "hyperemesis gravidarum", "ectopic pregnancy",
    "gestational diabetes", "vulvodynia", "vaginal cyst", "endometriosis",
    "ovarian cyst", "polycystic ovarian syndrome (pcos)", "cervicitis",
    "pelvic inflammatory disease", "vaginitis", "spontaneous abortion",
    "threatened abortion", "postpartum depression", "preeclampsia"
}

class MediSensePipeline:
    def __init__(self, models_dir=None):
        if models_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            models_dir = os.path.join(base_dir, "models")

        self.nlp = SecureSemanticExtractor(models_dir=models_dir)
        self.triage = ClinicalTriageEngine()

        with open(os.path.join(models_dir, "medical_model.pkl"), "rb") as f:
            self.model = pickle.load(f)
        with open(os.path.join(models_dir, "label_encoder.pkl"), "rb") as f:
            self.label_encoder = pickle.load(f)
        with open(os.path.join(models_dir, "symptom_features.pkl"), "rb") as f:
            self.symptom_list = pickle.load(f)

    def analyze(self, raw_text, patient_profile=None, top_k=3, similarity_threshold=0.70):
        try:
            # 1. Semantic extraction with calibrated similarity threshold
            extraction = self.nlp.extract_symptoms(raw_text, similarity_threshold=similarity_threshold)
            active_symptoms = extraction["present"]
            negated_symptoms = extraction["negated"]

            if not active_symptoms:
                return {
                    "status": "error",
                    "message": "No recognized symptoms matching clinical vocabulary were identified.",
                    "active_symptoms": [],
                    "negated_symptoms": negated_symptoms
                }

            # 2. Vectorize
            vector = pd.DataFrame(0, index=[0], columns=self.symptom_list)
            for sym in active_symptoms:
                if sym in vector.columns:
                    vector.loc[0, sym] = 1

            # 3. Model prediction
            probas = self.model.predict_proba(vector)[0]
            sorted_indices = np.argsort(probas)[::-1]

            # 4. Demographic & Biological Guardrails
            profile = patient_profile or {}
            is_female = str(profile.get("sex", "")).strip().lower() == "female"
            is_pregnant = bool(profile.get("is_pregnant", False))

            differential = []
            for idx in sorted_indices:
                disease_name = self.label_encoder.inverse_transform([idx])[0]
                d_lower = disease_name.lower()

                # Guardrail: Suppress female/obstetric conditions for non-females
                if not is_female and d_lower in FEMALE_OBSTETRIC_CONDITIONS:
                    continue

                # Guardrail: Suppress pregnancy conditions for non-pregnant profiles
                if not is_pregnant and ("pregnancy" in d_lower or d_lower == "hyperemesis gravidarum"):
                    continue

                conf = round(float(probas[idx] * 100), 2)
                differential.append({
                    "disease": disease_name.title(),
                    "confidence": conf
                })
                if len(differential) >= top_k:
                    break

            # 5. Clinical Triage
            top_disease = differential[0]["disease"] if differential else "Undetermined"
            top_conf = differential[0]["confidence"] if differential else 0.0
            triage_report = self.triage.assess_urgency(active_symptoms, top_disease, top_conf)

            warning = None
            if len(active_symptoms) == 1:
                warning = "Only 1 clinical symptom detected. Confidence scores reflect limited diagnostic evidence."

            return {
                "status": "success",
                "active_symptoms": active_symptoms,
                "negated_symptoms": negated_symptoms,
                "predictions": differential,
                "triage": triage_report,
                "warning": warning
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Clinical analysis exception: {str(e)}"
            }

    def analyze_note(self, text, patient_profile=None, top_k=3):
        return self.analyze(text, patient_profile=patient_profile, top_k=top_k)
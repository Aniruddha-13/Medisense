import os
import pickle
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Load saved model and metadata
print("Loading Medical Diagnosis System...")
with open(os.path.join(BASE_DIR, "medical_model.pkl"), "rb") as f:
    model = pickle.load(f)

with open(os.path.join(BASE_DIR, "label_encoder.pkl"), "rb") as f:
    label_encoder = pickle.load(f)

with open(os.path.join(BASE_DIR, "symptom_features.pkl"), "rb") as f:
    symptom_list = pickle.load(f)

print(f"System ready. Total symptoms recognized: {len(symptom_list)}")


def diagnose_patient(reported_symptoms):
    # Normalize inputs to lowercase and strip extra whitespace
    cleaned_symptoms = [s.strip().lower() for s in reported_symptoms if s.strip()]
    
    # Check for recognized symptoms
    valid_symptoms = [s for s in cleaned_symptoms if s in symptom_list]
    invalid_symptoms = [s for s in cleaned_symptoms if s not in symptom_list]

    if invalid_symptoms:
        print(f"\n[Warning] Unrecognized symptoms ignored: {', '.join(invalid_symptoms)}")

    if not valid_symptoms:
        print("\n[Error] No valid symptoms provided from the dataset dictionary.")
        return

    # Create binary input vector (1 row, 230 columns)
    input_data = pd.DataFrame(0, index=[0], columns=symptom_list)
    for sym in valid_symptoms:
        input_data.loc[0, sym] = 1

    # Predict class probabilities
    probabilities = model.predict_proba(input_data)[0]

    # Get top 3 predicted indices
    top_indices = np.argsort(probabilities)[::-1][:3]

    print("\n" + "=" * 45)
    print("           DIAGNOSTIC REPORT")
    print("=" * 45)
    print(f"Symptoms Analyzed: {', '.join(valid_symptoms)}\n")
    print(f"{'Rank':<6} {'Predicted Condition':<30} {'Confidence'}")
    print("-" * 45)

    for rank, idx in enumerate(top_indices, start=1):
        disease_name = label_encoder.inverse_transform([idx])[0]
        confidence = probabilities[idx] * 100
        print(f"{rank:<6} {disease_name.title():<30} {confidence:.1f}%")
    print("=" * 45)


# 2. Interactive user loop
if __name__ == "__main__":
    print("\nEnter symptoms separated by commas (or type 'exit' to quit).")
    print("Example: fever, cough, shortness of breath\n")

    while True:
        user_input = input("Enter symptoms: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            print("Shutting down diagnostic system.")
            break

        symptoms = user_input.split(",")
        diagnose_patient(symptoms)
        print("\n")
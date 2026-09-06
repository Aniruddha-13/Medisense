import os
import pickle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "models", "symptom_features.pkl"), "rb") as f:
    symptoms = pickle.load(f)

keywords = ["nose", "nasal", "ear", "head", "congestion", "sinus", "throat", "cold"]
matched = [s for s in symptoms if any(k in s for k in keywords)]

print("Related symptoms in your dataset:")
for s in sorted(matched):
    print(f" - {s}")
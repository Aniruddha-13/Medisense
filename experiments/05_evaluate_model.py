import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    top_k_accuracy_score,
    classification_report,
    precision_recall_fscore_support
)

# Resolve paths
EXPERIMENTS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(EXPERIMENTS_DIR)
DATA_PATH = os.path.join(BASE_DIR, "data", "Diseases_and_Symptoms_dataset.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")

print("--- 1. LOADING EVALUATION DATA & ARTIFACTS ---")
df = pd.read_csv(DATA_PATH)
X = df.drop(columns=['diseases'])

label_encoder = joblib.load(os.path.join(MODELS_DIR, "label_encoder.pkl"))
model = joblib.load(os.path.join(MODELS_DIR, "medical_model.pkl"))

y_encoded = label_encoder.transform(df['diseases'])

# Use the exact same seed & split as training
_, X_test, _, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

print(f"Total Test Samples (Held-out): {X_test.shape[0]:,}")
print(f"Total Disease Classes:         {len(label_encoder.classes_)}")

print("\n--- 2. COMPUTING INFERENCE & PROBABILITIES ---")
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)

# Metrics calculation
top1_acc = accuracy_score(y_test, y_pred) * 100
top3_acc = top_k_accuracy_score(y_test, y_proba, k=3, labels=np.arange(len(label_encoder.classes_))) * 100
top5_acc = top_k_accuracy_score(y_test, y_proba, k=5, labels=np.arange(len(label_encoder.classes_))) * 100

precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted')

print("\n==================================================")
print("       [*] CLINICAL MODEL BENCHMARK RESULTS        ")
print("==================================================")
print(f" Top-1 Exact Match Accuracy:     {top1_acc:.2f}%")
print(f" Top-3 Differential Accuracy:    {top3_acc:.2f}%  <-- Clinical Target")
print(f" Top-5 Differential Accuracy:    {top5_acc:.2f}%")
print(f" Weighted Precision:             {precision * 100:.2f}%")
print(f" Weighted Recall:                {recall * 100:.2f}%")
print(f" Weighted F1-Score:              {f1 * 100:.2f}%")
print("==================================================")
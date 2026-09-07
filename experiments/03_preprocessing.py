import os
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Navigate from medisense/experiments -> medisense/
EXPERIMENTS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(EXPERIMENTS_DIR)

DATA_PATH = os.path.join(BASE_DIR, "data", "Diseases_and_Symptoms_dataset.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# 1. Load data
print(f"Loading data from: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)

# 2. Separate Features (X) and Target (y)
X = df.drop(columns=['diseases'])
y = df['diseases']

symptom_list = list(X.columns)
print(f"Total Features (Symptoms): {len(symptom_list)}")

# 3. Encode Disease labels using the current venv's scikit-learn
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# 4. Train-Test Split (80% Train, 20% Test)
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

print(f"Training samples: {X_train.shape[0]}")
print(f"Testing samples:  {X_test.shape[0]}")

# 5. Save preprocessing artifacts directly to models/
os.makedirs(MODELS_DIR, exist_ok=True)

encoder_path = os.path.join(MODELS_DIR, "label_encoder.pkl")
with open(encoder_path, "wb") as f:
    pickle.dump(label_encoder, f)

features_path = os.path.join(MODELS_DIR, "symptom_features.pkl")
with open(features_path, "wb") as f:
    pickle.dump(symptom_list, f)

print(f"\nSaved updated artifacts directly to '{MODELS_DIR}':")
print(" - label_encoder.pkl")
print(" - symptom_features.pkl")
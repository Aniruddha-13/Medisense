import os
import time
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

# Navigate from medisense/experiments -> medisense/
EXPERIMENTS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(EXPERIMENTS_DIR)

DATA_PATH = os.path.join(BASE_DIR, "data", "Diseases_and_Symptoms_dataset.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# 1. Load data
print(f"Loading dataset from: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
X = df.drop(columns=['diseases'])

# Load saved label encoder using joblib (handles both pickle and joblib artifacts)
label_encoder = joblib.load(os.path.join(MODELS_DIR, "label_encoder.pkl"))
y_encoded = label_encoder.transform(df['diseases'])

print(f"  Dataset shape: {X.shape}")
print(f"  Number of disease classes: {len(label_encoder.classes_)}")

# 2. Split data (same seed/strategy as preprocessing for consistency)
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
print(f"  Training samples: {X_train.shape[0]:,}")
print(f"  Test samples:     {X_test.shape[0]:,}")

# 3. Train Multinomial Logistic Regression (L2-regularized)
#    - Industry standard for sparse, high-dimensional one-hot feature spaces
#    - Excellent probability calibration without additional CalibratedClassifierCV
#    - Handles class imbalance via class_weight='balanced'
#    - Resulting .pkl is typically < 5 MB vs. 2+ GB for unconstrained Random Forest
print("\nTraining Multinomial Logistic Regression (L2, balanced classes) ...")
print("Algorithm: LogisticRegression(solver='saga', C=1.0, class_weight='balanced')")
start_time = time.time()

model = LogisticRegression(
    solver='saga',           # Best solver for large, sparse, multi-class datasets
    max_iter=2000,
    C=1.0,                   # Inverse regularization strength; higher C = less regularization
    class_weight='balanced', # Corrects for skewed class distributions
    random_state=42,
    n_jobs=-1,               # Parallelize across all CPU cores
    tol=1e-4,
    verbose=1
)
model.fit(X_train, y_train)

elapsed = round(time.time() - start_time, 2)
print(f"\nTraining completed in {elapsed} seconds.")

# 4. Save model with joblib (compress=3 keeps file size minimal)
os.makedirs(MODELS_DIR, exist_ok=True)
model_path = os.path.join(MODELS_DIR, "medical_model.pkl")
joblib.dump(model, model_path, compress=3)

size_mb = os.path.getsize(model_path) / (1024 * 1024)
print(f"\nModel saved to '{model_path}'")
print(f"Model file size: {size_mb:.2f} MB  (GitHub limit: 90 MB)")
print("Algorithm: Multinomial Logistic Regression (L2-regularized, SAGA solver)")
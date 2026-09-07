import os
import pandas as pd

# Automatically resolves the folder where this script lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Diseases_and_Symptoms_dataset.csv")

# 1. Load the dataset
df = pd.read_csv(DATA_PATH)

# 2. Dimensions
print("=== 1. DATASET SHAPE ===")
print(f"Total Rows: {df.shape[0]}, Total Columns: {df.shape[1]}")

# 3. Column names preview
print("\n=== 2. COLUMN NAMES (First 15) ===")
print(df.columns.tolist()[:15])

# 4. First 3 rows
print("\n=== 3. SAMPLE ROWS ===")
print(df.head(3))

# 5. Missing values
print(f"\n=== 4. MISSING VALUES TOTAL ===: {df.isnull().sum().sum()}")
import os
import pandas as pd

# Load dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Diseases_and_Symptoms_dataset.csv")
df = pd.read_csv(DATA_PATH)

# 1. Inspect the target column: 'diseases'
num_diseases = df['diseases'].nunique()
print(f"Total Unique Diseases: {num_diseases}")

# 2. Check class balance (top 10 most frequent diseases)
print("\nTop 10 Most Frequent Diseases:")
print(df['diseases'].value_counts().head(10))

# 3. Check the least frequent diseases
print("\nBottom 5 Least Frequent Diseases:")
print(df['diseases'].value_counts().tail(5))

# 4. Find the most common symptoms across all records
# (Since symptoms are 0 or 1, the sum equals the total count of times that symptom appeared)
symptom_columns = [col for col in df.columns if col != 'diseases']
symptom_counts = df[symptom_columns].sum().sort_values(ascending=False)

print("\nTop 10 Most Common Symptoms:")
print(symptom_counts.head(10))
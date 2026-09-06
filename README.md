# 🩺 MediSense-NLP: Clinical Triage & Differential Diagnosis Engine

MediSense-NLP is a production-style health-tech AI pipeline designed to process unstructured patient narratives, extract clinical entities via dense vector semantic search, apply demographic safety guardrails, and predict ranked differential diagnoses with urgency triage.

## 🚀 Architecture overview

1. **Semantic Clinical NLP Pipeline (`SentenceTransformers`)**
   - Uses `all-MiniLM-L6-v2` to map colloquial patient language (e.g., *"stuffy nose"*, *"pounding head"*) to a standardized 230-symptom vocabulary via Cosine Similarity.
   - Bypasses brittle hardcoded keyword dictionaries.
2. **Clinical Negation Engine**
   - Detects negative scopes (e.g., *"patient denies chest pain"*) and safely excludes them from the active symptom vector.
3. **Demographic Guardrails**
   - Filters impossible predictions based on biological sex and pregnancy status (e.g., suppresses obstetric conditions for male profiles).
4. **Ensemble Diagnostics & Triage Engine**
   - Random Forest model trained on 96k records to predict 100 disease classes.
   - Rules-based urgency scoring flags Emergency (Level 1) vs. Routine (Level 3) cases.

## 📊 Performance Benchmarks

Tested against a rigorous 20-case clinical suite across Cardiology, Pulmonology, Neurology, and Gastroenterology:
* **Top-3 Differential Accuracy:** 97.8%
* **End-to-End Pipeline Pass Rate:** 75.0% (Stress tested against colloquialisms and negations)

## 💻 Tech Stack
* **Core ML:** Python, `scikit-learn`, `pandas`, `numpy`
* **NLP:** `sentence-transformers`, `regex`
* **Web UI:** `streamlit`

## 🛠️ How to Run

1. Clone the repository and navigate to the project directory.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or .\venv\Scripts\Activate.ps1 on Windows
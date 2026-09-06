import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
FEATURES_PATH = os.path.join(MODELS_DIR, "symptom_features.pkl")
OUTPUT_PATH = os.path.join(MODELS_DIR, "symptom_embeddings.npy")

def generate_embeddings():
    print(f"Loading symptoms from: {FEATURES_PATH}")
    with open(FEATURES_PATH, "rb") as f:
        symptoms = pickle.load(f)

    print(f"Generating 384-dimensional embeddings for {len(symptoms)} symptoms...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Generate normalized embeddings for fast cosine dot-product
    embeddings = model.encode(symptoms, convert_to_numpy=True, normalize_embeddings=True)

    np.save(OUTPUT_PATH, embeddings)
    print(f"SUCCESS: Saved static embeddings matrix to: {OUTPUT_PATH}")
    print(f"File size: {os.path.getsize(OUTPUT_PATH) / 1024:.2f} KB (Loads in milliseconds!)")

if __name__ == "__main__":
    generate_embeddings()
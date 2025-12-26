# scripts/build_index.py
import os, pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer

INFILE = Path("data/passages.txt")
VEC_PATH = Path("models/tfidf_vectorizer.pkl")
DOCS_PATH = Path("models/passages.pkl")
MODEL_DIR = Path("models"); MODEL_DIR.mkdir(exist_ok=True)

texts = INFILE.read_text(encoding="utf8").split("\n\n")
vectorizer = TfidfVectorizer(ngram_range=(1,2), max_features=50000)
X = vectorizer.fit_transform(texts)

pickle.dump(vectorizer, open(VEC_PATH, "wb"))
pickle.dump(texts, open(DOCS_PATH, "wb"))
print("Built TF-IDF index:", len(texts), "documents")

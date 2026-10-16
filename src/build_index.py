# src/build_index.py
from src.retrieval import build_index
p = open("data/trusted_docs.txt", "r", encoding="utf-8").read().strip().split("\n\n")
print("Passages:", len(p))
build_index(p)
print("Index built: models/faiss.index and models/faiss_meta.pkl")

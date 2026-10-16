# src/retrieval.py
"""
Retrieval module with TF-IDF fallback and optional FAISS vector search.

Public API:
- query_index(q: str, k: int = 5) -> List[str]
- rebuild_tfidf_index(passages_file: str = "data/passages.txt") -> None
- build_faiss_index(passages_file: str = "data/passages.txt", embed_model: str = "all-MiniLM-L6-v2") -> None

Behavior:
- Prefers FAISS if a usable FAISS index and embeddings exist AND faiss can be imported.
- Otherwise uses a TF-IDF index built from data/passages.txt (one passage per paragraph separated by blank lines).
"""

from typing import List, Optional
import os
import pickle
import warnings

MODELS_DIR = "models"
TFIDF_VEC_PATH = os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl")
PASSAGES_PATH = os.path.join(MODELS_DIR, "passages.pkl")
FAISS_INDEX_PATH = os.path.join(MODELS_DIR, "faiss.index")
EMBS_PATH = os.path.join(MODELS_DIR, "embeddings.pkl")  # stores dict {'model': name, 'array': np.array}

# internal lazy state
_vectorizer = None
_passages: Optional[List[str]] = None
_faiss_index = None
_embeddings = None
_faiss_available = None  # None = unknown, True/False after probe


# ----------------------
# Helpers: TF-IDF path
# ----------------------
def _ensure_models_dir():
    os.makedirs(MODELS_DIR, exist_ok=True)


def rebuild_tfidf_index(passages_file: str = os.path.join("data", "passages.txt")) -> None:
    """
    Build TF-IDF vectorizer from passages_file and save artifacts to models/.
    Passages file format: passages separated by a blank line (i.e. paragraphs).

    Raises:
        FileNotFoundError: If passages_file does not exist
        ValueError: If no valid passages are found in the file
    """
    global _vectorizer, _passages

    if not os.path.exists(passages_file):
        raise FileNotFoundError(
            f"Passages file not found: {passages_file}\n"
            f"Please ensure the file exists and contains passage data separated by blank lines."
        )

    from sklearn.feature_extraction.text import TfidfVectorizer

    try:
        content = open(passages_file, encoding="utf8").read().strip()
        if not content:
            raise ValueError(f"Passages file is empty: {passages_file}")

        texts = content.split("\n\n")
        # Filter out empty passages
        texts = [t.strip() for t in texts if t.strip()]

        if not texts:
            raise ValueError(f"No valid passages found in {passages_file}")

        _vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=50000)
        _vectorizer.fit(texts)
        _passages = texts

        _ensure_models_dir()
        with open(TFIDF_VEC_PATH, "wb") as f:
            pickle.dump(_vectorizer, f)
        with open(PASSAGES_PATH, "wb") as f:
            pickle.dump(_passages, f)

        print(f"[retrieval] TF-IDF index rebuilt successfully ({len(_passages)} passages).")
    except Exception as e:
        raise RuntimeError(f"Failed to rebuild TF-IDF index: {str(e)}") from e


def _load_tfidf_if_needed():
    global _vectorizer, _passages
    if _vectorizer is not None and _passages is not None:
        return
    # Try to load saved artifacts
    try:
        if os.path.exists(TFIDF_VEC_PATH) and os.path.exists(PASSAGES_PATH):
            with open(TFIDF_VEC_PATH, "rb") as f:
                _vectorizer = pickle.load(f)
            with open(PASSAGES_PATH, "rb") as f:
                _passages = pickle.load(f)
            return
    except Exception as e:
        warnings.warn(f"[retrieval] Could not load TF-IDF artifacts: {e}")
    # Try auto-build from data/passages.txt if present
    passages_txt = os.path.join("data", "passages.txt")
    if os.path.exists(passages_txt):
        try:
            rebuild_tfidf_index(passages_txt)
        except Exception as e:
            warnings.warn(f"[retrieval] Failed auto-building TF-IDF: {e}")
    else:
        warnings.warn("[retrieval] No TF-IDF artifacts and no data/passages.txt found.")


def _query_tfidf(q: str, k: int = 5) -> List[str]:
    _load_tfidf_if_needed()
    if _vectorizer is None or _passages is None:
        return []
    try:
        from sklearn.metrics.pairwise import linear_kernel
        qv = _vectorizer.transform([q])
        pv = _vectorizer.transform(_passages)  # fine for moderate corpus sizes; cached vector could be added later
        sims = linear_kernel(qv, pv).flatten()
        import numpy as np
        idx = sims.argsort()[::-1][:k]
        return [ _passages[i] for i in idx ]
    except Exception as e:
        warnings.warn(f"[retrieval] TF-IDF query failed: {e}")
        return []


# ----------------------
# Helpers: FAISS path
# ----------------------
def _probe_faiss_available() -> bool:
    global _faiss_available
    if _faiss_available is not None:
        return _faiss_available
    try:
        import faiss  # type: ignore
        _faiss_available = True
    except Exception:
        _faiss_available = False
    return _faiss_available


def build_faiss_index(passages_file: str = os.path.join("data", "passages.txt"),
                      embed_model: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
    """
    Build embeddings using sentence-transformers and create a FAISS index.
    Saves artifacts to models/: models/faiss.index, models/embeddings.pkl, models/passages.pkl
    Requires: sentence-transformers, faiss (faiss-cpu or faiss-gpu)
    """
    if not _probe_faiss_available():
        raise RuntimeError("faiss not available; install faiss-cpu and sentence-transformers to use build_faiss_index()")

    if not os.path.exists(passages_file):
        raise FileNotFoundError(passages_file)

    # local imports
    from sentence_transformers import SentenceTransformer
    import numpy as np
    import faiss  # local import to ensure name exists in this scope

    texts = open(passages_file, encoding="utf8").read().strip().split("\n\n")
    if not texts:
        raise ValueError("No passages found in " + passages_file)

    print(f"[retrieval] Building embeddings with model {embed_model} for {len(texts)} passages...")
    embedder = SentenceTransformer(embed_model)
    emb_arr = embedder.encode(texts, convert_to_numpy=True, show_progress_bar=True)

    d = emb_arr.shape[1]
    # normalize vectors for cosine-like similarity
    import numpy as _np
    faiss.normalize_L2(emb_arr)
    index = faiss.IndexFlatIP(d)  # inner-product; works with normalized vectors

    index.add(emb_arr.astype("float32"))

    _ensure_models_dir()
    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(EMBS_PATH, "wb") as f:
        pickle.dump({"model": embed_model, "array": emb_arr}, f)
    with open(PASSAGES_PATH, "wb") as f:
        pickle.dump(texts, f)

    print(f"[retrieval] Built FAISS index and saved artifacts ({len(texts)} passages).")


def _try_load_faiss():
    """
    Attempt to load prebuilt FAISS artifacts into module memory.
    Returns True if loaded, False otherwise.
    """
    global _faiss_index, _embeddings, _passages
    if not _probe_faiss_available():
        return False
    try:
        import faiss  # local import
        import numpy as np
        if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(EMBS_PATH) and os.path.exists(PASSAGES_PATH):
            _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
            with open(EMBS_PATH, "rb") as f:
                _embeddings = pickle.load(f)
            with open(PASSAGES_PATH, "rb") as f:
                _passages = pickle.load(f)
            print("[retrieval] Loaded FAISS index and passages.")
            return True
    except Exception as e:
        warnings.warn(f"[retrieval] Failed loading FAISS artifacts: {e}")
    return False


def _query_faiss(q: str, k: int = 5) -> List[str]:
    """
    Query FAISS index: will try to load index and embed query using same model as stored
    (EMBS_PATH stores 'model' name if built with build_faiss_index).
    """
    if not _probe_faiss_available():
        return []
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
        import faiss  # local import

        # load if not loaded
        if _faiss_index is None or _embeddings is None or _passages is None:
            ok = _try_load_faiss()
            if not ok:
                return []
        # handle _embeddings structure saved by build_faiss_index
        model_name = _embeddings.get("model") if isinstance(_embeddings, dict) else None
        if model_name:
            embedder = SentenceTransformer(model_name)
        else:
            embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        q_emb = embedder.encode([q], convert_to_numpy=True)
        # normalize to match IndexFlatIP build
        faiss.normalize_L2(q_emb)
        D, I = _faiss_index.search(q_emb.astype("float32"), k)
        idxs = I[0].tolist()
        results = []
        for i in idxs:
            if i < 0 or i >= len(_passages):
                continue
            results.append(_passages[i])
        return results
    except Exception as e:
        warnings.warn(f"[retrieval] FAISS query failed: {e}")
        return []


# ----------------------
# Public API: query_index
# ----------------------
def query_index(q: str, k: int = 5, mode: str = "tfidf") -> List[str]:
    """
    Query the retrieval index and return top-k passages (strings).

    Args:
        q: Query string
        k: Number of passages to return
        mode: Retrieval mode - "tfidf", "faiss", or "hybrid"

    Returns:
        List of passage strings
    """
    if mode == "faiss":
        # FAISS only
        if _probe_faiss_available():
            try:
                faiss_res = _query_faiss(q, k=k)
                if faiss_res:
                    return faiss_res
            except Exception as e:
                warnings.warn(f"[retrieval] FAISS query failed, falling back to TF-IDF: {e}")
        # Fallback to TF-IDF if FAISS not available
        return _query_tfidf(q, k=k)

    elif mode == "hybrid":
        # Hybrid: combine FAISS and TF-IDF results
        results = []
        k_per_method = k // 2 + 1

        # Try FAISS first
        if _probe_faiss_available():
            try:
                faiss_res = _query_faiss(q, k=k_per_method)
                results.extend(faiss_res)
            except Exception:
                pass

        # Add TF-IDF results
        tfidf_res = _query_tfidf(q, k=k_per_method)
        results.extend(tfidf_res)

        # Deduplicate and limit to k
        seen = set()
        unique_results = []
        for passage in results:
            if passage not in seen:
                seen.add(passage)
                unique_results.append(passage)
            if len(unique_results) >= k:
                break

        return unique_results[:k]

    else:
        # Default: TF-IDF only
        return _query_tfidf(q, k=k)


# ----------------------
# CLI quick-test when run directly
# ----------------------
if __name__ == "__main__":
    print("Quick test for retrieval module.")
    # ensure TF-IDF exists or create minimal sample
    passages_txt = os.path.join("data", "passages.txt")
    if not os.path.exists(passages_txt):
        print("No data/passages.txt found. Creating a tiny sample...")
        os.makedirs("data", exist_ok=True)
        open(passages_txt, "w", encoding="utf8").write(
            "AAPL: Apple reported $81.4B revenue in Q1. Source: company filing.\n\n"
            "MSFT: Microsoft reported strong cloud growth; revenue up 18% YoY.\n\n"
            "GOOGL: Alphabet announced new AI initiatives in Q4."
        )
    # build tfidf if needed
    _load_tfidf_if_needed()
    print("Passages loaded:", 0 if _passages is None else len(_passages))
    print("Query sample:")
    for p in query_index("What was Apple revenue last quarter?", k=3):
        print(" -", p[:200])

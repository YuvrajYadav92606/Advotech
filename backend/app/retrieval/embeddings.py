import numpy as np
from typing import List, Union

_embedding_model = None

def get_embedding_model():
    """
    Singleton lazy loader for Sentence Transformer model.
    Uses 'all-MiniLM-L6-v2' (lightweight, 384-dimensional dense semantic vectors, fast on CPU).
    """
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Fast, high-performance dense embedding model
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            print(f"[Warning] SentenceTransformer load failed, fallback will be used: {e}")
            _embedding_model = "FALLBACK"
    return _embedding_model

def compute_dense_embeddings(texts: List[str]) -> np.ndarray:
    """
    Computes normalized dense vector embeddings for a list of texts.
    Returns ndarray of shape (N, 384).
    """
    model = get_embedding_model()
    if model != "FALLBACK":
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings
    else:
        # Fallback pseudo-dense vectors via TF-IDF if model fails
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(max_features=384)
        X = vec.fit_transform(texts).toarray()
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return X / norms

def compute_cosine_similarity(query_vector: np.ndarray, doc_vectors: np.ndarray) -> np.ndarray:
    """
    Calculates cosine similarity between a query embedding (1, D) and document embeddings (N, D).
    Formula: (u . v) / (||u|| * ||v||)
    Since vectors are normalized, dot product equals cosine similarity.
    """
    if query_vector.ndim == 1:
        query_vector = query_vector.reshape(1, -1)
    # Dot product with normalized vectors
    sims = np.dot(doc_vectors, query_vector.T).flatten()
    # Clip between 0.0 and 1.0 for clean scoring
    return np.clip(sims, 0.0, 1.0)

import argparse
import json
from pathlib import Path

import numpy as np


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a prebuilt legal embedding index against labeled queries.")
    parser.add_argument("--queries", required=True, help="JSONL records with query and relevant_doc_ids")
    parser.add_argument("--index-dir", default="artifacts/legal_index")
    parser.add_argument("--model", default=None, help="Defaults to model stored in index manifest")
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()

    index_dir = Path(args.index_dir)
    manifest = json.loads((index_dir / "manifest.json").read_text(encoding="utf-8"))
    model_name = args.model or manifest["embedding_model"]
    rows = read_jsonl(index_dir / "metadata.jsonl")
    vectors = np.load(index_dir / "embeddings.npy", mmap_mode="r")
    queries = read_jsonl(Path(args.queries))

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit("Install sentence-transformers first: pip install sentence-transformers") from exc

    model = SentenceTransformer(model_name)
    doc_ids = [str(row.get("document_id", row.get("chunk_id", ""))) for row in rows]
    doc_vectors = np.asarray(vectors, dtype=np.float32)
    recall_values = []
    reciprocal_ranks = []
    ndcg_values = []

    for item in queries:
        query = str(item.get("query", "")).strip()
        relevant = {str(value) for value in item.get("relevant_doc_ids", [])}
        if not query or not relevant:
            continue

        q_vector = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
        chunk_scores = doc_vectors @ q_vector
        best_score_by_document = {}
        for doc_id, score in zip(doc_ids, chunk_scores):
            if doc_id and (doc_id not in best_score_by_document or score > best_score_by_document[doc_id]):
                best_score_by_document[doc_id] = float(score)

        ranked_ids = [
            doc_id for doc_id, _ in sorted(
                best_score_by_document.items(), key=lambda pair: pair[1], reverse=True
            )[:args.k]
        ]
        hits = [1 if doc_id in relevant else 0 for doc_id in ranked_ids]
        recall_values.append(len(set(ranked_ids) & relevant) / len(relevant))
        reciprocal_ranks.append(next((1 / rank for rank, hit in enumerate(hits, 1) if hit), 0.0))
        dcg = sum(hit / np.log2(rank + 1) for rank, hit in enumerate(hits, 1))
        ideal_hits = min(len(relevant), args.k)
        idcg = sum(1 / np.log2(rank + 1) for rank in range(1, ideal_hits + 1))
        ndcg_values.append(dcg / idcg if idcg else 0.0)

    if not recall_values:
        raise SystemExit("No valid queries. Each JSONL row needs 'query' and non-empty 'relevant_doc_ids'.")

    print(json.dumps({
        "model": model_name,
        "queries_evaluated": len(recall_values),
        f"recall@{args.k}": round(float(np.mean(recall_values)), 4),
        "mrr": round(float(np.mean(reciprocal_ranks)), 4),
        f"ndcg@{args.k}": round(float(np.mean(ndcg_values)), 4),
    }, indent=2))


if __name__ == "__main__":
    main()

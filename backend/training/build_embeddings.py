import argparse
import json
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description="Build normalized embeddings for legal chunks in batches.")
    parser.add_argument("--input", default="datasets/processed/legal_chunks.jsonl")
    parser.add_argument("--output-dir", default="artifacts/legal_index")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--max-chunks", type=int, default=0, help="Optional pilot limit; 0 processes all chunks")
    args = parser.parse_args()

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit("Install sentence-transformers first: pip install sentence-transformers") from exc

    source = Path(args.input)
    if not source.exists():
        raise SystemExit(f"Input file not found: {source}")

    rows = []
    with source.open("r", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            rows.append(json.loads(line))
            if args.max_chunks and len(rows) >= args.max_chunks:
                break
    if not rows:
        raise SystemExit("No chunks found in the input file.")

    texts = [f"{row.get('title', '')}\n{row.get('text', '')}" for row in rows]
    model = SentenceTransformer(args.model)
    vectors = model.encode(
        texts,
        batch_size=args.batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    np.save(output_dir / "embeddings.npy", vectors)
    with (output_dir / "metadata.jsonl").open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "embedding_model": args.model,
        "embedding_dimensions": int(vectors.shape[1]),
        "chunk_count": len(rows),
        "normalized": True,
        "input": str(source),
        "embeddings_file": "embeddings.npy",
        "metadata_file": "metadata.jsonl",
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

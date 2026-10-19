import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

TEXT_FIELDS = ("text", "content", "judgment_text", "full_text", "body", "document")
ID_FIELDS = ("id", "document_id", "doc_id", "case_id", "uuid")
TITLE_FIELDS = ("title", "case_title", "case_name", "name", "heading")


def first_value(record: dict[str, Any], keys: tuple[str, ...], default: Any = None) -> Any:
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return value
    return default


def read_records(path: Path) -> Iterable[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix in {".jsonl", ".ndjson"}:
        with path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                    if isinstance(value, dict):
                        yield value
                    else:
                        print(f"Skipping non-object JSON at {path}:{line_number}")
                except json.JSONDecodeError as exc:
                    print(f"Skipping invalid JSON at {path}:{line_number}: {exc}")
    elif suffix == ".json":
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item
        elif isinstance(value, dict):
            records = value.get("data") or value.get("documents") or value.get("records")
            if isinstance(records, list):
                for item in records:
                    if isinstance(item, dict):
                        yield item
            else:
                yield value
    elif suffix in {".parquet", ".pq"}:
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("Parquet input requires pandas and pyarrow. Install with: pip install pandas pyarrow") from exc
        for frame in pd.read_parquet(path, chunksize=10_000) if False else [pd.read_parquet(path)]:
            for row in frame.to_dict(orient="records"):
                yield row
    else:
        print(f"Skipping unsupported file: {path}")


def clean_text(value: Any) -> str:
    text = str(value or "").replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize(record: dict[str, Any], source_file: str, row_number: int) -> dict[str, Any] | None:
    raw_text = first_value(record, TEXT_FIELDS)
    text = clean_text(raw_text)
    if len(text) < 80:
        return None

    document_id = str(first_value(record, ID_FIELDS, f"{Path(source_file).stem}_{row_number}")).strip()
    title = str(first_value(record, TITLE_FIELDS, document_id)).strip()
    source_url = first_value(record, ("source_url", "url", "link", "uri"))
    court = first_value(record, ("court", "court_name", "court_or_authority", "authority"))
    date = first_value(record, ("decision_date", "date", "decision_or_enactment_date", "judgment_date"))
    doc_type = str(first_value(record, ("doc_type", "document_type", "type"), "CASE_LAW")).upper()

    return {
        "document_id": document_id,
        "document_type": "STATUTE" if "STATUTE" in doc_type or "LEGISLATION" in doc_type or "ACT" == doc_type else "CASE_LAW",
        "title": title,
        "court_or_authority": str(court).strip() if court else None,
        "decision_date": str(date).strip() if date else None,
        "citation": first_value(record, ("citation", "neutral_citation", "case_citation")),
        "jurisdiction": str(first_value(record, ("jurisdiction",), "India")),
        "source_url": str(source_url).strip() if source_url else None,
        "source_dataset": str(first_value(record, ("dataset_source", "source", "dataset"), Path(source_file).stem)),
        "text": text,
    }


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            boundary = max(text.rfind("\n", start, end), text.rfind(". ", start, end), text.rfind("; ", start, end))
            if boundary > start + int(chunk_size * 0.6):
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break
        start = max(end - overlap, start + 1)
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize legal JSON/JSONL/Parquet records and create searchable chunks.")
    parser.add_argument("--input", required=True, help="Input file or directory containing JSON, JSONL, or Parquet files")
    parser.add_argument("--output", default="datasets/processed/legal_chunks.jsonl")
    parser.add_argument("--chunk-chars", type=int, default=3000, help="Approximate chunk size in characters")
    parser.add_argument("--overlap-chars", type=int, default=400)
    parser.add_argument("--min-text-chars", type=int, default=80)
    args = parser.parse_args()

    if args.chunk_chars < 300 or args.overlap_chars < 0 or args.overlap_chars >= args.chunk_chars:
        parser.error("Use chunk-chars >= 300 and 0 <= overlap-chars < chunk-chars")

    input_path = Path(args.input)
    files = sorted(p for p in input_path.rglob("*") if p.is_file()) if input_path.is_dir() else [input_path]
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    seen_ids: set[str] = set()
    documents = chunks_written = duplicates = rejected = 0

    with output_path.open("w", encoding="utf-8") as out:
        for file_path in files:
            for row_number, raw in enumerate(read_records(file_path), 1):
                record = normalize(raw, str(file_path), row_number)
                if not record or len(record["text"]) < args.min_text_chars:
                    rejected += 1
                    continue
                if record["document_id"] in seen_ids:
                    duplicates += 1
                    continue
                seen_ids.add(record["document_id"])
                documents += 1
                chunks = chunk_text(record["text"], args.chunk_chars, args.overlap_chars)
                for index, chunk in enumerate(chunks):
                    item = {key: value for key, value in record.items() if key != "text"}
                    item.update({
                        "chunk_id": f"{record['document_id']}::chunk_{index:05d}",
                        "chunk_index": index,
                        "chunk_count": len(chunks),
                        "text": chunk,
                    })
                    out.write(json.dumps(item, ensure_ascii=False) + "\n")
                    chunks_written += 1

    print(json.dumps({
        "output": str(output_path),
        "unique_documents": documents,
        "chunks_written": chunks_written,
        "duplicate_document_ids_skipped": duplicates,
        "records_rejected": rejected,
    }, indent=2))


if __name__ == "__main__":
    main()

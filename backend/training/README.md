# AdvoTech legal corpus pipeline

This folder contains offline tools for turning external legal datasets into normalized chunks, embedding them in batches, and evaluating retrieval. It does not replace the current application indexer yet; first validate the new index against a held-out evaluation set.

## 1. Keep data outside Git

Download datasets to a local folder such as `datasets/raw/`. Review each source's license, attribution requirements, data quality, and terms for underlying judgments before processing. Do not commit raw corpora, embeddings, model weights, or index files.

## 2. Install optional pipeline dependencies

From the repository root, with the project's virtual environment active:

```powershell
python -m pip install pandas pyarrow sentence-transformers numpy
```

## 3. Normalize and chunk a pilot dataset

The input can be a JSON, JSONL, or Parquet file, or a directory containing supported files. The normalizer recognizes common text fields such as `text`, `content`, `judgment_text`, and `full_text`, and common ID/title fields. Inspect source schemas first; adapt the field mapping for a dataset rather than assuming every dataset has the same format.

```powershell
python backend/training/ingest_dataset.py --input datasets/raw/pilot.jsonl --output datasets/processed/legal_chunks.jsonl --chunk-chars 3000 --overlap-chars 400
```

Start with a small pilot. The pipeline skips duplicate document IDs, reports malformed JSON lines, and preserves available provenance metadata. Review the output and rejected records before scaling up. It currently deduplicates by document ID; content-level deduplication and amendment-aware versioning should be added for the chosen corpus.

For very large Parquet corpora, convert or iterate through source files in manageable partitions before ingestion. Do not try to load a multi-gigabyte single Parquet file into RAM on a laptop.

## 4. Build embeddings

```powershell
python backend/training/build_embeddings.py --input datasets/processed/legal_chunks.jsonl --output-dir artifacts/legal_index --model sentence-transformers/all-MiniLM-L6-v2 --batch-size 32 --max-chunks 5000
```

Omit `--max-chunks` to process the full input after the pilot has passed. Batch size can be lowered if memory is limited. Embeddings and metadata must remain aligned row-by-row. Never mix vectors from different embedding models in one index.

## 5. Evaluate retrieval

Create a labeled JSONL file with one question per line and relevant document IDs. IDs must match the `document_id` values emitted by the ingestion pipeline.

```json
{"query":"What are the legal requirements for a cheque dishonour notice?","relevant_doc_ids":["ACT_NI_1881_SEC_138"]}
```

Run:

```powershell
python backend/training/evaluate_retrieval.py --queries datasets/processed/eval_queries.jsonl --index-dir artifacts/legal_index --k 10
```

Report Recall@10, MRR, and nDCG@10. Build the evaluation set from verified source links, keep it separate from training data, and split by source judgment to reduce leakage. Do not treat model-generated relevance labels as ground truth without review.

## Important limitations

- This is an offline preprocessing and dense-retrieval baseline, not model fine-tuning.
- The Parquet reader currently favors simplicity and may load a source file into memory. Partition large datasets before ingestion.
- Embeddings are stored as a NumPy matrix for a small pilot. For hundreds of thousands or millions of chunks, use a persistent vector index/database and incremental ingestion instead of brute-force matrix scoring.
- Legal currency, amendment status, source attribution, court/date metadata, and citation correctness require explicit validation.
- Do not present retrieved text as legal advice; show source links, applicable dates, uncertainty, and appropriate professional-review messaging.

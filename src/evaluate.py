from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from statistics import mean

import numpy as np

from retrievers import (
    BM25Retriever,
    DenseRetriever,
    HybridRerankRetriever,
    HybridRRFRetriever,
    SearchResult,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCUMENTS = ROOT / "data" / "processed" / "documents.jsonl"
DEFAULT_QUERIES = ROOT / "data" / "processed" / "queries.jsonl"
DEFAULT_RESULTS_DIR = ROOT / "results"


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def recall_at_k(results: list[SearchResult], relevant_doc_ids: set[str]) -> float:
    if not relevant_doc_ids:
        return 0.0
    retrieved = {result.doc_id for result in results}
    return len(retrieved & relevant_doc_ids) / len(relevant_doc_ids)


def reciprocal_rank(results: list[SearchResult], relevant_doc_ids: set[str]) -> float:
    for rank, result in enumerate(results, start=1):
        if result.doc_id in relevant_doc_ids:
            return 1.0 / rank
    return 0.0


def first_relevant_rank(results: list[SearchResult], relevant_doc_ids: set[str]) -> int | None:
    for rank, result in enumerate(results, start=1):
        if result.doc_id in relevant_doc_ids:
            return rank
    return None


def is_hard_query(query: dict) -> bool:
    if "hard" in query:
        return bool(query["hard"])
    return str(query.get("difficulty", "")).lower() == "hard"


def build_retrievers(
    documents: list[dict],
    dense_model: str,
    reranker_model: str,
    rerank_candidate_k: int,
) -> dict[str, BM25Retriever | DenseRetriever | HybridRRFRetriever | HybridRerankRetriever]:
    bm25 = BM25Retriever(documents)
    dense = DenseRetriever(documents, model_name=dense_model)
    hybrid = HybridRRFRetriever(bm25=bm25, dense=dense)
    hybrid_rerank = HybridRerankRetriever(
        documents=documents,
        candidate_retriever=hybrid,
        model_name=reranker_model,
        candidate_k=rerank_candidate_k,
    )
    return {
        "bm25": bm25,
        "dense": dense,
        "hybrid_rrf": hybrid,
        "hybrid_rerank": hybrid_rerank,
    }


def validate_inputs(documents: list[dict], queries: list[dict]) -> None:
    if not documents:
        raise ValueError("No documents found. Run src/build_corpus.py after adding markdown files.")
    if not queries:
        raise ValueError("No queries found. Add 20 labelled queries to data/processed/queries.jsonl.")

    doc_ids = {document["doc_id"] for document in documents}
    missing: list[tuple[str, str]] = []
    for query in queries:
        for doc_id in query.get("relevant_doc_ids", []):
            if doc_id not in doc_ids:
                missing.append((query.get("query_id", "<missing query_id>"), doc_id))

    if missing:
        examples = ", ".join(f"{query_id}:{doc_id}" for query_id, doc_id in missing[:10])
        raise ValueError(f"Query labels reference missing documents: {examples}")


def evaluate_retriever(
    config_name: str,
    retriever: BM25Retriever | DenseRetriever | HybridRRFRetriever | HybridRerankRetriever,
    queries: list[dict],
    top_k: int,
) -> tuple[dict[str, float | int | str], list[dict[str, str | int | float | bool | None]]]:
    per_query_rows: list[dict[str, str | int | float | bool | None]] = []
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    latencies_ms: list[float] = []

    for query in queries:
        relevant_doc_ids = set(query.get("relevant_doc_ids", []))

        start = time.perf_counter()
        results = retriever.search(query["query"], top_k=top_k)
        latency_ms = (time.perf_counter() - start) * 1000

        query_recall = recall_at_k(results, relevant_doc_ids)
        query_rr = reciprocal_rank(results, relevant_doc_ids)
        rank = first_relevant_rank(results, relevant_doc_ids)

        recalls.append(query_recall)
        reciprocal_ranks.append(query_rr)
        latencies_ms.append(latency_ms)

        per_query_rows.append(
            {
                "config": config_name,
                "query_id": query["query_id"],
                "query": query["query"],
                "hard": is_hard_query(query),
                "category": query.get("category", ""),
                "recall_at_5": query_recall,
                "reciprocal_rank": query_rr,
                "first_relevant_rank": rank,
                "latency_ms": latency_ms,
                "top5_doc_ids": "|".join(result.doc_id for result in results),
            }
        )

    metrics = {
        "config": config_name,
        "num_queries": len(queries),
        "recall_at_5": mean(recalls),
        "mrr": mean(reciprocal_ranks),
        "p95_latency_ms": float(np.percentile(latencies_ms, 95)),
    }
    return metrics, per_query_rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_evaluation(
    documents_path: Path = DEFAULT_DOCUMENTS,
    queries_path: Path = DEFAULT_QUERIES,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    dense_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    reranker_model: str = "cross-encoder/ms-marco-TinyBERT-L-2-v2",
    rerank_candidate_k: int = 20,
    top_k: int = 5,
) -> tuple[list[dict], list[dict]]:
    documents = load_jsonl(documents_path)
    queries = load_jsonl(queries_path)
    validate_inputs(documents, queries)

    retrievers = build_retrievers(
        documents,
        dense_model=dense_model,
        reranker_model=reranker_model,
        rerank_candidate_k=rerank_candidate_k,
    )
    metrics_rows: list[dict] = []
    per_query_rows: list[dict] = []

    for config_name, retriever in retrievers.items():
        metrics, rows = evaluate_retriever(config_name, retriever, queries, top_k=top_k)
        metrics_rows.append(metrics)
        per_query_rows.extend(rows)

    write_csv(results_dir / "metrics.csv", metrics_rows)
    write_csv(results_dir / "per_query_results.csv", per_query_rows)
    return metrics_rows, per_query_rows

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from evaluate import run_evaluation  # noqa: E402
from plot_results import plot_metrics  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all retrieval benchmark configs.")
    parser.add_argument(
        "--documents",
        type=Path,
        default=ROOT / "data" / "processed" / "documents.jsonl",
    )
    parser.add_argument(
        "--queries",
        type=Path,
        default=ROOT / "data" / "processed" / "queries.jsonl",
    )
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    parser.add_argument(
        "--dense-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
    )
    parser.add_argument(
        "--reranker-model",
        default="cross-encoder/ms-marco-TinyBERT-L-2-v2",
    )
    parser.add_argument("--rerank-candidate-k", type=int, default=20)
    args = parser.parse_args()

    metrics_rows, _ = run_evaluation(
        documents_path=args.documents,
        queries_path=args.queries,
        results_dir=args.results_dir,
        dense_model=args.dense_model,
        reranker_model=args.reranker_model,
        rerank_candidate_k=args.rerank_candidate_k,
    )
    plot_metrics(args.results_dir / "metrics.csv", args.results_dir / "metrics_plot.png")

    for row in metrics_rows:
        print(
            f"{row['config']}: "
            f"recall@5={row['recall_at_5']:.3f}, "
            f"mrr={row['mrr']:.3f}, "
            f"p95={row['p95_latency_ms']:.1f}ms"
        )


if __name__ == "__main__":
    main()

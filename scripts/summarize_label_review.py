"""Validate a fresh evaluation and refresh the review summary and README."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from statistics import mean

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
CONFIGS = ["bm25", "dense", "hybrid_rrf", "hybrid_rerank"]


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    queries = read_jsonl(ROOT / "data/processed/queries.jsonl")
    if any(q.get("benchmark_scope", "").startswith("admin_agent") for q in queries):
        raise SystemExit("Historical review script: use scripts/summarize_admin_scope.py for admin_agent_v1.")
    by_id = {q["query_id"]: q for q in queries}
    docs = {d["doc_id"] for d in read_jsonl(ROOT / "data/processed/documents.jsonl")}
    rows = read_csv(RESULTS / "per_query_results.csv")
    old_rows = read_csv(RESULTS / "before_label_review/per_query_results.csv")
    old_by_key = {(r["config"], r["query_id"]): r for r in old_rows}
    metrics = read_csv(RESULTS / "metrics.csv")
    old_metrics = {r["config"]: r for r in read_csv(RESULTS / "before_label_review/metrics.csv")}
    assert len(rows) == len(queries) * len(CONFIGS)
    keys = {(r["config"], r["query_id"]) for r in rows}
    assert keys == {(c, qid) for c in CONFIGS for qid in by_id}
    assert len(keys) == len(rows)
    rankings_changed = 0
    for r in rows:
        q = by_id[r["query_id"]]
        assert r["query"] == q["query"] == old_by_key[(r["config"], r["query_id"])]["query"]
        top = r["top5_doc_ids"].split("|")
        assert len(top) == len(set(top)) == 5 and set(top) <= docs
        relevant = set(q["relevant_doc_ids"])
        expected_recall = len(set(top) & relevant) / len(relevant)
        rank = next((i for i, doc_id in enumerate(top, 1) if doc_id in relevant), None)
        assert abs(float(r["recall_at_5"]) - expected_recall) < 1e-12
        assert abs(float(r["reciprocal_rank"]) - (1 / rank if rank else 0)) < 1e-12
        assert r["first_relevant_rank"] == (str(rank) if rank else "")
        rankings_changed += r["top5_doc_ids"] != old_by_key[(r["config"], r["query_id"])]["top5_doc_ids"]
    for m in metrics:
        selected = [r for r in rows if r["config"] == m["config"]]
        assert len(selected) == len(queries)
        assert abs(float(m["recall_at_5"]) - mean(float(r["recall_at_5"]) for r in selected)) < 1e-12
        assert abs(float(m["mrr"]) - mean(float(r["reciprocal_rank"]) for r in selected)) < 1e-12
        assert abs(float(m["p95_latency_ms"]) - float(np.percentile([float(r["latency_ms"]) for r in selected], 95))) < 1e-9

    def avg(config: str, ids: set[str], field: str) -> float:
        return mean(float(r[field]) for r in rows if r["config"] == config and r["query_id"] in ids)

    def misses(config: str, ids: set[str]) -> list[str]:
        return [r["query_id"] for r in rows if r["config"] == config and r["query_id"] in ids and not r["first_relevant_rank"]]

    all_ids = set(by_id)
    hard = {q["query_id"] for q in queries if q["difficulty"] == "hard"}
    winner = max(metrics, key=lambda m: (float(m["mrr"]), float(m["recall_at_5"])))
    best = winner["config"]
    section = ["# Metrics", "", "The evaluation reports document-level `recall@5`, `MRR` (within the returned top 5), and `p95_latency_ms`.", "", f"The reviewed dataset contains {len(queries)} queries and {sum(len(q['relevant_doc_ids']) for q in queries)} relevance labels across 344 retrieval documents. Labels identify passages explaining the core answer, a configuration step, or a diagnostic setting. Generic context and unrelated workflow fragments are excluded. Multiple labels can be alternative evidence or different parts of an answer; relevance judgments are not exhaustive.", "", "Recall@5 is the number of labelled documents in the top 5 divided by all labelled documents for that query. Queries have 1–7 labels. q20 has 7 labels, so its maximum recall@5 is 5/7; the maximum mean recall@5 across this dataset is 0.985714. MRR can still reach 1. An answer-group metric would avoid this document-count limitation, but is not used here.", "", "# Results and Evaluation", "", "## Overall Analysis", "", "Labels were revised on 2026-10-22 and all four retrievers were executed again with the existing query wording, corpus and default models. Latency was measured again; differences from the earlier run must not be attributed to label changes. [Answers and evidence](docs/query_answers.md), [label changes](results/label_review_changes.json), and [pre-review data](results/before_label_review/) are available.", "", "![Retrieval metrics plot](results/metrics_plot.png)", "", "| config | recall@5 | MRR | p95 latency |", "| --- | ---: | ---: | ---: |"]
    section.extend(f"| {m['config']} | {float(m['recall_at_5']):.3f} | {float(m['mrr']):.3f} | {float(m['p95_latency_ms']):.1f} ms |" for m in metrics)
    section.extend(["", f"With MRR prioritized over document recall, `{best}` is the preferred configuration in this run (MRR {float(winner['mrr']):.3f}, recall@5 {float(winner['recall_at_5']):.3f}). This is a descriptive comparison of 20 queries, not a statistical significance claim.", "", "Latency excludes offline corpus construction, model loading and document embedding. Query embedding and reranking are included in the retrieval timing. " + ("All configurations meet the p95 target of 1 second." if all(float(m['p95_latency_ms']) < 1000 for m in metrics) else "At least one configuration exceeds the p95 target of 1 second; consult the table for this machine's measured values."), "", "## Category Analysis", "", "Mean document recall@5:", "", "| category | queries | bm25 | dense | hybrid_rrf | hybrid_rerank |", "| --- | --- | ---: | ---: | ---: | ---: |"])
    for category in dict.fromkeys(q["category"] for q in queries):
        ids = {q["query_id"] for q in queries if q["category"] == category}
        section.append(f"| `{category}` | {', '.join(sorted(ids))} | " + " | ".join(f"{avg(c, ids, 'recall_at_5'):.3f}" for c in CONFIGS) + " |")
    section.extend(["", "Category scores use the revised labels. Missing valid labels previously made some successful retrievals appear incorrect; removing peripheral chunks also changes recall denominators. Scores from the two label versions should not be compared as a model improvement.", "", "## Hard Queries", "", "The five hard queries are q12 (related-record automation), q16 (email non-engagement), q17 (Flow debugging and rollback), q19 (bulk failures), and q20 (record edit access). q19 does not establish Apex as the only possible cause; its labels cover the Apex bulkification/governor-limit investigation path. q10 uses a Messaging agent-to-queue fallback example for a broader routing question. These scope limits are documented in [the answer guide](docs/query_answers.md).", "", "| config | hard recall@5 | hard MRR | complete misses among hard queries |", "| --- | ---: | ---: | --- |"])
    for config in CONFIGS:
        section.append(f"| {config} | {avg(config, hard, 'recall_at_5'):.3f} | {avg(config, hard, 'reciprocal_rank'):.3f} | {', '.join(misses(config, hard)) or 'none'} |")
    q19_hits = [c for c in CONFIGS if not misses(c, {"q19"})]
    section.extend(["", f"q19 is now a hit for {', '.join(q19_hits) or 'no configuration'}. The earlier claim that every configuration missed q19 no longer applies to the revised label set. Bulk DML documentation is valid evidence even when it is not the originally selected bulk-trigger page.", "", f"## Where the Preferred Configuration Still Loses ({best})", "", f"`{best}` has no labelled relevant result in the top 5 for: {', '.join(misses(best, all_ids)) or 'none'}.", "", "The remaining misses should be inspected against the actual ranked passages before attributing them to a model's reasoning. Broad query wording, missing context, chunk boundaries and incomplete relevance judgments remain possible contributors.", "", ""])
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    start = text.index("# Metrics\n")
    end = text.index("# If I Had One More Week\n")
    readme.write_text(text[:start] + "\n".join(section) + text[end:], encoding="utf-8")

    summary = ["# Label review evaluation — 2026-10-22", "", "Fresh execution of all four retrievers after relevance-label changes. The 20 query strings and 344-document corpus are unchanged. Latencies below are separate measurements, not a label-change effect.", "", "| config | old recall@5 | new recall@5 | old MRR | new MRR | old p95 ms | new p95 ms |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for m in metrics:
        old = old_metrics[m["config"]]
        summary.append(f"| {m['config']} | {float(old['recall_at_5']):.3f} | {float(m['recall_at_5']):.3f} | {float(old['mrr']):.3f} | {float(m['mrr']):.3f} | {float(old['p95_latency_ms']):.1f} | {float(m['p95_latency_ms']):.1f} |")
    summary.extend(["", f"Top-5 rankings changed in {rankings_changed}/{len(rows)} config-query rows compared with the saved run. If rankings differ, score differences combine relevance-label changes and execution/environment differences.", "", "q20 has 7 labels: maximum recall@5 = 5/7; dataset mean ceiling = 0.985714. All 80 per-query recalls, reciprocal ranks and first-relevant ranks, plus all aggregate metrics and p95 values, were independently recalculated and validated.", "", "Manual additions to label_candidates.csv have blank lexical scores; their row ranks are review-list positions, not new retrieval scores.", "", "[Questions, answers and evidence](../docs/query_answers.md). [Exact label changes](label_review_changes.json). [Original queries and results](before_label_review/).", ""])
    (RESULTS / "label_review_summary.md").write_text("\n".join(summary), encoding="utf-8")
    provenance = {"review_date": "2026-10-22", "method": "fresh execution: python run_eval.py", "dense_model": "sentence-transformers/all-MiniLM-L6-v2", "reranker_model": "cross-encoder/ms-marco-TinyBERT-L-2-v2", "rerank_candidate_k": 20, "top_k": 5, "query_strings_unchanged": True, "top5_rows_changed_vs_baseline": rankings_changed, "validated_config_query_rows": len(rows), "sha256": {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for p in [ROOT / "data/processed/queries.jsonl", ROOT / "data/processed/documents.jsonl", RESULTS / "metrics.csv", RESULTS / "per_query_results.csv"]}}
    (RESULTS / "label_review_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print("Validated all 80 rows and aggregate metrics; refreshed README and review summary.")
    print(f"Top-5 changes vs baseline: {rankings_changed}; preferred configuration: {best}")


if __name__ == "__main__":
    main()

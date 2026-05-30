from __future__ import annotations

import argparse
import json
from pathlib import Path
from textwrap import shorten


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCUMENTS = ROOT / "data" / "processed" / "documents.jsonl"
DEFAULT_QUERIES = ROOT / "data" / "processed" / "queries.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def print_query_summary(query: dict) -> None:
    doc_ids = query.get("relevant_doc_ids", [])
    print(
        f"{query['query_id']} | {query.get('difficulty', '')} | "
        f"{query.get('category', '')} | labels={len(doc_ids)}"
    )
    print(f"  {query['query']}")
    print(f"  relevant_doc_ids: {', '.join(doc_ids) if doc_ids else '<none>'}")


def print_labeled_document(document: dict, snippet_chars: int) -> None:
    print(f"\n--- {document['doc_id']}")
    print(f"title: {document.get('title', '')}")
    print(f"source: {document.get('source_file', '')}")
    print(f"product_area: {document.get('product_area', '')}")
    print(f"url: {document.get('url', '')}")
    print("text:")
    print(shorten(document.get("text", ""), width=snippet_chars, placeholder=" ..."))


def review_query(
    query_id: str,
    documents: list[dict],
    queries: list[dict],
    snippet_chars: int,
) -> None:
    documents_by_id = {document["doc_id"]: document for document in documents}
    queries_by_id = {query["query_id"]: query for query in queries}

    if query_id not in queries_by_id:
        available = ", ".join(query["query_id"] for query in queries)
        raise SystemExit(f"Unknown query_id: {query_id}. Available: {available}")

    query = queries_by_id[query_id]
    print_query_summary(query)

    if query.get("expected_source"):
        print(f"  expected_source: {query['expected_source']}")
    if query.get("label_search_terms"):
        print(f"  label_search_terms: {', '.join(query['label_search_terms'])}")

    for doc_id in query.get("relevant_doc_ids", []):
        document = documents_by_id.get(doc_id)
        if not document:
            print(f"\n--- {doc_id}")
            print("MISSING FROM documents.jsonl")
            continue
        print_labeled_document(document, snippet_chars)


def main() -> None:
    parser = argparse.ArgumentParser(description="Review query relevance labels.")
    parser.add_argument("query_id", nargs="?", help="Query ID to inspect, for example q10.")
    parser.add_argument("--documents", type=Path, default=DEFAULT_DOCUMENTS)
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERIES)
    parser.add_argument("--snippet-chars", type=int, default=1200)
    args = parser.parse_args()

    documents = load_jsonl(args.documents)
    queries = load_jsonl(args.queries)

    if args.query_id:
        review_query(args.query_id, documents, queries, args.snippet_chars)
        return

    for query in queries:
        print_query_summary(query)


if __name__ == "__main__":
    main()

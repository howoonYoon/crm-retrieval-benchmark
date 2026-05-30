from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from statistics import mean, median


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "data" / "processed" / "documents.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def token_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9_]+", text.lower()))


def duplicated(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect processed corpus statistics.")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    args = parser.parse_args()

    documents = load_jsonl(args.corpus)
    lengths = [token_count(document.get("text", "")) for document in documents]

    print(f"documents: {len(documents)}")
    if not documents:
        return

    print(f"tokens mean: {mean(lengths):.1f}")
    print(f"tokens median: {median(lengths):.1f}")
    print(f"tokens min: {min(lengths)}")
    print(f"tokens max: {max(lengths)}")

    short_docs = [
        document["doc_id"]
        for document, length in zip(documents, lengths)
        if length < 50
    ]
    duplicate_ids = duplicated([document["doc_id"] for document in documents])
    duplicate_titles = duplicated([document["title"] for document in documents])

    if short_docs:
        print(f"short documents under 50 tokens: {len(short_docs)}")
        print(", ".join(short_docs[:20]))
    if duplicate_ids:
        print(f"duplicate doc_ids: {', '.join(duplicate_ids[:20])}")
    if duplicate_titles:
        print(f"duplicate titles: {', '.join(duplicate_titles[:20])}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .retrievers import BM25Retriever, DenseRetriever, HybridRRFRetriever
except ImportError:  # Support the repository's existing src-on-sys.path scripts.
    from retrievers import BM25Retriever, DenseRetriever, HybridRRFRetriever


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCUMENTS = ROOT / "data" / "processed" / "documents.jsonl"
DEFAULT_DENSE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
ALLOWED_STRATEGIES = {"bm25", "dense", "hybrid_rrf"}


class DocumentSearchService:
    """Reusable document search service with MCP-safe JSON responses."""

    def __init__(
        self,
        documents_path: Path = DEFAULT_DOCUMENTS,
        dense_model: str = DEFAULT_DENSE_MODEL,
    ) -> None:
        self.documents_path = Path(documents_path)
        self.dense_model = dense_model
        self.documents = self._load_documents(self.documents_path)
        self.documents_by_id = {
            document["doc_id"]: document for document in self.documents
        }
        self._retrievers: dict[str, Any] = {}

    @staticmethod
    def _load_documents(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            raise FileNotFoundError(f"Document corpus not found: {path}")
        with path.open("r", encoding="utf-8") as file:
            documents = [json.loads(line) for line in file if line.strip()]
        if not documents:
            raise ValueError(f"Document corpus is empty: {path}")
        return documents

    def _get_retriever(self, strategy: str):
        if strategy not in ALLOWED_STRATEGIES:
            allowed = ", ".join(sorted(ALLOWED_STRATEGIES))
            raise ValueError(f"Unsupported strategy '{strategy}'. Choose one of: {allowed}")

        if strategy in self._retrievers:
            return self._retrievers[strategy]

        if strategy == "bm25":
            retriever = BM25Retriever(self.documents)
        elif strategy == "dense":
            retriever = DenseRetriever(self.documents, model_name=self.dense_model)
        else:
            bm25 = self._get_retriever("bm25")
            dense = self._get_retriever("dense")
            retriever = HybridRRFRetriever(bm25=bm25, dense=dense)

        self._retrievers[strategy] = retriever
        return retriever

    def search_documents(
        self,
        query: str,
        top_k: int = 5,
        strategy: str = "hybrid_rrf",
    ) -> dict[str, Any]:
        query = query.strip()
        if not query:
            raise ValueError("query must not be empty")
        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be between 1 and 10")

        retriever = self._get_retriever(strategy)
        ranked_results = retriever.search(query, top_k=top_k)
        evidence: list[dict[str, Any]] = []

        for rank, result in enumerate(ranked_results, start=1):
            document = self.documents_by_id[result.doc_id]
            text = str(document.get("text", "")).strip()
            evidence.append(
                {
                    "evidence_id": f"docs:{result.doc_id}",
                    "source_type": "salesforce_docs",
                    "source_ref": str(document.get("url") or result.doc_id),
                    "doc_id": result.doc_id,
                    "rank": rank,
                    "score": float(result.score),
                    "title": str(document.get("title", "")),
                    "url": str(document.get("url", "")),
                    "section": str(document.get("section", "")),
                    "excerpt": text[:1200],
                    "document_type": str(document.get("document_type", "")),
                    "product_area": str(document.get("product_area", "")),
                    "page_start": document.get("page_start"),
                    "page_end": document.get("page_end"),
                }
            )

        return {
            "schema_version": "1.0",
            "status": "ok",
            "query": query,
            "strategy": strategy,
            "top_k": top_k,
            "evidence": evidence,
            "error_code": None,
            "retryable": False,
        }


_default_service: DocumentSearchService | None = None


def search_documents(
    query: str,
    top_k: int = 5,
    strategy: str = "hybrid_rrf",
) -> dict[str, Any]:
    """Search Salesforce documents and return an MCP-serializable response."""

    global _default_service
    if _default_service is None:
        _default_service = DocumentSearchService()
    return _default_service.search_documents(query, top_k=top_k, strategy=strategy)

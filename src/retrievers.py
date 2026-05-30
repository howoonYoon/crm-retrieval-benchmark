from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


@dataclass(frozen=True)
class SearchResult:
    doc_id: str
    score: float


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def document_text(document: dict) -> str:
    title = document.get("title", "")
    product_area = document.get("product_area", "")
    text = document.get("text", "")
    return f"{title}\n{product_area}\n{text}"


class BM25Retriever:
    name = "bm25"

    def __init__(self, documents: list[dict]):
        from rank_bm25 import BM25Okapi

        self.doc_ids = [document["doc_id"] for document in documents]
        tokenized_documents = [tokenize(document_text(document)) for document in documents]
        self.index = BM25Okapi(tokenized_documents)

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        scores = self.index.get_scores(tokenize(query))
        top_indexes = np.argsort(scores)[::-1][:top_k]
        return [
            SearchResult(doc_id=self.doc_ids[index], score=float(scores[index]))
            for index in top_indexes
        ]


class DenseRetriever:
    name = "dense"

    def __init__(
        self,
        documents: list[dict],
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        from sentence_transformers import SentenceTransformer

        self.doc_ids = [document["doc_id"] for document in documents]
        self.model = SentenceTransformer(model_name)
        texts = [document_text(document) for document in documents]
        self.embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        scores = np.matmul(self.embeddings, query_embedding)
        top_indexes = np.argsort(scores)[::-1][:top_k]
        return [
            SearchResult(doc_id=self.doc_ids[index], score=float(scores[index]))
            for index in top_indexes
        ]


class HybridRRFRetriever:
    name = "hybrid_rrf"

    def __init__(
        self,
        bm25: BM25Retriever,
        dense: DenseRetriever,
        rrf_k: int = 60,
        bm25_weight: float = 1.0,
        dense_weight: float = 1.0,
    ):
        self.bm25 = bm25
        self.dense = dense
        self.rrf_k = rrf_k
        self.bm25_weight = bm25_weight
        self.dense_weight = dense_weight

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        pool_size = max(50, top_k)
        scores: dict[str, float] = {}

        for rank, result in enumerate(self.bm25.search(query, pool_size), start=1):
            scores[result.doc_id] = scores.get(result.doc_id, 0.0) + (
                self.bm25_weight / (self.rrf_k + rank)
            )

        for rank, result in enumerate(self.dense.search(query, pool_size), start=1):
            scores[result.doc_id] = scores.get(result.doc_id, 0.0) + (
                self.dense_weight / (self.rrf_k + rank)
            )

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return [
            SearchResult(doc_id=doc_id, score=float(score))
            for doc_id, score in ranked[:top_k]
        ]


class HybridRerankRetriever:
    name = "hybrid_rerank"

    def __init__(
        self,
        documents: list[dict],
        candidate_retriever: HybridRRFRetriever,
        model_name: str = "cross-encoder/ms-marco-TinyBERT-L-2-v2",
        candidate_k: int = 20,
        batch_size: int = 16,
    ):
        from sentence_transformers import CrossEncoder

        self.documents_by_id = {
            document["doc_id"]: document_text(document) for document in documents
        }
        self.candidate_retriever = candidate_retriever
        self.model = CrossEncoder(model_name)
        self.candidate_k = candidate_k
        self.batch_size = batch_size

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        candidates = self.candidate_retriever.search(
            query,
            top_k=max(self.candidate_k, top_k),
        )
        pairs = [
            (query, self.documents_by_id[result.doc_id])
            for result in candidates
        ]
        scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )
        scores = np.asarray(scores).reshape(-1)

        ranked = sorted(
            zip(candidates, scores),
            key=lambda item: float(item[1]),
            reverse=True,
        )
        return [
            SearchResult(doc_id=result.doc_id, score=float(score))
            for result, score in ranked[:top_k]
        ]

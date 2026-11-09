import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from retrievers import SearchResult
from search_documents import DocumentSearchService


class DocumentSearchServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        corpus_path = Path(self.temp_directory.name) / "documents.jsonl"
        documents = [
            {
                "doc_id": "doc-1",
                "title": "Case Status",
                "url": "https://help.salesforce.com/case-status",
                "section": "Case Management",
                "text": "Configure and troubleshoot Case status values.",
                "document_type": "html",
                "product_area": "Service Cloud",
            },
            {
                "doc_id": "doc-2",
                "title": "Lead Conversion",
                "url": "https://help.salesforce.com/lead-conversion",
                "text": "Convert a Lead into an Account and Contact.",
            },
        ]
        corpus_path.write_text(
            "".join(json.dumps(document) + "\n" for document in documents),
            encoding="utf-8",
        )
        self.service = DocumentSearchService(documents_path=corpus_path)

    def test_response_is_mcp_serializable_and_contains_sources(self):
        class FixtureRetriever:
            def search(self, query, top_k):
                return [SearchResult("doc-1", 0.75)][:top_k]

        self.service._retrievers["bm25"] = FixtureRetriever()
        response = self.service.search_documents("stuck case", 1, "bm25")

        json.dumps(response)
        self.assertEqual(response["schema_version"], "1.0")
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["evidence"][0]["source_type"], "salesforce_docs")
        self.assertEqual(
            response["evidence"][0]["source_ref"],
            "https://help.salesforce.com/case-status",
        )
        self.assertIn("Case status", response["evidence"][0]["excerpt"])

    def test_rejects_invalid_inputs(self):
        for query, top_k, strategy in [
            ("", 5, "bm25"),
            ("case", 0, "bm25"),
            ("case", 11, "bm25"),
            ("case", 5, "unknown"),
        ]:
            with self.subTest(query=query, top_k=top_k, strategy=strategy):
                with self.assertRaises(ValueError):
                    self.service.search_documents(query, top_k, strategy)


if __name__ == "__main__":
    unittest.main()

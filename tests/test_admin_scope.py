import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from build_corpus import admin_supplement_documents, chunk_source_text
from evaluate import SearchResult, aspect_recall_at_k, evaluate_retriever, validate_inputs


class AspectEvaluationTests(unittest.TestCase):
    def test_supplementary_hits_receive_no_core_credit(self):
        class ContextRetriever:
            def search(self, query, top_k):
                return [SearchResult('oauth', 1)]
        query = {'query_id': 'q', 'query': 'Send approved templates', 'relevant_doc_ids': ['template_steps'], 'supplementary_doc_ids': ['oauth']}
        validate_inputs([{'doc_id': 'template_steps'}, {'doc_id': 'oauth'}], [query])
        metrics, rows = evaluate_retriever('fixture', ContextRetriever(), [query], 5)
        self.assertEqual(metrics['recall_at_5'], 0)
        self.assertEqual(metrics['mrr'], 0)
        self.assertNotIn('aspect_recall_at_5', metrics)
        self.assertIsNone(rows[0]['first_relevant_rank'])

    def test_core_and_context_cannot_overlap_and_changed_core_requires_review(self):
        import hashlib
        docs = [{'doc_id': 'core', 'text': 'Original direct answer'}]
        with self.assertRaisesRegex(ValueError, 'overlap'):
            validate_inputs(docs, [{'query_id': 'q', 'relevant_doc_ids': ['core'], 'supplementary_doc_ids': ['core']}])
        query = {'query_id': 'q', 'relevant_doc_ids': ['core'], 'core_label_text_sha256': {'core': hashlib.sha256(docs[0]['text'].encode()).hexdigest()}}
        validate_inputs(docs, [query])
        with self.assertRaisesRegex(ValueError, 'Core source changed'):
            validate_inputs([{'doc_id': 'core', 'text': 'Changed to a different subject'}], [query])

    def test_aspects_count_groups_not_number_of_documents(self):
        aspects = [
            {"aspect_id": "setup", "relevant_doc_ids": ["a", "b", "c"]},
            {"aspect_id": "code", "relevant_doc_ids": ["d"]},
        ]
        self.assertEqual(aspect_recall_at_k([SearchResult("a", 1), SearchResult("b", .9)], aspects), .5)
        self.assertEqual(aspect_recall_at_k([SearchResult("c", 1), SearchResult("d", .9)], aspects), 1)
        self.assertEqual(aspect_recall_at_k([SearchResult("x", 1)], aspects), 0)

    def test_invalid_aspect_cannot_silently_change_denominator(self):
        docs = [{"doc_id": "a"}, {"doc_id": "b"}]
        for aspects in [[{"aspect_id": "s", "relevant_doc_ids": []}], [{"aspect_id": "s", "relevant_doc_ids": ["x"]}], [{"aspect_id": "s", "relevant_doc_ids": ["a"]}]]:
            with self.subTest(aspects=aspects), self.assertRaises(ValueError):
                validate_inputs(docs, [{"query_id": "q", "relevant_doc_ids": ["a", "b"], "answer_aspects": aspects}])

    def test_new_metric_is_macro_average_and_legacy_queries_work(self):
        class Retriever:
            def search(self, query, top_k):
                return [SearchResult("irrelevant", 2), SearchResult("a", 1)]
        queries = [
            {"query_id": "q1", "query": "one", "relevant_doc_ids": ["a", "b"], "answer_aspects": [{"aspect_id": "s", "relevant_doc_ids": ["a"]}, {"aspect_id": "c", "relevant_doc_ids": ["b"]}]},
            {"query_id": "q2", "query": "two", "relevant_doc_ids": ["a"], "answer_aspects": [{"aspect_id": "s", "relevant_doc_ids": ["a"]}]},
        ]
        metrics, rows = evaluate_retriever("fixture", Retriever(), queries, 5)
        self.assertEqual(metrics['aspect_recall_at_5'], .75)
        self.assertEqual(metrics['mrr'], .5)
        self.assertEqual([r['aspect_recall_at_5'] for r in rows], [.5, 1])
        for query in queries:
            del query['answer_aspects']
        metrics, rows = evaluate_retriever("fixture", Retriever(), queries, 5)
        self.assertNotIn('aspect_recall_at_5', metrics)
        self.assertNotIn('aspect_recall_at_5', rows[0])


class CuratedPassageTests(unittest.TestCase):
    def test_code_punctuation_and_newlines_survive_chunking(self):
        code = "SELECT Id, Name\nFROM Account WHERE Name = 'Example';\nmerge mainAccount duplicateAccount;"
        self.assertEqual(chunk_source_text(code), [code])
        self.assertIn("'Example';", chunk_source_text(code, 12, 2)[0])

    def test_markers_bound_the_passage_and_ids_are_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'urls.txt').write_text('https://example.test/sales_core.pdf\n', encoding='utf-8')
            text = 'unrelated prefix BEGIN ' + ' '.join(f'word{i}' for i in range(90)) + ' END unrelated suffix'
            (root / 'sales_core.jsonl').write_text(json.dumps({'page': 1, 'text': text}) + '\n', encoding='utf-8')
            spec = {'key': 'fixture', 'source_file': 'sales_core.pdf', 'page_start': 1, 'page_end': 1, 'title': 'Fixture', 'start_marker': 'BEGIN', 'end_marker': 'END'}
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps([spec]), encoding='utf-8')
            first = admin_supplement_documents(root / 'urls.txt', root, manifest)
            self.assertEqual(first, admin_supplement_documents(root / 'urls.txt', root, manifest))
            self.assertTrue(first[0]['text'].startswith('BEGIN word0'))
            self.assertNotIn('unrelated', first[0]['text'])
            self.assertNotIn('END', first[0]['text'])
            spec['start_marker'] = 'MISSING'
            manifest.write_text(json.dumps([spec]), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Missing start marker'):
                admin_supplement_documents(root / 'urls.txt', root, manifest)


if __name__ == '__main__':
    unittest.main()

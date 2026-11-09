import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from build_corpus import admin_supplement_documents, chunk_source_text
from evaluate import SearchResult, evaluate_retriever, validate_inputs


class CoreEvaluationTests(unittest.TestCase):
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

    def test_recall_and_mrr_are_macro_averages(self):
        class Retriever:
            def search(self, query, top_k):
                return [SearchResult("irrelevant", 2), SearchResult("a", 1)]
        queries = [
            {"query_id": "q1", "query": "one", "relevant_doc_ids": ["a", "b"]},
            {"query_id": "q2", "query": "two", "relevant_doc_ids": ["a"]},
        ]
        metrics, rows = evaluate_retriever("fixture", Retriever(), queries, 5)
        self.assertEqual(metrics['recall_at_5'], .75)
        self.assertEqual(metrics['mrr'], .5)
        self.assertEqual([r['recall_at_5'] for r in rows], [.5, 1])
        self.assertEqual([r['first_relevant_rank'] for r in rows], [2, 2])
        self.assertNotIn('aspect_recall_at_5', metrics)
        self.assertNotIn('aspect_recall_at_5', rows[0])

    def test_first_hit_rank_and_reciprocal_rank_agree(self):
        class Retriever:
            def search(self, query, top_k):
                return [SearchResult(doc_id, 0) for doc_id in rankings[query]][:top_k]

        rankings = {
            'first': ['gold', 'other'],
            'last': ['a', 'b', 'c', 'd', 'gold'],
            'miss': ['other'],
            'empty': [],
        }
        queries = [{'query_id': key, 'query': key, 'relevant_doc_ids': ['gold']} for key in rankings]
        _, rows = evaluate_retriever('fixture', Retriever(), queries, 5)
        self.assertEqual([r['first_relevant_rank'] for r in rows], [1, 5, None, None])
        self.assertEqual([r['reciprocal_rank'] for r in rows], [1, .2, 0, 0])


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

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from build_html_corpus import canonical_url, chunk_sections, extract_sections
from build_corpus import tokens
from retrievers import document_text


class HTMLCorpusTests(unittest.TestCase):
    def test_canonicalization_keeps_article_identity(self):
        self.assertEqual(canonical_url('https://help.salesforce.com/s/articleView?utm_source=x&id=sf.one&type=5#x'), 'https://help.salesforce.com/s/articleView?id=sf.one&language=en_US&type=5')
        self.assertNotEqual(canonical_url('https://help.salesforce.com/s/articleView?id=sf.one'), canonical_url('https://help.salesforce.com/s/articleView?id=sf.two'))
        with self.assertRaises(ValueError):
            canonical_url('https://example.org/docs')

    def test_shell_is_not_an_article(self):
        with self.assertRaises(ValueError):
            extract_sections('<html><nav>Salesforce documentation</nav><main><doc-xml-content></doc-xml-content></main></html>')

    def test_sections_remove_navigation_and_preserve_code(self):
        text = ' '.join(['Configuration explains account permissions and record access.'] * 8)
        html = f'<nav>MENU NOISE</nav><main><h1>Permissions</h1><p>{text}</p><h2>Code</h2><pre>SELECT Id, Name\nFROM Account WHERE Name = \'Example\';</pre><h3>Notes</h3><p>{text}</p><footer>FOOTER NOISE</footer></main>'
        title, sections = extract_sections(html)
        self.assertEqual(title, 'Permissions')
        self.assertEqual([s['section'] for s in sections], ['Permissions', 'Permissions > Code', 'Permissions > Code > Notes'])
        merged = str(sections)
        self.assertNotIn('NOISE', merged)
        self.assertIn("'Example';", merged)

    def test_tables_repeat_headers_and_chunks_have_stable_metadata(self):
        rows = ''.join(f'<tr><td>Field{i}</td><td>{"Field description with permissions " * 12}</td></tr>' for i in range(18))
        title, sections = extract_sections(f'<main><h1>Object fields</h1><table><tr><th>Field</th><th>Description</th></tr>{rows}</table></main>')
        page = dict(source_id='fixture', title=title, url='https://developer.salesforce.com/docs/test', sections=sections, fetched_at='fixed', source_sha256='hash', extraction_method='fixture')
        chunks = chunk_sections(page)
        self.assertEqual(chunks, chunk_sections(page))
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertIn('| Field | Description |', chunk['text'])
            self.assertLessEqual(len(tokens(chunk['text'])), 220)
            self.assertEqual(chunk['document_type'], 'html')
            self.assertEqual(chunk['url'], page['url'])
            self.assertIn(chunk['section'], document_text(chunk))


if __name__ == '__main__':
    unittest.main()

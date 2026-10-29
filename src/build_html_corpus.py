"""Ingest official Salesforce HTML, including Atlas content APIs and rendered Help.

The processed page snapshots are checked in for deterministic offline rebuilding.
Raw responses/rendered DOMs are local cache files; failed or empty pages are excluded.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

from build_corpus import chunk_source_text, tokens

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'data/raw/html_sources.json'
CACHE = ROOT / 'data/raw/html'
PAGES = ROOT / 'data/processed/html_pages.jsonl'
CHUNKS = ROOT / 'data/processed/html_documents.jsonl'
ALLOWED_HOSTS = {'developer.salesforce.com', 'help.salesforce.com'}
MAX_TOKENS = 220


def canonical_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username:
        raise ValueError(f'Not an approved official Salesforce URL: {url}')
    pairs = [(k, v) for k, v in parse_qsl(parsed.query) if not k.lower().startswith('utm_')]
    if parsed.hostname == 'help.salesforce.com' and not any(k == 'language' for k, _ in pairs):
        pairs.append(('language', 'en_US'))
    return urlunsplit(('https', parsed.netloc.lower(), parsed.path, urlencode(sorted(pairs)), ''))


def source_id(url: str) -> str:
    return hashlib.sha256(canonical_url(url).encode()).hexdigest()[:16]


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding='utf-8') as file:
        return [json.loads(line) for line in file if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')


def get(url: str) -> requests.Response:
    # Public, unauthenticated requests. A browser UA yields false 403s on some pages.
    response = requests.get(url, timeout=(8, 25))
    response.raise_for_status()
    if urlsplit(response.url).hostname not in ALLOWED_HOSTS:
        raise ValueError(f'Unexpected redirect outside official documentation: {response.url}')
    return response


def select_body(soup: BeautifulSoup) -> Tag:
    for selector in ['#content', 'c-hc-knowledge-article .container', 'article', '.slds-text-longform', '.knowledge-article-content', '[itemprop="articleBody"]', 'main', '[role="main"]']:
        for root in soup.select(selector):
            if len(root.get_text(' ', strip=True)) >= 160 and root.find(re.compile('^h[1-6]$')):
                return root
    # Atlas APIs return an article fragment rather than a complete HTML page.
    if soup.find('h1') and not soup.find(['doc-xml-content', 'script']):
        return soup
    raise ValueError('No substantive article body found (JS shell, error page or unsupported layout)')


def extract_sections(html: str, title_hint: str = '') -> tuple[str, list[dict]]:
    soup = BeautifulSoup(html, 'html.parser')
    for node in soup.select('script, style, noscript, nav, header, footer, aside, form, button, iframe, [role="navigation"], .toc, .sidebar, .breadcrumbs, .feedback'):
        node.decompose()
    root = select_body(soup)
    heading = root.find('h1')
    title = heading.get_text(' ', strip=True) if heading else title_hint
    if not title:
        raise ValueError('Article title missing')
    sections, path, blocks = [], [], []

    def flush():
        nonlocal blocks
        if blocks:
            sections.append({'section': ' > '.join(label for _, label in path) or title, 'blocks': blocks})
            blocks = []

    def walk(node):
        if isinstance(node, NavigableString):
            value = re.sub(r'\s+', ' ', str(node)).strip()
            if value:
                blocks.append(value)
            return
        if not isinstance(node, Tag):
            return
        if re.fullmatch(r'h[1-6]', node.name):
            if not node.get_text(' ', strip=True):
                return
            flush()
            level = int(node.name[1])
            while path and path[-1][0] >= level:
                path.pop()
            path.append((level, node.get_text(' ', strip=True)))
        elif node.name == 'pre':
            blocks.append('```\n' + node.get_text().strip() + '\n```')
        elif node.name == 'table':
            # Repeat the table header on long table fragments; keep rows intact.
            rows = [[cell.get_text(' ', strip=True).replace('|', '\\|') for cell in row.find_all(['th', 'td'], recursive=False)] for row in node.find_all('tr')]
            rows = [row for row in rows if row]
            if rows:
                header = '| ' + ' | '.join(rows[0]) + ' |\n| ' + ' | '.join(['---'] * len(rows[0])) + ' |'
                batch = []
                for row in rows[1:]:
                    text = '| ' + ' | '.join(row) + ' |'
                    if batch and len(tokens(header + '\n' + '\n'.join(batch) + text)) > MAX_TOKENS:
                        blocks.append(header + '\n' + '\n'.join(batch))
                        batch = []
                    batch.append(text)
                blocks.append(header + ('\n' + '\n'.join(batch) if batch else ''))
        elif node.name in {'ul', 'ol'}:
            blocks.append('\n'.join('- ' + item.get_text(' ', strip=True) for item in node.find_all('li', recursive=False)))
        elif node.name in {'p', 'blockquote', 'dt', 'dd'} or 'shortdesc' in node.get('class', []):
            text = node.get_text(' ', strip=True)
            if text:
                blocks.append(text)
        else:
            for child in node.children:
                walk(child)

    walk(root)
    flush()
    text = '\n'.join(block for section in sections for block in section['blocks'])
    if len(tokens(text)) < 30 or any(error in title.lower() for error in ['page not found', 'access denied', 'sorry to interrupt']):
        raise ValueError('Insufficient article text or an error page')
    return title, sections


def chunk_sections(page: dict) -> list[dict]:
    docs = []
    for section_index, section in enumerate(page['sections'], 1):
        section_name = re.sub(r'( >\s*)+$', '', section['section']).strip()
        parts, pending = [], []
        for block in section['blocks']:
            for piece in chunk_source_text(block, MAX_TOKENS, 32):
                if pending and len(tokens('\n\n'.join(pending + [piece]))) > MAX_TOKENS:
                    parts.append('\n\n'.join(pending))
                    pending = []
                pending.append(piece)
        if pending:
            parts.append('\n\n'.join(pending))
        section_key = hashlib.sha256(f"{section_index}:{section_name}".encode()).hexdigest()[:10]
        for index, text in enumerate(parts, 1):
            docs.append({'doc_id': f"sf_html_{page['source_id']}_{section_key}_{index:03d}", 'parent_id': f"sf_html_{page['source_id']}", 'title': page['title'], 'url': page['url'], 'section': section_name, 'section_index': section_index, 'chunk_index': index, 'document_type': 'html', 'source_file': page['source_id'] + '.html', 'product_area': 'Salesforce Developer Documentation' if 'developer.salesforce.com' in page['url'] else 'Salesforce Admin Help', 'text': text, 'fetched_at': page['fetched_at'], 'source_sha256': page['source_sha256'], 'content_sha256': hashlib.sha256(text.encode()).hexdigest(), 'extraction_method': page['extraction_method'], 'source_version': page.get('source_version')})
    return docs


def snapshot(spec: dict, html: str, method: str, version=None) -> dict:
    title, sections = extract_sections(html, spec['title_hint'])
    return {'source_id': source_id(spec['url']), 'url': canonical_url(spec['url']), 'title': title, 'sections': sections, 'document_type': 'html', 'query_hints': spec.get('query_hints', []), 'fetched_at': datetime.now(timezone.utc).isoformat(), 'source_sha256': hashlib.sha256(html.encode()).hexdigest(), 'extraction_method': method, 'source_version': version}


def fetch_static(spec: dict, refresh=False) -> dict:
    url = canonical_url(spec['url'])
    key = source_id(url)
    cache = CACHE / f'{key}.json'
    if cache.exists() and not refresh:
        return json.loads(cache.read_text(encoding='utf-8'))
    response = get(url)
    html = response.content.decode('utf-8')
    (CACHE / f'{key}.html').write_text(html, encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    version, method = None, 'html_main'
    if soup.find('doc-xml-content'):
        # The endpoint contract is exposed by Salesforce's public doc/xmlContent JS.
        _, _, atlas_id, deliverable, topic = urlsplit(url).path.split('/', 4)
        info = get(f'https://developer.salesforce.com/docs/get_document/{atlas_id}').json()
        language, version = info['language']['locale'], info['version']
        endpoint = f"https://developer.salesforce.com/docs/get_document_content/{deliverable}/{topic}/{language}/{version['doc_version']}"
        payload = get(endpoint).json()
        html = payload['content']
        (CACHE / f'{key}.article.html').write_text(html, encoding='utf-8')
        method = 'salesforce_public_article_html'
    elif soup.find('doc-amf-reference'):
        config = json.loads(soup.find('doc-amf-reference')['reference-set-config'])
        reference = next(item for item in config['refList'] if item.get('isSelected'))
        schema_url = urljoin(url, reference['source'])
        try:
            get(schema_url)
        except requests.HTTPError as exc:
            raise ValueError(f"API reference is an empty shell; its official schema is unavailable: {schema_url} ({exc.response.status_code})") from exc
        raise ValueError('OpenAPI reference requires a schema-specific extractor; the empty HTML shell was excluded')
    page = snapshot(spec, html, method, version)
    cache.write_text(json.dumps(page, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return page


async def render_pages(specs: list[dict], channel: str) -> tuple[list[dict], list[dict]]:
    from playwright.async_api import async_playwright
    successes, failures = [], []
    async with async_playwright() as playwright:
        kwargs = {'headless': True}
        if channel:
            kwargs['channel'] = channel
        browser = await playwright.chromium.launch(**kwargs)
        semaphore = asyncio.Semaphore(2)

        async def render(spec):
            async with semaphore:
                page = await browser.new_page(locale='en-US')
                try:
                    await page.goto(spec['url'], wait_until='domcontentloaded', timeout=35000)
                    await page.wait_for_selector('#content h1, c-hc-knowledge-article h1, article h1, .slds-text-longform h1, [itemprop="articleBody"]', timeout=25000)
                    # The title can precede article hydration; require substantive body text.
                    # Playwright locators can traverse Salesforce's component DOM;
                    # document.querySelector is scoped by its synthetic shadow layer.
                    body = page.locator('#content, c-hc-knowledge-article .container, article, .slds-text-longform, [itemprop="articleBody"]').first
                    for attempt in range(20):
                        if len(await body.inner_text()) > 500:
                            break
                        await page.wait_for_timeout(500)
                    else:
                        raise ValueError('Article body did not finish rendering')
                    html = await page.content()
                    result = snapshot(spec, html, 'rendered_html')
                    key = result['source_id']
                    (CACHE / f'{key}.rendered.html').write_text(html, encoding='utf-8')
                    (CACHE / f'{key}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                    successes.append(result)
                    print(f"Rendered OK: {result['title']}", flush=True)
                except Exception as exc:
                    failures.append({'url': spec['url'], 'status': 'failed', 'error': str(exc)[:700]})
                    (CACHE / f"{source_id(spec['url'])}.failed.html").write_text(await page.content(), encoding='utf-8')
                    print(f"Rendered FAILED: {spec['url']} ({str(exc)[:120]})", flush=True)
                finally:
                    await page.close()

        await asyncio.gather(*(render(spec) for spec in specs))
        await browser.close()
    return successes, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', help='Re-chunk checked-in cleaned page snapshots, without network access')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--render', action='store_true', help='Render pages whose static HTML has no body')
    parser.add_argument('--browser-channel', default='msedge' if sys.platform == 'win32' else '')
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    specs = json.loads(SOURCES.read_text(encoding='utf-8'))
    for spec in specs:
        spec['url'] = canonical_url(spec['url'])
    if len({spec['url'] for spec in specs}) != len(specs):
        raise ValueError('Duplicate canonical URLs in manifest')
    failures = []
    if args.offline:
        pages = read_jsonl(PAGES)
        report_path = ROOT / 'data/processed/html_ingestion_report.json'
        if report_path.exists():
            failures = [row for row in json.loads(report_path.read_text(encoding='utf-8'))['pages'] if row['status'] == 'failed']
    else:
        pages, retry = [], []
        with ThreadPoolExecutor(max_workers=3) as pool:
            jobs = {pool.submit(fetch_static, spec, args.refresh): spec for spec in specs}
            for job in as_completed(jobs):
                spec = jobs[job]
                try:
                    page = job.result()
                    pages.append(page)
                    print(f"HTML OK: {page['title']}", flush=True)
                except Exception as exc:
                    retry.append(spec)
                    failures.append({'url': spec['url'], 'status': 'failed', 'error': str(exc)[:700]})
                    print(f"Needs render/review: {spec['title_hint']}", flush=True)
        if args.render and retry:
            rendered, failed = asyncio.run(render_pages(retry, args.browser_channel))
            pages.extend(rendered)
            failures = failed
        pages.sort(key=lambda page: page['url'])
    documents = [document for page in pages for document in chunk_sections(page)]
    if len({page['url'] for page in pages}) != len(pages) or not {page['url'] for page in pages} <= {spec['url'] for spec in specs}:
        raise ValueError('Page snapshots contain duplicate or unrequested URLs')
    if not documents:
        raise ValueError('No valid HTML content; existing corpus has not been modified')
    if len({d['doc_id'] for d in documents}) != len(documents):
        raise ValueError('Duplicate HTML document IDs')
    if not args.offline:
        write_jsonl(PAGES, pages)
    write_jsonl(CHUNKS, documents)
    if not args.offline:
        report = {'requested_urls': len(specs), 'successful_urls': len(pages), 'failed_urls': len(failures), 'chunks': len(documents), 'pages': [{'url': page['url'], 'title': page['title'], 'status': 'ok', 'method': page['extraction_method'], 'source_sha256': page['source_sha256'], 'fetched_at': page['fetched_at'], 'source_version': page.get('source_version'), 'chunks': sum(d['url'] == page['url'] for d in documents)} for page in pages] + failures}
        (ROOT / 'data/processed/html_ingestion_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {len(documents)} HTML chunks from {len(pages)} pages; failures: {len(failures)}', flush=True)


if __name__ == '__main__':
    main()

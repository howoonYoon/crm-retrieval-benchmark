from __future__ import annotations

import argparse
import json
import re
import shutil
import ssl
import urllib.request
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_URLS = ROOT / "data" / "raw" / "source_urls.txt"
DEFAULT_PDF_DIR = ROOT / "data" / "raw" / "pdfs"
DEFAULT_TEXT_CACHE_DIR = ROOT / "data" / "raw" / "pdf_text"
DEFAULT_OUT = ROOT / "data" / "processed" / "documents.jsonl"

CHUNK_TOKENS = 600
CHUNK_OVERLAP = 80


PDF_PROFILES = {
    "agentforce_contact_center_5-30-2026": {
        "title": "Agentforce Contact Center Guide",
        "product_area": "Email-to-Case",
        "terms": [
            "email-to-case",
            "email to case",
            "routing address",
            "incoming email",
            "support email",
            "case",
            "email service",
            "threading",
            "lightning threading",
            "turn on email-to-case",
            "configure email-to-case",
            "add routing addresses",
        ],
        "priority_pages_only": True,
        "priority_pages": list(range(575, 598)),
        "min_chunk_tokens": 40,
        "max_docs_per_pdf": 40,
    },
    "object_reference": {
        "title": "Salesforce Object Reference",
        "product_area": "CRM Objects",
        "terms": [
            "account",
            "asset",
            "case",
            "case comment",
            "case history",
            "contact",
            "contract",
            "email message",
            "entitlement",
            "knowledge article",
            "knowledge article version",
            "opportunity",
            "quote",
            "service contract",
            "user",
        ],
        "use_generic_terms": False,
        "priority_pages_only": True,
        "min_chunk_tokens": 30,
        "short_marker_pages": [3682],
        "max_docs_per_pdf": 50,
        "page_start_markers": {
            266: "Account Represents an individual account",
            1415: "Contact Represents a contact",
            1972: "EmailMessage Represents an email",
            3078: "KnowledgeArticle Provides read-only access",
            3682: "Opportunity Represents an opportunity",
            4595: "Quote Represents a quote",
        },
        "priority_pages": [
            266,
            267,
            276,
            277,
            280,
            284,
            292,
            769,
            779,
            782,
            785,
            1238,
            1240,
            1241,
            1245,
            1249,
            1251,
            1415,
            1422,
            1424,
            1426,
            1430,
            1432,
            1433,
            1603,
            1615,
            1972,
            1973,
            1974,
            3078,
            3090,
            3682,
            3683,
            3684,
            3691,
            4595,
            4602,
            4603,
            4610,
            4611,
            4623,
            4962,
            4969,
            5600,
        ],
    },
    "salesforce_apex_developer_guide": {
        "title": "Salesforce Apex Developer Guide",
        "product_area": "Apex Automation",
        "terms": [
            "apex",
            "trigger",
            "context variable",
            "governor limit",
            "soql",
            "dml",
            "class",
            "test method",
            "future method",
            "queueable",
            "batch apex",
            "exception",
            "warning email",
            "limit warning",
        ],
        "priority_pages": [
            137,
            141,
            142,
            143,
            144,
            145,
            169,
            175,
            176,
            179,
            187,
            268,
            271,
            272,
            273,
            290,
            353,
            354,
            364,
        ],
        "merge_page_ranges": [(271, 273)],
    },
    "console": {
        "title": "Salesforce Console Guide",
        "product_area": "Agent Workspace",
        "terms": [
            "console",
            "service console",
            "workspace",
            "agent",
            "utility bar",
            "split view",
            "case",
            "record page",
            "navigation",
        ],
    },
    "service_presence_administrators": {
        "title": "Service Presence for Administrators",
        "product_area": "Routing",
        "terms": [
            "service presence",
            "omni-channel",
            "routing",
            "presence status",
            "capacity",
            "queue",
            "agent",
            "work item",
            "availability",
        ],
        "priority_pages": [5, 54, 66],
    },
    "lightning_knowledge_guide": {
        "title": "Lightning Knowledge Guide",
        "product_area": "Knowledge",
        "terms": [
            "knowledge",
            "article",
            "data category",
            "publish",
            "agent",
            "case",
            "search",
            "knowledge base",
        ],
        "priority_pages": [11, 12, 30, 31, 34],
    },
    "salesforce_entitlements_implementation_guide": {
        "title": "Salesforce Entitlements Implementation Guide",
        "product_area": "Entitlements",
        "terms": [
            "entitlement",
            "milestone",
            "service contract",
            "sla",
            "case",
            "support process",
            "entitlement process",
        ],
        "priority_pages": [5, 6, 7, 8, 10, 11, 21, 35, 36, 43, 44, 45],
        "max_docs_per_pdf": 12,
    },
    "mc_email": {
        "title": "Marketing Cloud Email Guide",
        "product_area": "Marketing Cloud",
        "terms": [
            "email",
            "subscriber",
            "send",
            "data extension",
            "template",
            "journey",
            "automation",
            "contact",
            "triggered send",
        ],
        "priority_pages": [128, 129, 146, 147, 148, 149, 150, 151, 152, 153, 154, 261],
        "short_marker_pages": [151, 152],
    },
    "mc_journeys_and_automations": {
        "title": "Marketing Cloud Journeys and Automations",
        "product_area": "Marketing Cloud",
        "terms": [
            "journey",
            "journey builder",
            "automation",
            "entry source",
            "activity",
            "contact",
            "data extension",
            "event",
            "decision split",
        ],
        "priority_pages": [
            75,
            102,
            103,
            104,
            253,
            300,
            309,
            310,
            318,
            320,
            321,
            322,
            324,
            325,
            326,
            350,
            351,
            352,
            353,
        ],
        "max_docs_per_pdf": 45,
    },
    "mc_cross-cloud_products": {
        "title": "Marketing Cloud Cross-Cloud Products",
        "product_area": "Marketing Cloud Integration",
        "terms": [
            "service cloud",
            "sales cloud",
            "marketing cloud",
            "connect",
            "synchronized",
            "account",
            "contact",
            "case",
            "journey",
            "data extension",
        ],
    },
    "engagement_audience_builder_and_contact_builder_5-30-2026": {
        "title": "Marketing Cloud Audience Builder and Contact Builder",
        "product_area": "Marketing Cloud Contact Data",
        "terms": [
            "audience builder",
            "contact builder",
            "salesforce data extension",
            "data extension",
            "salesforce",
            "sales cloud",
            "service cloud",
            "synchronized data source",
            "contact key",
            "subscriber key",
            "publish audience",
            "messaging",
            "journey builder",
        ],
        "priority_pages_only": True,
        "priority_pages": [5, 6, 11, 15, 16, 17, 139, 140, 141, 142, 143, 168, 176, 177, 182, 183, 185],
        "merge_page_ranges": [(139, 142)],
        "max_docs_per_pdf": 30,
    },
    "sales_core": {
        "title": "Sales Core Guide",
        "product_area": "Sales Lifecycle",
        "terms": [
            "account",
            "contact",
            "opportunity",
            "quote",
            "contract",
            "asset",
            "lead",
            "forecast",
            "pipeline",
            "product",
            "price book",
        ],
        "max_docs_per_pdf": 35,
        "priority_pages": [96, 104, 109, 117, 118, 166, 218, 219, 220, 228, 243, 277, 280, 281, 282, 283, 284],
        "merge_page_ranges": [(280, 284)],
    },
    "extend_click_automate": {
        "title": "Salesforce Flow and Click-Based Automation Guide",
        "product_area": "CRM Automation",
        "terms": [
            "flow",
            "flow builder",
            "automation",
            "approval",
            "process",
            "record-triggered",
            "scheduled",
            "screen flow",
            "case",
            "record",
            "email alert",
            "assignment",
            "update records",
        ],
        "priority_pages": [5, 30, 31, 36, 37, 97, 100, 157, 238, 239, 240, 241, 242, 243, 244, 277, 278, 319],
        "short_marker_pages": [239, 240, 243, 244],
        "merge_page_ranges": [(238, 244)],
    },
    "setup": {
        "title": "Salesforce Setup Guide",
        "product_area": "Admin Setup",
        "terms": [
            "setup",
            "user",
            "permission",
            "profile",
            "role",
            "queue",
            "assignment",
            "security",
            "sharing",
            "record",
            "case",
            "email",
            "object",
            "field",
            "data loader",
            "data import wizard",
            "import",
            "export",
        ],
        "priority_pages": [411],
    },
    "salesforce_security_impl_guide": {
        "title": "Salesforce Security Implementation Guide",
        "product_area": "Security and Access",
        "terms": [
            "security",
            "permission",
            "profile",
            "role",
            "sharing",
            "record access",
            "object permission",
            "field-level security",
            "user",
            "login",
            "session",
        ],
        "priority_pages": [48, 49, 50],
        "merge_page_ranges": [(48, 50)],
    },
    "salesforce_record_access_under_the_hood": {
        "title": "Salesforce Record Access Under the Hood",
        "product_area": "Security and Access",
        "terms": [
            "record access",
            "sharing",
            "owner",
            "role hierarchy",
            "organization-wide defaults",
            "manual sharing",
            "criteria-based sharing",
            "permission",
            "profile",
            "team",
        ],
    },
    "extend_click": {
        "title": "Salesforce Platform Customization Guide",
        "product_area": "Admin Setup",
        "terms": [
            "customize",
            "object",
            "field",
            "record type",
            "page layout",
            "permission",
            "profile",
            "flow",
            "validation rule",
            "formula",
            "lookup",
            "relationship",
            "case",
        ],
    },
    "data_quality": {
        "title": "Salesforce Data Quality Guide",
        "product_area": "Data Quality",
        "terms": [
            "data quality",
            "duplicate",
            "duplicate rule",
            "matching rule",
            "merge",
            "account",
            "contact",
            "lead",
            "data import",
            "clean",
            "validation",
            "record",
        ],
    },
    "api_cti": {
        "title": "Salesforce Open CTI Guide",
        "product_area": "Contact Center Integration",
        "terms": [
            "open cti",
            "cti",
            "call center",
            "softphone",
            "phone",
            "screen pop",
            "agent",
            "console",
            "service console",
            "lightning",
            "case",
            "contact",
        ],
        "max_docs_per_pdf": 0,
    },
    "messaging_admin_implementation_guide": {
        "title": "Salesforce Messaging Administrator Guide",
        "product_area": "Messaging",
        "terms": [
            "messaging",
            "messaging channel",
            "messaging session",
            "whatsapp",
            "sms",
            "enhanced messaging",
            "agent",
            "routing",
            "queue",
            "omni-channel",
            "service cloud",
            "conversation",
        ],
        "priority_pages": [39, 40],
    },
}


GENERIC_TERMS = [
    "admin",
    "automation",
    "case",
    "configuration",
    "customer",
    "record",
    "salesforce",
    "service",
    "setup",
    "workflow",
]


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def source_urls(path: Path) -> list[str]:
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if value and not value.startswith("#"):
            urls.append(value)
    return urls


def pdf_name(url: str) -> str:
    name = Path(urlparse(url).path).name
    if not name.lower().endswith(".pdf"):
        raise ValueError(f"Source URL is not a PDF: {url}")
    return name


def profile_for(filename: str) -> dict[str, object]:
    stem = Path(filename).stem
    return PDF_PROFILES.get(
        stem,
        {
            "title": stem.replace("_", " ").title(),
            "product_area": "CRM Documentation",
            "terms": GENERIC_TERMS,
        },
    )


def download_pdf(url: str, pdf_dir: Path, refresh: bool = False) -> Path:
    pdf_dir.mkdir(parents=True, exist_ok=True)
    path = pdf_dir / pdf_name(url)
    if path.exists() and path.stat().st_size > 0 and not refresh:
        return path

    parsed = urlparse(url)
    if parsed.scheme == "file":
        source_path = Path(url2pathname(parsed.path))
        if not source_path.exists():
            raise FileNotFoundError(f"Local PDF source does not exist: {source_path}")
        shutil.copyfile(source_path, path)
        return path
    if parsed.scheme == "":
        source_path = Path(url)
        if not source_path.is_absolute():
            source_path = (ROOT / source_path).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Local PDF source does not exist: {source_path}")
        shutil.copyfile(source_path, path)
        return path

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(request, context=context, timeout=120) as response:
        with path.open("wb") as file:
            shutil.copyfileobj(response, file)
    return path


def normalize_text(text: str) -> str:
    replacements = {
        "\ufb00": "ff",
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_pages(pdf_path: Path, cache_dir: Path, refresh: bool = False) -> list[dict]:
    from pypdf import PdfReader

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{pdf_path.stem}.jsonl"
    if cache_path.exists() and not refresh:
        with cache_path.open("r", encoding="utf-8") as file:
            return [json.loads(line) for line in file if line.strip()]

    reader = PdfReader(str(pdf_path))
    pages: list[dict] = []
    for page_index, page in enumerate(reader.pages, start=1):
        text = normalize_text(page.extract_text() or "")
        pages.append(
            {
                "source_file": pdf_path.name,
                "page": page_index,
                "text": text,
            }
        )

    with cache_path.open("w", encoding="utf-8") as file:
        for page in pages:
            file.write(json.dumps(page, ensure_ascii=False) + "\n")
    return pages


def tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*", text)


def detokenize(words: list[str]) -> str:
    return " ".join(words).strip()


def chunk_page_text(
    text: str,
    chunk_tokens: int,
    overlap: int,
    min_tokens: int = 80,
) -> list[str]:
    words = tokens(text)
    if len(words) < min_tokens:
        return []

    chunks: list[str] = []
    step = max(1, chunk_tokens - overlap)
    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_tokens]
        if len(chunk_words) < min_tokens:
            continue
        chunks.append(detokenize(chunk_words))
    return chunks


def looks_like_toc_page(text: str) -> bool:
    dot_leaders = text.count(". . .")
    page_number_refs = len(re.findall(r"\b\d{2,5}\b", text))
    short_lines = [
        line.strip()
        for line in text.splitlines()
        if 10 <= len(line.strip()) <= 90
    ]
    if dot_leaders >= 5:
        return True
    if page_number_refs >= 80 and len(short_lines) >= 20:
        return True
    return False


def score_text(text: str, terms: list[str]) -> int:
    lowered = text.lower()
    score = 0
    for term in terms:
        term_lower = term.lower()
        count = lowered.count(term_lower)
        if " " in term_lower:
            score += count * 3
        else:
            score += count
    return score


def trim_to_marker(text: str, marker: str) -> str:
    pattern = r"\s+".join(re.escape(part) for part in marker.split())
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return text
    return text[match.start() :]


def title_from_chunk(chunk: str, source_title: str, page: int, sequence: int) -> str:
    words = chunk.split()
    prefix = " ".join(words[:10]).strip(" .,:;")
    if len(prefix) < 20:
        return f"{source_title} p{page} chunk {sequence}"
    return f"{source_title} p{page} chunk {sequence}: {prefix}"


def build_chunks_for_pdf(
    url: str,
    pdf_path: Path,
    pages: list[dict],
    min_score: int,
    max_docs_per_pdf: int,
    chunk_tokens: int,
    overlap: int,
) -> list[dict]:
    profile = profile_for(pdf_path.name)
    source_title = str(profile["title"])
    product_area = str(profile["product_area"])
    use_generic_terms = bool(profile.get("use_generic_terms", True))
    terms = list(profile["terms"]) + (GENERIC_TERMS if use_generic_terms else [])
    priority_pages = set(profile.get("priority_pages", []))
    priority_pages_only = bool(profile.get("priority_pages_only", False))
    doc_limit = int(profile.get("max_docs_per_pdf", max_docs_per_pdf))
    min_chunk_tokens = int(profile.get("min_chunk_tokens", 80))
    page_start_markers = profile.get("page_start_markers", {})
    short_marker_pages = set(profile.get("short_marker_pages", []))
    merge_page_ranges = [
        (int(start), int(end))
        for start, end in profile.get("merge_page_ranges", [])
    ]

    candidates: list[dict] = []
    pages_by_number = {
        int(page["page"]): str(page["text"])
        for page in pages
    }

    def prepared_page_text(page_number: int) -> str:
        page_text = pages_by_number.get(page_number, "")
        marker = page_start_markers.get(page_number)
        if isinstance(marker, str):
            page_text = trim_to_marker(page_text, marker)
        return page_text

    def add_candidate_chunks(
        text: str,
        page_start: int,
        page_end: int,
        min_tokens: int,
    ) -> None:
        if not text or looks_like_toc_page(text):
            return
        for chunk_index, chunk in enumerate(
            chunk_page_text(text, chunk_tokens, overlap, min_tokens),
            start=1,
        ):
            score = score_text(chunk, terms)
            if any(page in priority_pages for page in range(page_start, page_end + 1)):
                score += 1000
            if score < min_score:
                continue
            candidates.append(
                {
                    "score": score,
                    "page": page_start,
                    "page_end": page_end,
                    "chunk_index": chunk_index,
                    "text": chunk,
                }
            )

    merged_pages: set[int] = set()
    for start_page, end_page in merge_page_ranges:
        if priority_pages_only and not any(
            page in priority_pages for page in range(start_page, end_page + 1)
        ):
            continue
        merged_text = " ".join(
            prepared_page_text(page_number)
            for page_number in range(start_page, end_page + 1)
            if page_number in pages_by_number
        )
        add_candidate_chunks(merged_text, start_page, end_page, min_chunk_tokens)
        merged_pages.update(range(start_page, end_page + 1))

    for page in pages:
        page_number = int(page["page"])
        if page_number in merged_pages:
            continue
        if priority_pages_only and page_number not in priority_pages:
            continue
        page_text = prepared_page_text(page_number)
        page_min_chunk_tokens = 10 if page_number in short_marker_pages else min_chunk_tokens
        add_candidate_chunks(page_text, page_number, page_number, page_min_chunk_tokens)

    candidates.sort(
        key=lambda item: (-item["score"], item["page"], item["page_end"], item["chunk_index"])
    )
    selected = candidates[:doc_limit]
    selected.sort(key=lambda item: (item["page"], item["page_end"], item["chunk_index"]))

    source_id = slugify(pdf_path.stem)
    documents: list[dict] = []
    for local_index, chunk in enumerate(selected, start=1):
        page = int(chunk["page"])
        page_end = int(chunk["page_end"])
        doc_id = f"{source_id}_p{page:04d}_{local_index:03d}"
        documents.append(
            {
                "doc_id": doc_id,
                "title": title_from_chunk(chunk["text"], source_title, page, local_index),
                "url": f"{url}#page={page}",
                "source_file": pdf_path.name,
                "product_area": product_area,
                "page_start": page,
                "page_end": page_end,
                "text": chunk["text"],
            }
        )
    return documents


def build_corpus(
    source_urls_path: Path,
    pdf_dir: Path,
    text_cache_dir: Path,
    out_path: Path,
    min_score: int,
    max_docs_per_pdf: int,
    max_docs: int,
    chunk_tokens: int,
    overlap: int,
    refresh: bool = False,
) -> list[dict]:
    urls = source_urls(source_urls_path)
    if not urls:
        raise ValueError(f"No PDF URLs found in {source_urls_path}")

    documents: list[dict] = []
    counts_by_source: dict[str, int] = defaultdict(int)
    for url in urls:
        pdf_path = download_pdf(url, pdf_dir, refresh=refresh)
        pages = extract_pdf_pages(pdf_path, text_cache_dir, refresh=refresh)
        pdf_documents = build_chunks_for_pdf(
            url=url,
            pdf_path=pdf_path,
            pages=pages,
            min_score=min_score,
            max_docs_per_pdf=max_docs_per_pdf,
            chunk_tokens=chunk_tokens,
            overlap=overlap,
        )
        documents.extend(pdf_documents)
        counts_by_source[pdf_path.name] = len(pdf_documents)

    if len(documents) > max_docs:
        documents = documents[:max_docs]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as file:
        for document in documents:
            file.write(json.dumps(document, ensure_ascii=False) + "\n")

    print("Documents by source:")
    for source, count in sorted(counts_by_source.items()):
        print(f"  {source}: {count}")
    return documents


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build documents.jsonl from official Salesforce PDF sources."
    )
    parser.add_argument("--source-urls", type=Path, default=DEFAULT_SOURCE_URLS)
    parser.add_argument("--pdf-dir", type=Path, default=DEFAULT_PDF_DIR)
    parser.add_argument("--text-cache-dir", type=Path, default=DEFAULT_TEXT_CACHE_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--min-score", type=int, default=2)
    parser.add_argument("--max-docs-per-pdf", type=int, default=30)
    parser.add_argument("--max-docs", type=int, default=500)
    parser.add_argument("--chunk-tokens", type=int, default=CHUNK_TOKENS)
    parser.add_argument("--overlap", type=int, default=CHUNK_OVERLAP)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    documents = build_corpus(
        source_urls_path=args.source_urls,
        pdf_dir=args.pdf_dir,
        text_cache_dir=args.text_cache_dir,
        out_path=args.out,
        min_score=args.min_score,
        max_docs_per_pdf=args.max_docs_per_pdf,
        max_docs=args.max_docs,
        chunk_tokens=args.chunk_tokens,
        overlap=args.overlap,
        refresh=args.refresh,
    )
    print(f"Wrote {len(documents)} documents to {args.out}")
    if not 200 <= len(documents) <= 500:
        print("WARNING: document count is outside the assignment target of 200-500.")


if __name__ == "__main__":
    main()

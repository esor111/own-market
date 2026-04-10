"""
Helpers for extracting corporate-action rows from official summary PDFs.
"""
from io import BytesIO
import re
import ssl
import urllib.request


USER_AGENT = "Mozilla/5.0 (compatible; MarketGistBot/1.0)"
UNVERIFIED_SSL_CONTEXT = ssl._create_unverified_context()


def _clean_text(value):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _fetch_pdf_bytes(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45, context=UNVERIFIED_SSL_CONTEXT) as response:
        return response.read()


def _collect_bucket(words, x_min, x_max):
    items = [word for word in words if x_min <= float(word.get("x0", 0)) < x_max]
    items.sort(key=lambda word: (round(float(word.get("top", 0)), 1), float(word.get("x0", 0))))
    return _clean_text(" ".join(str(word.get("text") or "") for word in items))


def _extract_serial_rows(words):
    serials = [
        word
        for word in words
        if float(word.get("x0", 0)) < 30
        and float(word.get("top", 0)) > 95
        and re.fullmatch(r"\d{1,2}", str(word.get("text") or ""))
    ]
    serials.sort(key=lambda word: float(word.get("top", 0)))
    return serials


def extract_rights_summary_pdf_rows(pdf_url, publication_date=""):
    try:
        import pdfplumber
    except Exception:
        return {
            "rows": [],
            "notes": ["pdfplumber is unavailable; corporate-action PDF enrichment was skipped"],
        }

    try:
        pdf_bytes = _fetch_pdf_bytes(pdf_url)
    except Exception as exc:
        return {
            "rows": [],
            "notes": [f"failed to download source PDF: {exc!r}"],
        }

    rows = []
    notes = []

    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page_index, page in enumerate(pdf.pages):
                words = page.extract_words(use_text_flow=True) or []
                serials = _extract_serial_rows(words)
                if not serials:
                    continue

                for index, serial in enumerate(serials):
                    prev_top = float(serials[index - 1].get("top", 0)) if index > 0 else float(serial.get("top", 0)) - 12
                    next_top = (
                        float(serials[index + 1].get("top", 0))
                        if index + 1 < len(serials)
                        else float(serial.get("top", 0)) + 12
                    )
                    y_min = (prev_top + float(serial.get("top", 0))) / 2
                    y_max = (float(serial.get("top", 0)) + next_top) / 2
                    block = [
                        word
                        for word in words
                        if y_min <= float(word.get("top", 0)) < y_max
                    ]

                    company_name = _collect_bucket(block, 30, 118)
                    if not company_name or company_name.lower().startswith("total"):
                        continue

                    row = {
                        "serial_no": str(serial.get("text") or "").strip(),
                        "publication_date": str(publication_date or "").strip()[:10],
                        "company_name": company_name,
                        "sector": _collect_bucket(block, 118, 160),
                        "ratio": _collect_bucket(block, 160, 200),
                        "from_shares": _collect_bucket(block, 205, 250),
                        "to_shares": _collect_bucket(block, 250, 305),
                        "issue_share_count": _collect_bucket(block, 305, 360),
                        "issue_amount": _collect_bucket(block, 360, 415),
                        "issue_manager": _collect_bucket(block, 415, 478),
                        "approval_date_bs": _collect_bucket(block, 478, 520),
                        "source_pdf_url": pdf_url,
                        "page_number": page_index + 1,
                    }
                    rows.append(row)
    except Exception as exc:
        return {
            "rows": [],
            "notes": [f"failed to parse source PDF: {exc!r}"],
        }

    if not rows:
        notes.append("no company-level rows were extracted from the source PDF")

    return {
        "rows": rows,
        "notes": notes,
    }

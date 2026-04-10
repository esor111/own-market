"""
Audit official NRB macro sources before building a replay-safe macro adapter.

Usage:
    python nrb_macro_source_audit.py
"""
import json
import os
import re
from datetime import datetime

import requests

from config import VALIDATION_DIR


AUDIT_DIR = os.path.join(VALIDATION_DIR, "historical_context_backfills")
USER_AGENT = "market-gist-macro-audit/1.0"
TIMEOUT_SECONDS = 25

TARGET_FIELDS = {
    "interbank_rate": [
        "interbank",
        "weighted average interbank rate",
        "short term interest rates",
    ],
    "remittance": [
        "remittance",
        "worker's remittance",
    ],
    "private_credit_growth": [
        "private sector credit",
        "credit growth",
    ],
    "monetary_policy": [
        "monetary policy",
        "quarter review",
        "midterm review",
    ],
}

SOURCES = [
    {
        "name": "nrb_homepage_indicators",
        "url": "https://www.nrb.org.np/",
        "intended_use": "spot-check current indicator availability and wording",
        "expected_fields": ["interbank_rate", "remittance", "private_credit_growth", "monetary_policy"],
        "granularity": "current snapshot",
    },
    {
        "name": "nrb_monthly_statistics_archive",
        "url": "https://www.nrb.org.np/category/monthly-statistics/",
        "intended_use": "best candidate for replay-safe monthly macro numeric extraction",
        "expected_fields": ["interbank_rate", "remittance", "private_credit_growth"],
        "granularity": "monthly",
    },
    {
        "name": "nrb_monetary_policy_english_archive",
        "url": "https://www.nrb.org.np/category/monetary-policy/monetary-policy-english/",
        "intended_use": "policy regime dates and policy-review tagging",
        "expected_fields": ["monetary_policy"],
        "granularity": "policy review windows",
    },
    {
        "name": "nrb_quarterly_economic_bulletin_archive",
        "url": "https://www.nrb.org.np/category/economic-bulletin/quarterly-economic-bulletin/",
        "intended_use": "quarterly macro fallback and cross-check source",
        "expected_fields": ["interbank_rate", "remittance", "private_credit_growth"],
        "granularity": "quarterly",
    },
]


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _clean_html_text(content):
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", content)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _fetch_text(url):
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "html" in content_type:
        text = _clean_html_text(response.text)
    else:
        text = response.text
    return response, content_type, text


def _keyword_hits(text, expected_fields):
    lowered = text.lower()
    hits = {}
    for field_name in expected_fields:
        matches = []
        for keyword in TARGET_FIELDS.get(field_name, []):
            if keyword.lower() in lowered:
                matches.append(keyword)
        hits[field_name] = matches
    return hits


def _recommendation(source_name, accessible, coverage_ratio):
    if not accessible:
        return "blocked_or_unreachable"
    if source_name == "nrb_monthly_statistics_archive":
        return "build_first_monthly_numeric_adapter" if coverage_ratio >= 0.34 else "needs_manual_archive_inspection"
    if source_name == "nrb_monetary_policy_english_archive":
        return "use_for_policy_regime_labels"
    if source_name == "nrb_quarterly_economic_bulletin_archive":
        return "use_as_quarterly_macro_fallback"
    if source_name == "nrb_homepage_indicators":
        return "use_for_current_indicator_wording_only"
    return "manual_review"


def audit_sources():
    rows = []
    for source in SOURCES:
        result = {
            "name": source["name"],
            "url": source["url"],
            "intended_use": source["intended_use"],
            "expected_fields": source["expected_fields"],
            "granularity": source["granularity"],
            "accessible": False,
            "status_code": None,
            "content_type": None,
            "final_url": None,
            "keyword_hits": {},
            "field_hit_count": 0,
            "field_coverage_ratio": 0.0,
            "recommendation": None,
            "error": None,
        }
        try:
            response, content_type, text = _fetch_text(source["url"])
            hits = _keyword_hits(text, source["expected_fields"])
            field_hit_count = sum(1 for value in hits.values() if value)
            coverage_ratio = round(field_hit_count / len(source["expected_fields"]), 4) if source["expected_fields"] else 0.0
            result.update({
                "accessible": True,
                "status_code": response.status_code,
                "content_type": content_type,
                "final_url": response.url,
                "keyword_hits": hits,
                "field_hit_count": field_hit_count,
                "field_coverage_ratio": coverage_ratio,
            })
            result["recommendation"] = _recommendation(source["name"], True, coverage_ratio)
        except Exception as exc:
            result["error"] = str(exc)
            result["recommendation"] = _recommendation(source["name"], False, 0.0)
        rows.append(result)

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "purpose": "audit official NRB macro sources before writing a replay-safe macro adapter",
        "sources": rows,
        "recommended_build_order": [
            "nrb_monthly_statistics_archive",
            "nrb_monetary_policy_english_archive",
            "nrb_quarterly_economic_bulletin_archive",
            "nrb_homepage_indicators",
        ],
        "next_step": "build nrb macro adapter only after verifying the monthly archive is structured enough for replay-safe numeric extraction",
    }
    return summary


def render_markdown(summary):
    lines = [
        "# NRB Macro Source Audit",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- purpose: `{summary['purpose']}`",
        "",
        "## Source Results",
        "",
    ]
    for item in summary.get("sources", []):
        lines.extend([
            f"### {item['name']}",
            "",
            f"- url: `{item['url']}`",
            f"- intended_use: `{item['intended_use']}`",
            f"- granularity: `{item['granularity']}`",
            f"- accessible: `{item['accessible']}`",
            f"- status_code: `{item['status_code']}`",
            f"- content_type: `{item['content_type']}`",
            f"- field_hit_count: `{item['field_hit_count']}`",
            f"- field_coverage_ratio: `{item['field_coverage_ratio']}`",
            f"- recommendation: `{item['recommendation']}`",
        ])
        if item.get("error"):
            lines.append(f"- error: `{item['error']}`")
        if item.get("keyword_hits"):
            lines.append("- keyword_hits:")
            for field_name, hits in item["keyword_hits"].items():
                lines.append(f"  - `{field_name}`: `{hits}`")
        lines.append("")

    lines.extend([
        "## Recommended Build Order",
        "",
    ])
    for name in summary.get("recommended_build_order", []):
        lines.append(f"- `{name}`")
    lines.extend([
        "",
        "## Next Step",
        "",
        f"- {summary.get('next_step')}",
        "",
    ])
    return "\n".join(lines)


def main():
    summary = audit_sources()
    dated_json_path = os.path.join(
        AUDIT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__nrb_macro_source_audit_v1.json",
    )
    latest_json_path = os.path.join(AUDIT_DIR, "latest__nrb_macro_source_audit_v1.json")
    dated_md_path = os.path.join(
        AUDIT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__nrb_macro_source_audit_v1.md",
    )
    latest_md_path = os.path.join(AUDIT_DIR, "latest__nrb_macro_source_audit_v1.md")
    markdown = render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    print(json.dumps({
        "dated_json_path": dated_json_path,
        "latest_json_path": latest_json_path,
        "dated_md_path": dated_md_path,
        "latest_md_path": latest_md_path,
        "source_count": len(summary["sources"]),
    }, indent=2))


if __name__ == "__main__":
    main()

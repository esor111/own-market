"""
Discover replay-safe NRB current macro report assets by fiscal year and month window.

Usage:
    python nrb_current_macro_discovery.py 2081-82
"""
import json
import os
import sys
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import VALIDATION_DIR


DISCOVERY_DIR = os.path.join(VALIDATION_DIR, "historical_context_backfills")
USER_AGENT = "market-gist-macro-discovery/1.0"
TIMEOUT_SECONDS = 30
BASE_URL = "https://www.nrb.org.np"
CURRENT_MACRO_CATEGORY = "https://www.nrb.org.np/category/current-macroeconomic-situation/?department=red"


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _fetch(url):
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT_SECONDS,
        allow_redirects=True,
    )
    response.raise_for_status()
    return response


def _extract_subcategory_links(fy_token):
    url = f"{CURRENT_MACRO_CATEGORY}&fy={fy_token}"
    response = _fetch(url)
    soup = BeautifulSoup(response.text, "html.parser")
    records = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"])
        text = " ".join(a.get_text(" ", strip=True).split())
        if f"fy={fy_token}" not in href or "subcategory=" not in href:
            continue
        subcategory = href.split("subcategory=", 1)[1].split("&", 1)[0]
        key = (subcategory, href)
        if key in seen:
            continue
        seen.add(key)
        records.append({
            "subcategory": subcategory,
            "label": text,
            "url": href,
        })
    return url, records


def _extract_post_links(subcategory_url):
    response = _fetch(subcategory_url)
    soup = BeautifulSoup(response.text, "html.parser")
    posts = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(subcategory_url, a["href"])
        text = " ".join(a.get_text(" ", strip=True).split())
        if not href.startswith(f"{BASE_URL}/red/"):
            continue
        if "current-macroeconomic" not in href:
            continue
        key = (text, href)
        if key in seen:
            continue
        seen.add(key)
        posts.append({
            "title": text,
            "url": href,
        })
    return posts


def _classify_post_type(title):
    lowered = title.lower()
    if "tables" in lowered:
        return "tables"
    if "english" in lowered:
        return "english_report"
    if "nepali" in lowered:
        return "nepali_report"
    return "other"


def _resolve_asset_metadata(url):
    response = _fetch(url)
    content_type = (response.headers.get("content-type") or "").lower()
    final_url = response.url
    asset_type = "html"
    if "spreadsheetml" in content_type or final_url.lower().endswith((".xlsx", ".xls")):
        asset_type = "xlsx"
    elif "pdf" in content_type or final_url.lower().endswith(".pdf"):
        asset_type = "pdf"
    return {
        "final_url": final_url,
        "content_type": content_type,
        "asset_type": asset_type,
        "status_code": response.status_code,
    }


def build_current_macro_discovery(fy_token):
    fy_url, subcategories = _extract_subcategory_links(fy_token)
    results = []
    for subcategory in subcategories:
        post_links = _extract_post_links(subcategory["url"])
        post_records = []
        for post in post_links:
            resolved = _resolve_asset_metadata(post["url"])
            post_records.append({
                "title": post["title"],
                "post_url": post["url"],
                "post_type": _classify_post_type(post["title"]),
                **resolved,
            })
        results.append({
            **subcategory,
            "post_count": len(post_records),
            "posts": post_records,
        })

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source": "nrb_current_macro_archive",
        "fy_token": fy_token,
        "fy_url": fy_url,
        "subcategory_count": len(results),
        "subcategories": results,
        "notes": [
            "this is a discovery manifest, not a parsed macro dataset",
            "the tables posts currently resolve directly to xlsx assets",
            "the english and nepali report posts currently resolve directly to pdf assets",
            "this manifest is intended to make the later replay-safe macro parser deterministic",
        ],
    }
    return summary


def render_markdown(summary):
    lines = [
        "# NRB Current Macro Discovery",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- fy_token: `{summary['fy_token']}`",
        f"- fy_url: `{summary['fy_url']}`",
        f"- subcategory_count: `{summary['subcategory_count']}`",
        "",
        "## Notes",
        "",
    ]
    for note in summary.get("notes", []):
        lines.append(f"- {note}")

    lines.extend(["", "## Subcategories", ""])
    for item in summary.get("subcategories", []):
        lines.append(f"### {item['label']}")
        lines.append("")
        lines.append(f"- subcategory: `{item['subcategory']}`")
        lines.append(f"- url: `{item['url']}`")
        lines.append(f"- post_count: `{item['post_count']}`")
        for post in item.get("posts", []):
            lines.append(
                f"- `{post['post_type']}`: `{post['final_url']}` "
                f"(content_type `{post['content_type']}`)"
            )
        lines.append("")
    return "\n".join(lines)


def main():
    fy_token = sys.argv[1] if len(sys.argv) >= 2 else "2081-82"
    summary = build_current_macro_discovery(fy_token)
    safe_token = fy_token.replace("/", "_")
    dated_json_path = os.path.join(
        DISCOVERY_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__nrb_current_macro_discovery__{safe_token}_v1.json",
    )
    latest_json_path = os.path.join(
        DISCOVERY_DIR,
        f"latest__nrb_current_macro_discovery__{safe_token}_v1.json",
    )
    dated_md_path = os.path.join(
        DISCOVERY_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__nrb_current_macro_discovery__{safe_token}_v1.md",
    )
    latest_md_path = os.path.join(
        DISCOVERY_DIR,
        f"latest__nrb_current_macro_discovery__{safe_token}_v1.md",
    )
    markdown = render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    print(json.dumps({
        "fy_token": fy_token,
        "subcategory_count": summary["subcategory_count"],
        "dated_json_path": dated_json_path,
        "latest_json_path": latest_json_path,
        "dated_md_path": dated_md_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()

"""
Official event extraction helpers.
"""
import html
import re
import urllib.request
from datetime import date, datetime


class OfficialEventExtractor:
    BASE_URL = "https://sebon.gov.np/prospectus"
    PAGE_LIMIT = 3
    USER_AGENT = "Mozilla/5.0 (compatible; MarketGistBot/1.0)"
    STOPWORDS = {
        "limited", "ltd", "bank", "hydropower", "development", "company",
        "project", "power", "finance", "fund", "mutual", "open", "ended",
        "commercial", "industries", "industry", "holdings", "nepal", "public"
    }

    def _fetch(self, url):
        request = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT})
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8", errors="ignore")

    def _clean_text(self, value):
        text = re.sub(r"<[^>]+>", " ", value or "")
        text = html.unescape(text)
        return re.sub(r"\s+", " ", text).strip()

    def _normalize_tokens(self, value):
        cleaned = re.sub(r"[^a-z0-9]+", " ", (value or "").lower())
        tokens = [token for token in cleaned.split() if len(token) >= 3 and token not in self.STOPWORDS]
        return tokens

    def _row_to_record(self, row_match):
        title, event_date, _, pdf_url = row_match
        return {
            "title": self._clean_text(title),
            "event_date": self._clean_text(event_date),
            "pdf_url": self._clean_text(pdf_url)
        }

    def _extract_rows(self, html_text):
        pattern = re.compile(
            r"<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td><a href=\"(.*?)\"",
            re.IGNORECASE | re.DOTALL
        )
        return [self._row_to_record(match) for match in pattern.findall(html_text)]

    def _classify_event_type(self, title):
        lowered = title.lower()
        if "right" in lowered:
            return "rights_issue", "mixed", 45
        if "bonus" in lowered:
            return "bonus_share", "positive", 45
        if "book closure" in lowered:
            return "book_closure", "neutral", 21
        if "debenture" in lowered:
            return "debenture_offer", "neutral", 60
        if "general public" in lowered or "locals" in lowered or "foreign employment" in lowered:
            return "prospectus_offer", "neutral", 60
        return "prospectus_notice", "neutral", 30

    def _days_since(self, event_date, run_date):
        try:
            event_day = datetime.strptime(event_date, "%Y-%m-%d").date()
            run_day = datetime.strptime(run_date, "%Y-%m-%d").date()
        except ValueError:
            return None
        return (run_day - event_day).days

    def find_recent_official_event(self, symbol, company_name, run_date):
        symbol_tokens = self._normalize_tokens(symbol)
        company_tokens = self._normalize_tokens(company_name)
        target_tokens = [token for token in company_tokens if token not in symbol_tokens] + symbol_tokens
        if not target_tokens:
            target_tokens = company_tokens or symbol_tokens

        checked_pages = []
        candidates = []
        for page in range(1, self.PAGE_LIMIT + 1):
            url = self.BASE_URL if page == 1 else f"{self.BASE_URL}?page={page}"
            html_text = self._fetch(url)
            checked_pages.append(url)
            for row in self._extract_rows(html_text):
                row_tokens = self._normalize_tokens(row["title"])
                overlap = [token for token in target_tokens if token in row_tokens]
                if overlap:
                    row["matched_tokens"] = overlap
                    row["match_score"] = len(overlap)
                    candidates.append(row)

        candidates.sort(key=lambda item: (-item["match_score"], item["event_date"]), reverse=False)
        if not candidates:
            return {
                "event_found": False,
                "source": "sebon_prospectus",
                "event_date": "",
                "event_type": "no_recent_official_event_match",
                "sentiment": "neutral",
                "impact_window_days": 0,
                "relevance_now": "inactive",
                "confidence_source": "page_text",
                "details": {
                    "company_name": company_name,
                    "symbol": symbol,
                    "pages_checked": checked_pages
                },
                "source_refs": checked_pages
            }

        best = candidates[-1]
        event_type, sentiment, impact_window_days = self._classify_event_type(best["title"])
        days_since_event = self._days_since(best["event_date"], run_date)
        relevance_now = "active_window"
        if days_since_event is not None and days_since_event > impact_window_days:
            relevance_now = "expired"

        return {
            "event_found": True,
            "source": "sebon_prospectus",
            "event_date": best["event_date"],
            "event_type": event_type,
            "sentiment": sentiment,
            "impact_window_days": impact_window_days,
            "relevance_now": relevance_now,
            "confidence_source": "page_text",
            "details": {
                "matched_title": best["title"],
                "matched_tokens": best["matched_tokens"],
                "pdf_url": best["pdf_url"],
                "days_since_event": days_since_event,
                "company_name": company_name
            },
            "source_refs": checked_pages + ([best["pdf_url"]] if best.get("pdf_url") else [])
        }

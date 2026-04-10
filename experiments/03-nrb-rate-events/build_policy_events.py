"""
Build a hand-curated NRB policy event table from official NRB archive dates and
official rate-series change points.

Usage:
    python experiments/03-nrb-rate-events/build_policy_events.py
"""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

import requests


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
AJAX_URL = "https://www.nrb.org.np/wp-admin/admin-ajax.php"

MANUAL_EVENTS = [
    {
        "event_date": "2022-07-22",
        "event_type": "monetary_policy_announcement",
        "event_label": "Monetary Policy 2079-80 (Full Text, Nepali)",
        "direction": "announcement",
        "detail": "Annual monetary policy announcement",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-in-nepali-2079-80-full-text/",
    },
    {
        "event_date": "2022-11-27",
        "event_type": "monetary_policy_q1_review",
        "event_label": "Monetary Policy 2079-80 1st Quarter Review",
        "direction": "review",
        "detail": "First quarter monetary policy review",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-2079-80-1st-quarter-review/",
    },
    {
        "event_date": "2023-02-10",
        "event_type": "monetary_policy_midterm_review",
        "event_label": "Monetary Policy 2079-80 Mid Term Review",
        "direction": "review",
        "detail": "Midterm monetary policy review",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-2079-80-mid-term-review/",
    },
    {
        "event_date": "2023-05-12",
        "event_type": "monetary_policy_q3_review",
        "event_label": "Monetary Policy 2079-80 3rd Quarter Review",
        "direction": "review",
        "detail": "Third quarter monetary policy review",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-2079-80-3rd-quarter-review/",
    },
    {
        "event_date": "2023-07-23",
        "event_type": "monetary_policy_announcement",
        "event_label": "Monetary Policy 2080-81 (Full Text, Nepali)",
        "direction": "announcement",
        "detail": "Annual monetary policy announcement",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-in-nepali-2080-81-full-text/",
    },
    {
        "event_date": "2023-12-08",
        "event_type": "monetary_policy_q1_review",
        "event_label": "Monetary Policy 2080-81 1st Quarter Review",
        "direction": "review",
        "detail": "First quarter monetary policy review",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-2080-81-1st-quarter-review/",
    },
    {
        "event_date": "2024-02-12",
        "event_type": "monetary_policy_midterm_review",
        "event_label": "Monetary Policy 2080-81 Midterm Review",
        "direction": "review",
        "detail": "Midterm monetary policy review",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-2080-81-midterm-review/",
    },
    {
        "event_date": "2024-05-17",
        "event_type": "monetary_policy_q3_review",
        "event_label": "Monetary Policy 2080-81 3rd Quarter Review",
        "direction": "review",
        "detail": "Third quarter monetary policy review",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-2080-81-3rd-quarter-review/",
    },
    {
        "event_date": "2024-07-26",
        "event_type": "monetary_policy_announcement",
        "event_label": "Monetary Policy 2081-82 (Full Text, Nepali)",
        "direction": "announcement",
        "detail": "Annual monetary policy announcement",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-in-nepali-2081-82-full-text/",
    },
    {
        "event_date": "2024-11-29",
        "event_type": "monetary_policy_q1_review",
        "event_label": "Monetary Policy 2081-82 1st Quarter Review",
        "direction": "review",
        "detail": "First quarter monetary policy review",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-2081-82-1st-quarter-review/",
    },
    {
        "event_date": "2025-02-25",
        "event_type": "monetary_policy_midterm_review",
        "event_label": "Monetary Policy 2081-82 Midterm Review",
        "direction": "review",
        "detail": "Midterm monetary policy review",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-2081-82-midterm-review/",
    },
    {
        "event_date": "2025-05-25",
        "event_type": "monetary_policy_q3_review",
        "event_label": "Monetary Policy 2081-82 3rd Quarter Review",
        "direction": "review",
        "detail": "Third quarter monetary policy review",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-2081-82-3rd-quarter-review/",
    },
    {
        "event_date": "2025-07-11",
        "event_type": "monetary_policy_announcement",
        "event_label": "Monetary Policy 2082-83 (Full Text, Nepali)",
        "direction": "announcement",
        "detail": "Annual monetary policy announcement",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-in-nepali-2082-83-full-text/",
    },
    {
        "event_date": "2025-12-01",
        "event_type": "monetary_policy_q1_review",
        "event_label": "Monetary Policy 2082-83 1st Quarter Review",
        "direction": "review",
        "detail": "First quarter monetary policy review",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-2082-83-1st-quarter-review/",
    },
    {
        "event_date": "2026-02-24",
        "event_type": "monetary_policy_midterm_review",
        "event_label": "Monetary Policy 2082-83 Midterm Review",
        "direction": "review",
        "detail": "Midterm monetary policy review",
        "source": "https://www.nrb.org.np/ofg/monetary-policy-2081-82-midterm-review-2/",
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    rows = list(MANUAL_EVENTS)
    rows.extend(fetch_policy_rate_change_events("99", "policy_rate_change", "Policy Rate (Overnight Repo)"))
    rows.extend(fetch_policy_rate_change_events("80", "bank_rate_change", "Bank Rate"))

    rows.sort(key=lambda row: (row["event_date"], row["event_type"], row["event_label"]))
    output_path = DATA_DIR / "policy_events.csv"
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["event_date", "event_type", "event_label", "direction", "detail", "source"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} policy events to {output_path}")


def fetch_policy_rate_change_events(rate_id: str, event_type: str, series_name: str) -> list[dict]:
    payload = {
        "action": "get_rates",
        "date_from": "2022-01-01",
        "date_to": "2025-12-31",
        "rate_type": "POLICY_RATE",
        "rate_id": rate_id,
    }
    response = requests.post(AJAX_URL, data=payload, timeout=60)
    response.raise_for_status()
    body = response.json()
    if not body.get("success"):
        raise RuntimeError(f"NRB AJAX failed for policy series rate_id={rate_id}: {body}")

    data = body.get("data") or {}
    labels = data.get("label") or []
    values = data.get("values") or []
    if len(labels) != len(values):
        raise RuntimeError(
            f"Length mismatch for policy series rate_id={rate_id}: {len(labels)} labels vs {len(values)} values"
        )

    events: list[dict] = []
    previous_value: float | None = None
    for label, raw_value in zip(labels, values):
        current_value = float(raw_value)
        if previous_value is None:
            previous_value = current_value
            continue
        if current_value == previous_value:
            continue
        event_date = datetime.strptime(label, "%B %d, %Y").date().isoformat()
        direction = "tightening" if current_value > previous_value else "easing"
        events.append(
            {
                "event_date": event_date,
                "event_type": event_type,
                "event_label": f"{series_name} changed",
                "direction": direction,
                "detail": f"{current_value:.2f}% from {previous_value:.2f}%",
                "source": AJAX_URL,
            }
        )
        previous_value = current_value
    return events


if __name__ == "__main__":
    main()

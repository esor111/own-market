import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python render_volume_chart.py <full_json_path>")

    full_json_path = Path(sys.argv[1]).resolve()
    data = json.loads(full_json_path.read_text(encoding="utf-8"))
    daily = data.get("daily", [])
    if not daily:
        raise SystemExit(f"No daily rows found in {full_json_path}")

    labels = [row["date_np"][5:] for row in daily]
    volumes = [row["volume"] for row in daily]
    closes = [row["close"] for row in daily]
    symbol = data.get("symbol", "SYMBOL")

    fig, ax1 = plt.subplots(figsize=(13, 6), dpi=160)
    ax1.bar(labels, volumes, color="#2f80ed", alpha=0.88)
    ax1.set_ylabel("Volume (shares)")
    ax1.tick_params(axis="x", rotation=55)
    ax1.grid(axis="y", alpha=0.25)

    ax2 = ax1.twinx()
    ax2.plot(labels, closes, color="#c0392b", marker="o", linewidth=1.8)
    ax2.set_ylabel("Close price")

    fig.suptitle(f"{symbol} Daily Volume and Close (fresh Nepse Alpha scrape)")
    fig.text(
        0.01,
        0.01,
        (
            f"Scraped: {data.get('scraped_at_np')} | "
            f"Range: {data.get('cutoff_datetime_np')} to {data.get('latest_datetime_np')} | "
            f"Total volume: {data.get('total_volume', 0):,}"
        ),
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))

    output_path = full_json_path.with_name(f"{symbol.lower()}_volume_daily_chart.png")
    fig.savefig(output_path)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

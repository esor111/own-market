from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

import pandas as pd

from stats import describe_returns


DEFAULT_WINDOWS = {
    "pre_-10_-1": (-10, -1),
    "reaction_0_1": (0, 1),
    "drift_2_10": (2, 10),
}


def run_event_study(
    prices: pd.DataFrame,
    events: pd.DataFrame,
    event_date_col: str = "event_date",
    windows: dict[str, tuple[int, int]] | None = None,
    price_col: str = "close",
    anchor_mode: str = "on_or_after",
    max_forward_gap_days: int | None = 10,
) -> pd.DataFrame:
    price_frame = prepare_price_frame(prices, price_col=price_col)
    if price_frame.empty or events.empty:
        return pd.DataFrame()

    study_windows = windows or DEFAULT_WINDOWS
    event_frame = events.copy()
    event_frame[event_date_col] = pd.to_datetime(event_frame[event_date_col], errors="coerce")
    event_frame = event_frame.dropna(subset=[event_date_col]).reset_index(drop=True)
    if event_frame.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    passthrough_cols = [col for col in event_frame.columns if col != event_date_col]

    closes = price_frame[price_col].tolist()
    dates = price_frame["date"].tolist()

    for event in event_frame.to_dict("records"):
        event_date = event[event_date_col]
        anchor_idx = resolve_anchor_index(
            dates,
            event_date,
            mode=anchor_mode,
            max_forward_gap_days=max_forward_gap_days,
        )
        if anchor_idx is None:
            continue

        for window_label, (start_offset, end_offset) in study_windows.items():
            start_idx = anchor_idx + start_offset
            end_idx = anchor_idx + end_offset
            if start_idx < 0 or end_idx >= len(price_frame) or start_idx > end_idx:
                continue

            start_price = closes[start_idx]
            end_price = closes[end_idx]
            if start_price in (None, 0) or end_price is None:
                continue

            return_pct = ((end_price / start_price) - 1) * 100.0
            row = {
                "event_date": event_date.date().isoformat(),
                "anchor_date": dates[anchor_idx].date().isoformat(),
                "window_label": window_label,
                "start_offset": start_offset,
                "end_offset": end_offset,
                "start_date": dates[start_idx].date().isoformat(),
                "end_date": dates[end_idx].date().isoformat(),
                "start_price": start_price,
                "end_price": end_price,
                "return_pct": return_pct,
            }
            for column in passthrough_cols:
                row[column] = event[column]
            rows.append(row)

    return pd.DataFrame(rows)


def rolling_baseline_returns(
    prices: pd.DataFrame,
    windows: dict[str, tuple[int, int]] | None = None,
    price_col: str = "close",
) -> pd.DataFrame:
    price_frame = prepare_price_frame(prices, price_col=price_col)
    if price_frame.empty:
        return pd.DataFrame()

    study_windows = windows or DEFAULT_WINDOWS
    closes = price_frame[price_col].tolist()
    dates = price_frame["date"].tolist()
    rows: list[dict] = []

    for anchor_idx in range(len(price_frame)):
        for window_label, (start_offset, end_offset) in study_windows.items():
            start_idx = anchor_idx + start_offset
            end_idx = anchor_idx + end_offset
            if start_idx < 0 or end_idx >= len(price_frame) or start_idx > end_idx:
                continue

            start_price = closes[start_idx]
            end_price = closes[end_idx]
            if start_price in (None, 0) or end_price is None:
                continue

            rows.append(
                {
                    "anchor_date": dates[anchor_idx].date().isoformat(),
                    "window_label": window_label,
                    "start_offset": start_offset,
                    "end_offset": end_offset,
                    "start_date": dates[start_idx].date().isoformat(),
                    "end_date": dates[end_idx].date().isoformat(),
                    "return_pct": ((end_price / start_price) - 1) * 100.0,
                }
            )

    return pd.DataFrame(rows)


def summarize_event_returns(
    returns_frame: pd.DataFrame,
    group_cols: list[str] | None = None,
    positive: bool = True,
) -> pd.DataFrame:
    if returns_frame.empty:
        return pd.DataFrame()

    groups = group_cols or ["window_label"]
    rows: list[dict] = []

    grouped = returns_frame.groupby(groups, dropna=False)
    for keys, group in grouped:
        if not isinstance(keys, tuple):
            keys = (keys,)
        summary = describe_returns(group["return_pct"], positive=positive)
        row = {column: value for column, value in zip(groups, keys)}
        row.update(summary)
        rows.append(row)

    return pd.DataFrame(rows).sort_values(groups).reset_index(drop=True)


def prepare_price_frame(prices: pd.DataFrame, price_col: str = "close") -> pd.DataFrame:
    if prices.empty:
        return pd.DataFrame(columns=["date", price_col])
    frame = prices.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame = frame.dropna(subset=["date", price_col]).sort_values("date").reset_index(drop=True)
    return frame


def resolve_anchor_index(
    trading_dates: Iterable[pd.Timestamp],
    event_date: str | date | datetime | pd.Timestamp,
    mode: str = "on_or_after",
    max_forward_gap_days: int | None = 10,
) -> int | None:
    target_date = pd.Timestamp(event_date).normalize()
    date_list = list(trading_dates)

    if mode == "exact":
        for idx, trading_date in enumerate(date_list):
            if trading_date.normalize() == target_date:
                return idx
        return None

    if mode == "on_or_before":
        for idx in range(len(date_list) - 1, -1, -1):
            if date_list[idx].normalize() <= target_date:
                return idx
        return None

    for idx, trading_date in enumerate(date_list):
        if trading_date.normalize() >= target_date:
            if max_forward_gap_days is not None:
                gap_days = (trading_date.normalize() - target_date).days
                if gap_days > max_forward_gap_days:
                    return None
            return idx
    return None

from __future__ import annotations

import math
import statistics
from typing import Iterable


def clean_numeric(values: Iterable[float | int | None]) -> list[float]:
    cleaned: list[float] = []
    for value in values:
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if math.isnan(numeric):
            continue
        cleaned.append(numeric)
    return cleaned


def mean_return(values: Iterable[float | int | None]) -> float | None:
    cleaned = clean_numeric(values)
    return statistics.fmean(cleaned) if cleaned else None


def median_return(values: Iterable[float | int | None]) -> float | None:
    cleaned = clean_numeric(values)
    return statistics.median(cleaned) if cleaned else None


def hit_rate(
    values: Iterable[float | int | None],
    positive: bool = True,
    neutral_value: float = 0.0,
) -> tuple[int, int, float | None]:
    cleaned = clean_numeric(values)
    if not cleaned:
        return 0, 0, None

    if positive:
        successes = sum(1 for value in cleaned if value > neutral_value)
    else:
        successes = sum(1 for value in cleaned if value < neutral_value)
    total = len(cleaned)
    return successes, total, successes / total


def wilson_interval(
    successes: int,
    total: int,
    confidence: float = 0.95,
) -> tuple[float | None, float | None]:
    if total <= 0:
        return None, None

    z = _z_for_confidence(confidence)
    phat = successes / total
    denominator = 1 + (z * z / total)
    centre = phat + (z * z / (2 * total))
    margin = z * math.sqrt((phat * (1 - phat) / total) + (z * z / (4 * total * total)))
    return (centre - margin) / denominator, (centre + margin) / denominator


def one_sample_t_test(
    values: Iterable[float | int | None],
    null_mean: float = 0.0,
) -> tuple[float | None, float | None]:
    cleaned = clean_numeric(values)
    sample_size = len(cleaned)
    if sample_size < 2:
        return None, None

    sample_mean = statistics.fmean(cleaned)
    sample_stdev = statistics.stdev(cleaned)
    if sample_stdev == 0:
        return None, 0.0 if sample_mean == null_mean else None

    t_stat = (sample_mean - null_mean) / (sample_stdev / math.sqrt(sample_size))
    p_value = 2 * (1 - _normal_cdf(abs(t_stat)))
    return t_stat, p_value


def describe_returns(
    values: Iterable[float | int | None],
    positive: bool = True,
) -> dict:
    cleaned = clean_numeric(values)
    hits, total, rate = hit_rate(cleaned, positive=positive)
    ci_low, ci_high = wilson_interval(hits, total)
    t_stat, p_value = one_sample_t_test(cleaned)
    return {
        "count": total,
        "mean_return": mean_return(cleaned),
        "median_return": median_return(cleaned),
        "hit_count": hits,
        "hit_rate": rate,
        "hit_rate_ci_low": ci_low,
        "hit_rate_ci_high": ci_high,
        "t_stat": t_stat,
        "p_value": p_value,
    }


def _normal_cdf(value: float) -> float:
    return 0.5 * (1 + math.erf(value / math.sqrt(2)))


def _z_for_confidence(confidence: float) -> float:
    if confidence >= 0.99:
        return 2.576
    if confidence >= 0.95:
        return 1.96
    if confidence >= 0.90:
        return 1.645
    return 1.96

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import floor

@dataclass(frozen=True)
class ForecastPoint:
    year_month: str  # YYYY-MM
    predicted_visits: int
    method: str

def seasonal_naive_forecast(monthly_counts: list[tuple[str, int]], months_ahead: int = 3) -> list[ForecastPoint]:
    """Simple forecasting without pandas.

    Strategy:
    - If at least 12 months exist: predict each future month as the value of the same month last year (seasonal naive).
    - Else: use the mean of last 3 months (rounded).
    """
    if not monthly_counts or months_ahead <= 0:
        return []

    # monthly_counts expected sorted by ym asc (YYYY-MM)
    last_ym = monthly_counts[-1][0]
    last_year = int(last_ym[:4])
    last_month = int(last_ym[5:7])

    counts_map = {ym: c for ym, c in monthly_counts}

    def next_ym(y: int, m: int):
        m += 1
        if m == 13:
            y += 1
            m = 1
        return y, m

    forecasts: list[ForecastPoint] = []
    has_12 = len(monthly_counts) >= 12

    # rolling average base if needed
    last3 = [c for _, c in monthly_counts[-3:]]
    avg3 = sum(last3) / len(last3)

    y, m = last_year, last_month
    for _ in range(months_ahead):
        y, m = next_ym(y, m)
        ym = f"{y:04d}-{m:02d}"

        if has_12:
            prev = f"{y-1:04d}-{m:02d}"
            if prev in counts_map:
                pred = counts_map[prev]
                method = "seasonal_naive"
            else:
                pred = int(floor(avg3 + 0.5))
                method = "avg_last3_fallback"
        else:
            pred = int(floor(avg3 + 0.5))
            method = "avg_last3"

        forecasts.append(ForecastPoint(year_month=ym, predicted_visits=pred, method=method))

    return forecasts

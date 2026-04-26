"""
Acceptance criteria:
- _linear_trend_for_position returns Growing / Declining / Stable / Insufficient data
  for synthetically shaped data matching those patterns.
- forecast is always >= 0 regardless of slope direction.
- r2 is in [0, 1].
- add_trend_forecast produces the required columns with correct dtypes and no NaN
  in slope/r2/label.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data.processor import (
    MIN_TREND_WEEKS,
    R2_THRESHOLD,
    SLOPE_THRESHOLD,
    _linear_trend_for_position,
    add_trend_forecast,
)


def _make_dates(n_weeks: int, weekly_count_fn) -> pd.Series:
    rng = np.random.default_rng(42)
    base = pd.Timestamp("2024-01-01")
    dates: list[pd.Timestamp] = []
    for week in range(n_weeks):
        count = max(0, int(weekly_count_fn(week) + rng.integers(-1, 2)))
        for _ in range(count):
            dates.append(base + pd.Timedelta(days=week * 7 + int(rng.integers(0, 7))))
    return pd.to_datetime(dates)


class TestLinearTrendForPosition:
    def test_growing_data_labelled_growing(self):
        dates = _make_dates(20, lambda w: 10 + w * 3)
        result = _linear_trend_for_position(
            pd.Series(dates),
            forecast_weeks=8,
            min_weeks=MIN_TREND_WEEKS,
            r2_threshold=R2_THRESHOLD,
            slope_threshold=SLOPE_THRESHOLD,
        )
        assert result["trend_label"] == "Growing"
        assert result["slope"] > 0
        assert result["r2"] >= R2_THRESHOLD

    def test_declining_data_labelled_declining(self):
        dates = _make_dates(20, lambda w: max(0, 60 - w * 2))
        result = _linear_trend_for_position(
            pd.Series(dates),
            forecast_weeks=8,
            min_weeks=MIN_TREND_WEEKS,
            r2_threshold=R2_THRESHOLD,
            slope_threshold=SLOPE_THRESHOLD,
        )
        assert result["trend_label"] == "Declining"
        assert result["slope"] < 0

    def test_flat_data_labelled_stable(self):
        dates = _make_dates(20, lambda w: 20)
        result = _linear_trend_for_position(
            pd.Series(dates),
            forecast_weeks=8,
            min_weeks=MIN_TREND_WEEKS,
            r2_threshold=R2_THRESHOLD,
            slope_threshold=SLOPE_THRESHOLD,
        )
        assert result["trend_label"] == "Stable"

    def test_too_few_dates_returns_insufficient(self):
        dates = pd.Series(pd.to_datetime(["2024-01-01", "2024-01-02"]))
        result = _linear_trend_for_position(
            dates,
            forecast_weeks=8,
            min_weeks=MIN_TREND_WEEKS,
            r2_threshold=R2_THRESHOLD,
            slope_threshold=SLOPE_THRESHOLD,
        )
        assert result["trend_label"] == "Insufficient data"
        assert result["slope"] == 0.0
        assert np.isnan(result["forecast"])

    def test_empty_series_returns_insufficient(self):
        result = _linear_trend_for_position(
            pd.Series(dtype="datetime64[ns]"),
            forecast_weeks=8,
            min_weeks=MIN_TREND_WEEKS,
            r2_threshold=R2_THRESHOLD,
            slope_threshold=SLOPE_THRESHOLD,
        )
        assert result["trend_label"] == "Insufficient data"

    def test_forecast_non_negative_on_strong_decline(self):
        dates = _make_dates(20, lambda w: max(0, 100 - w * 10))
        result = _linear_trend_for_position(
            pd.Series(dates),
            forecast_weeks=52,
            min_weeks=MIN_TREND_WEEKS,
            r2_threshold=R2_THRESHOLD,
            slope_threshold=SLOPE_THRESHOLD,
        )
        assert result["forecast"] >= 0.0

    def test_r2_bounded(self):
        dates = _make_dates(20, lambda w: 10 + w * 3)
        result = _linear_trend_for_position(
            pd.Series(dates),
            forecast_weeks=8,
            min_weeks=MIN_TREND_WEEKS,
            r2_threshold=R2_THRESHOLD,
            slope_threshold=SLOPE_THRESHOLD,
        )
        assert 0.0 <= result["r2"] <= 1.0

    def test_forecast_positive_for_growing(self):
        dates = _make_dates(20, lambda w: 10 + w * 3)
        result = _linear_trend_for_position(
            pd.Series(dates),
            forecast_weeks=8,
            min_weeks=MIN_TREND_WEEKS,
            r2_threshold=R2_THRESHOLD,
            slope_threshold=SLOPE_THRESHOLD,
        )
        assert result["forecast"] > 0


class TestAddTrendForecast:
    def _make_pos_and_postings(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        rng = np.random.default_rng(0)
        base = pd.Timestamp("2024-01-01")
        records = []
        for week in range(20):
            count = max(0, int(10 + week * 2 + rng.integers(-1, 2)))
            for i in range(count):
                records.append({
                    "search_position": "Data Analyst",
                    "first_seen": base + pd.Timedelta(
                        days=week * 7 + int(rng.integers(0, 7))
                    ),
                    "job_link": f"link_{week}_{i}",
                })
        postings = pd.DataFrame(records)
        postings["first_seen"] = pd.to_datetime(postings["first_seen"])
        pos = (
            postings.groupby("search_position")
            .agg(volume=("job_link", "count"))
            .reset_index()
        )
        return pos, postings

    def test_required_columns_present(self):
        pos, postings = self._make_pos_and_postings()
        result = add_trend_forecast(
            pos.copy(), postings,
            forecast_weeks=4, r2_threshold=R2_THRESHOLD, slope_threshold=SLOPE_THRESHOLD,
        )
        for col in ("trend_slope", "trend_r2", "forecast_4w", "trend_label"):
            assert col in result.columns, f"Missing column: {col}"

    def test_slope_and_r2_are_float(self):
        pos, postings = self._make_pos_and_postings()
        result = add_trend_forecast(
            pos.copy(), postings,
            forecast_weeks=4, r2_threshold=R2_THRESHOLD, slope_threshold=SLOPE_THRESHOLD,
        )
        assert result["trend_slope"].dtype == float
        assert result["trend_r2"].dtype == float

    def test_no_nan_in_slope_r2_label(self):
        pos, postings = self._make_pos_and_postings()
        result = add_trend_forecast(
            pos.copy(), postings,
            forecast_weeks=4, r2_threshold=R2_THRESHOLD, slope_threshold=SLOPE_THRESHOLD,
        )
        assert result["trend_slope"].isna().sum() == 0
        assert result["trend_r2"].isna().sum() == 0
        assert result["trend_label"].isna().sum() == 0

    def test_fallback_when_all_dates_null(self):
        pos = pd.DataFrame({"search_position": ["Data Analyst"], "volume": [100]})
        postings = pd.DataFrame({
            "search_position": ["Data Analyst"],
            "first_seen": pd.Series([pd.NaT], dtype="datetime64[ns]"),
        })
        result = add_trend_forecast(
            pos.copy(), postings,
            forecast_weeks=4, r2_threshold=R2_THRESHOLD, slope_threshold=SLOPE_THRESHOLD,
        )
        assert result["trend_label"].iloc[0] == "Insufficient data"
        assert result["trend_slope"].iloc[0] == 0.0

    def test_label_values_are_valid(self):
        pos, postings = self._make_pos_and_postings()
        result = add_trend_forecast(
            pos.copy(), postings,
            forecast_weeks=4, r2_threshold=R2_THRESHOLD, slope_threshold=SLOPE_THRESHOLD,
        )
        valid = {"Growing", "Declining", "Stable", "Insufficient data"}
        assert set(result["trend_label"].unique()).issubset(valid)

    def test_forecast_col_named_by_window(self):
        pos, postings = self._make_pos_and_postings()
        for weeks in (4, 8, 12):
            result = add_trend_forecast(
                pos.copy(), postings,
                forecast_weeks=weeks, r2_threshold=R2_THRESHOLD, slope_threshold=SLOPE_THRESHOLD,
            )
            assert f"forecast_{weeks}w" in result.columns

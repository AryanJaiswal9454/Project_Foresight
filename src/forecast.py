"""Baseline + model training, rolling-origin backtest, honest evaluation.

Non-negotiable rule: report WAPE vs baseline honestly. If the model doesn't
beat seasonal-naive, that is a finding to report, not a failure to hide.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.metrics import wape, bias
from src.features import build_feature_set

HORIZON_DAYS = 28  # ~4 weeks, matches the engagement's forecast horizon
FEATURE_COLS = [
    "unit_price", "is_promo", "is_holiday_flag", "is_weekend_flag",
    "month", "week_of_year",
    "units_lag_1", "units_lag_7", "units_lag_14", "units_lag_28",
    "units_roll_mean_7", "units_roll_mean_28", "units_roll_std_7", "units_roll_std_28",
]


def seasonal_naive_forecast(df: pd.DataFrame, horizon: int = HORIZON_DAYS) -> pd.DataFrame:
    """Predict demand = same SKU, same day, 364 days ago (one year prior, aligned by weekday)."""
    df = df.sort_values(["sku_id", "date"]).copy()
    df["baseline_pred"] = df.groupby("sku_id")["units_sold"].shift(364)
    return df


def rolling_origin_backtest(df: pd.DataFrame, n_folds: int = 4, horizon: int = HORIZON_DAYS):
    """Train on the past, test on the next `horizon` days, repeat n_folds times moving forward.
    Never a single random split for time series - that would leak future info into training.
    """
    import lightgbm as lgb

    df = df.sort_values(["sku_id", "date"]).reset_index(drop=True)
    dates = sorted(df["date"].unique())
    fold_results = []

    for fold in range(n_folds):
        # walk backward from the end, leaving `fold` horizons out for later folds
        test_end_idx = len(dates) - 1 - fold * horizon
        test_start_idx = test_end_idx - horizon
        if test_start_idx <= 400:  # need enough history for lag_28/roll_28 to be populated
            break
        test_start, test_end = dates[test_start_idx], dates[test_end_idx]
        train_cutoff = dates[test_start_idx - 1]

        train = df[df["date"] <= train_cutoff].dropna(subset=FEATURE_COLS + ["units_sold"])
        test = df[(df["date"] > train_cutoff) & (df["date"] <= test_end)].copy()
        test = test.dropna(subset=FEATURE_COLS)

        if len(train) == 0 or len(test) == 0:
            continue

        model = lgb.LGBMRegressor(n_estimators=200, learning_rate=0.05, num_leaves=31,
                                    min_child_samples=10, verbose=-1)
        model.fit(train[FEATURE_COLS], train["units_sold"])
        test["model_pred"] = model.predict(test[FEATURE_COLS]).clip(min=0)

        model_wape = wape(test["units_sold"], test["model_pred"])
        baseline_wape = wape(test["units_sold"], test["baseline_pred"].fillna(test["units_sold"].mean()))

        fold_results.append({
            "fold": fold, "test_start": test_start, "test_end": test_end,
            "model_wape": model_wape, "baseline_wape": baseline_wape,
            "model_bias": bias(test["units_sold"], test["model_pred"]),
        })

    return pd.DataFrame(fold_results), model


def main():
    df = pd.read_csv("data/processed/analysis_ready.csv", parse_dates=["date"])
    df = seasonal_naive_forecast(df)
    df = build_feature_set(df)

    results, final_model = rolling_origin_backtest(df)
    print(results.to_string(index=False))

    print(f"\nAverage backtest WAPE - Model: {results['model_wape'].mean():.4f} | "
          f"Baseline: {results['baseline_wape'].mean():.4f}")
    improvement = (results['baseline_wape'].mean() - results['model_wape'].mean()) / results['baseline_wape'].mean()
    print(f"Model improves on baseline by: {improvement:.1%}")

    results.to_csv("data/processed/backtest_results.csv", index=False)
    df.to_csv("data/processed/analysis_with_forecast.csv", index=False)
    import joblib
    joblib.dump(final_model, "data/processed/model.pkl")
    print("\nSaved model.pkl, backtest_results.csv, and analysis_with_forecast.csv")


if __name__ == "__main__":
    main()

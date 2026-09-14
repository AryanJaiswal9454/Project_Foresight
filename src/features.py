
import pandas as pd


def add_lag_features(df: pd.DataFrame, lags=(1, 7, 14, 28)) -> pd.DataFrame:
    df = df.sort_values(["sku_id", "date"]).copy()
    for lag in lags:
        df[f"units_lag_{lag}"] = df.groupby("sku_id")["units_sold"].shift(lag)
    return df


def add_rolling_features(df: pd.DataFrame, windows=(7, 28)) -> pd.DataFrame:
    df = df.sort_values(["sku_id", "date"]).copy()
    for w in windows:
        # shift(1) first so today's own value never leaks into its own rolling window
        df[f"units_roll_mean_{w}"] = (
            df.groupby("sku_id")["units_sold"]
            .transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
        )
        df[f"units_roll_std_{w}"] = (
            df.groupby("sku_id")["units_sold"]
            .transform(lambda s: s.shift(1).rolling(w, min_periods=1).std())
        )
    return df


def add_calendar_promo_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["is_promo"] = df["promo_flag"].astype(int)
    df["is_holiday_flag"] = df["is_holiday"].astype(int)
    df["is_weekend_flag"] = df["is_weekend"].astype(int)
    df["month"] = df["date"].dt.month
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    return df


def build_feature_set(df: pd.DataFrame) -> pd.DataFrame:
    df = add_lag_features(df)
    df = add_rolling_features(df)
    df = add_calendar_promo_features(df)
    return df

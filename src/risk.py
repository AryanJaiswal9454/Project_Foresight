"""Stockout / overstock risk scoring - combines forecast with inventory position.
Must stay transparent and explainable (Section 08) - simple, auditable rules,
not a black box.
"""
import pandas as pd
import numpy as np
from pathlib import Path

HORIZON_DAYS = 28


def latest_inventory_position(inventory: pd.DataFrame) -> pd.DataFrame:
    """Most recent snapshot per SKU."""
    latest = inventory.sort_values("date").groupby("sku_id").tail(1).copy()
    return latest


def recent_demand_rate(sales: pd.DataFrame, lookback_days: int = 28) -> pd.DataFrame:
    """Average daily demand over the most recent lookback window per SKU.
    Used as the forward demand-rate assumption for the risk horizon - a simple,
    explainable proxy rather than a full recursive multi-step forecast, and
    documented here rather than hidden.
    """
    cutoff = sales["date"].max() - pd.Timedelta(days=lookback_days)
    recent = sales[sales["date"] > cutoff]
    rate = recent.groupby("sku_id")["units_sold"].mean().rename("avg_daily_demand")
    return rate.reset_index()


def score_risk(sales: pd.DataFrame, inventory: pd.DataFrame, sku_master: pd.DataFrame,
               horizon: int = HORIZON_DAYS) -> pd.DataFrame:
    demand_rate = recent_demand_rate(sales, lookback_days=horizon)
    inv_latest = latest_inventory_position(inventory)

    df = inv_latest.merge(demand_rate, on="sku_id", how="left")
    df = df.merge(sku_master[["sku_id", "product_name", "category", "unit_cost", "list_price"]],
                   on="sku_id", how="left")
    df["avg_daily_demand"] = df["avg_daily_demand"].fillna(0)

    # Stockout risk: forecast demand over the lead time vs stock that will be available
    df["demand_over_lead_time"] = df["avg_daily_demand"] * df["lead_time_days"]
    df["available_stock"] = df["on_hand_units"] + df["on_order_units"]
    df["stockout_risk"] = (
        (df["demand_over_lead_time"] - df["available_stock"]) / df["demand_over_lead_time"].replace(0, np.nan)
    ).clip(lower=0, upper=1).fillna(0)

    # Overstock risk: on-hand stock vs demand over the full forecast horizon
    df["demand_over_horizon"] = df["avg_daily_demand"] * horizon
    df["overstock_risk"] = (
        (df["on_hand_units"] - df["demand_over_horizon"]) / df["on_hand_units"].replace(0, np.nan)
    ).clip(lower=0, upper=1).fillna(0)

    # Rupee value at stake - gated by the same thresholds as the quadrant, so a
    # "Healthy" SKU never shows a nonzero rupee value (D4 criterion: reconciles with the grid).
    df["revenue_at_risk"] = np.where(
        df["stockout_risk"] >= 0.5,
        (df["demand_over_lead_time"] - df["available_stock"]).clip(lower=0) * df["list_price"],
        0.0,
    )
    df["capital_locked"] = np.where(
        df["overstock_risk"] >= 0.5,
        (df["on_hand_units"] - df["demand_over_horizon"]).clip(lower=0) * df["unit_cost"],
        0.0,
    )

    # Quadrant / recommended action
    def quadrant(row):
        high_stockout = row["stockout_risk"] >= 0.5
        high_overstock = row["overstock_risk"] >= 0.5
        if high_stockout and high_overstock:
            return "Watch / Volatile", "Investigate - demand is erratic; review manually."
        elif high_stockout:
            return "Reorder Now", "Raise a replenishment order before stock runs out."
        elif high_overstock:
            return "Markdown / Clear", "Promote or discount to free up capital."
        else:
            return "Healthy", "No action needed; leave as is."

    df[["risk_quadrant", "recommended_action"]] = df.apply(
        lambda r: pd.Series(quadrant(r)), axis=1
    )

    df["rupee_value_at_stake"] = df["revenue_at_risk"] + df["capital_locked"]

    cols = ["sku_id", "product_name", "category", "on_hand_units", "on_order_units",
            "lead_time_days", "reorder_point", "avg_daily_demand", "stockout_risk",
            "overstock_risk", "risk_quadrant", "recommended_action",
            "revenue_at_risk", "capital_locked", "rupee_value_at_stake"]
    return df[cols].sort_values("rupee_value_at_stake", ascending=False)


def main():
    sales = pd.read_csv("data/processed/analysis_ready.csv", parse_dates=["date"])
    inventory = pd.read_csv("data/processed/inventory_clean.csv", parse_dates=["date"])
    sku_master = sales[["sku_id", "product_name", "category", "unit_cost", "list_price"]].drop_duplicates()

    risk_df = score_risk(sales, inventory, sku_master)
    risk_df.to_csv("data/processed/risk_scores.csv", index=False)

    print(risk_df.head(10).to_string(index=False))
    print(f"\nQuadrant counts:\n{risk_df['risk_quadrant'].value_counts()}")
    print(f"\nTotal revenue at risk: Rs {risk_df['revenue_at_risk'].sum():,.0f}")
    print(f"Total capital locked in overstock: Rs {risk_df['capital_locked'].sum():,.0f}")


if __name__ == "__main__":
    main()

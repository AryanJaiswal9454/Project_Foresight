
import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

VALID_SKU_RANGE = [f"SKU{i:03d}" for i in range(1, 51)]  


def load_raw():
    sales = pd.read_csv(RAW_DIR / "sales_daily.csv")
    sku_master = pd.read_csv(RAW_DIR / "sku_master.csv")
    calendar = pd.read_csv(RAW_DIR / "calendar.csv")
    inventory = pd.read_csv(RAW_DIR / "inventory_snapshots.csv")
    return sales, sku_master, calendar, inventory


def clean_sales(sales: pd.DataFrame) -> pd.DataFrame:
    sales = sales.rename(columns={
        "Date": "date", "SKU": "sku_id", "Units_Sold": "units_sold",
        "Revenue": "revenue", "Price": "unit_price", "Promotion": "promo_flag",
    })
    sales["date"] = pd.to_datetime(sales["date"])
    return sales


def clean_sku_master(sku_master: pd.DataFrame) -> pd.DataFrame:
    sku_master = sku_master.rename(columns={
        "SKU": "sku_id", "Product_Name": "product_name", "Category": "category",
        "Subcategory": "subcategory", "Launch_Date": "launch_date",
        "Cost_Price": "unit_cost", "Selling_Price": "list_price",
        "Gross_Margin_Per_Unit": "gross_margin_per_unit",
    })
    sku_master["launch_date"] = pd.to_datetime(sku_master["launch_date"])
    return sku_master


def clean_calendar(calendar: pd.DataFrame) -> pd.DataFrame:
    calendar = calendar.rename(columns={"promotion_event": "promo_event"})
    calendar["date"] = pd.to_datetime(calendar["date"])
    calendar["holiday"] = calendar["holiday"].fillna("No Holiday")
    calendar["promo_event"] = calendar["promo_event"].fillna("No Promotion")
    return calendar


def clean_inventory(inventory: pd.DataFrame, valid_skus: list) -> pd.DataFrame:
    inventory = inventory.rename(columns={
        "Snapshot_Date": "date", "SKU": "sku_id", "Current_Stock": "on_hand_units",
        "On_Order": "on_order_units", "Lead_Time_Days": "lead_time_days",
        "Safety_Stock": "safety_stock", "Reorder_Point": "reorder_point",
        "Inventory_Value": "inventory_value",
    })
    inventory["date"] = pd.to_datetime(inventory["date"])
    before = inventory["sku_id"].nunique()
    inventory = inventory[inventory["sku_id"].isin(valid_skus)].copy()
    after = inventory["sku_id"].nunique()
    print(f"[clean_inventory] Dropped {before - after} SKUs with no matching sales/master record "
          f"({before} -> {after} unique SKUs).")
    return inventory


def build_analysis_dataset(sales: pd.DataFrame, sku_master: pd.DataFrame,
                             calendar: pd.DataFrame) -> pd.DataFrame:
    """Daily sales fact table enriched with product and calendar attributes.
    Inventory is kept separate (different grain - periodic, not daily) and joined
    later during risk scoring against the nearest snapshot date."""
    df = sales.merge(sku_master, on="sku_id", how="left")
    df = df.merge(calendar, on="date", how="left")
    return df


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    sales, sku_master, calendar, inventory = load_raw()

    sales = clean_sales(sales)
    sku_master = clean_sku_master(sku_master)
    calendar = clean_calendar(calendar)
    inventory = clean_inventory(inventory, valid_skus=sku_master["sku_id"].tolist())

    analysis_df = build_analysis_dataset(sales, sku_master, calendar)

    analysis_df.to_csv(PROCESSED_DIR / "analysis_ready.csv", index=False)
    inventory.to_csv(PROCESSED_DIR / "inventory_clean.csv", index=False)

    print(f"\nWrote {len(analysis_df):,} rows to {PROCESSED_DIR / 'analysis_ready.csv'}")
    print(f"Wrote {len(inventory):,} rows to {PROCESSED_DIR / 'inventory_clean.csv'}")
    print(f"\nanalysis_ready.csv columns: {list(analysis_df.columns)}")


if __name__ == "__main__":
    main()

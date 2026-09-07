# Data-Quality & EDA Insight Memo — Project FORESIGHT

## Data-quality issues found and how they were handled

1. **Orphan SKUs in inventory data.** `inventory_snapshots.csv` contained 200 unique SKUs, but only 50 of
   them (`SKU001`-`SKU050`) had matching records in `sku_master.csv` and `sales_daily.csv`. The remaining
   150 (`SKU051`-`SKU200`) had no product master data and no sales history, so they were dropped from the
   analysis-ready inventory table. This is logged automatically every time the pipeline runs.
2. **Calendar nulls were not actually missing data.** `holiday` and `promo_event` in `calendar.csv` are NaN
   on most days - this is expected (most days aren't holidays or promo events), not a data-quality
   problem. Filled with explicit "No Holiday" / "No Promotion" labels rather than left as NaN.
3. **No other issues found.** No missing values, no duplicate rows, no negative units/price/stock, and
   revenue = units_sold x unit_price holds exactly across all 36,550 sales rows.

## Demand patterns

- **Strong, repeating yearly seasonality.** Monthly totals in 2024 and 2025 track each other closely -
  March peaks (~26,800 units), October troughs (~17,200 units).
- **Top movers vs dead stock.** SKU012 sold ~19,067 units over two years; SKU011 sold only ~1,951 units -
  a ~10x spread. SKU011, SKU025, and SKU039 are dead-stock candidates.
- **Promotions drive a real, measurable lift.** Average daily units sold jump ~38% (13.5 to 18.6) when a
  SKU is on promotion.
- **Weekends outsell weekdays by ~25%** (16.3 vs 13.1 average daily units).
- **Counter-intuitive finding: holidays show slightly lower average sales** (12.16 vs 14.02). Reported
  honestly - plausibly a small-sample effect, flagged for the client to sanity-check.
- **Price shows almost no linear correlation with demand** (r ~ 0.08).

## Assumptions
- The catalogue analysed is 50 active SKUs, not the ~200 SKUs referenced qualitatively in the brief.
- Inventory snapshots are monthly, not daily - risk scoring uses the most recent snapshot per SKU.

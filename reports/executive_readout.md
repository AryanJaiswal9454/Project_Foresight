# Project FORESIGHT — Executive Readout
**For: Head of Operations & Finance, NorthBay Living**

## Bottom line
- **Rs 14.9 lakh in revenue is at risk** from one SKU projected to stock out before replenishment arrives.
- **Rs 1.16 crore of working capital is locked** in 8 overstocked SKUs that should be marked down or promoted to clear.
- A demand forecasting model was built and tested honestly: it beats a simple "same time last year"
  baseline by **27.6%**, consistently across four separate test periods.

## What we built
1. A forecast of expected demand per product, refreshed from your own sales history.
2. A risk flag on every product: **Reorder Now**, **Markdown / Clear**, **Watch / Volatile**, or **Healthy**.
3. A live dashboard your team can use directly - filter by category, see the priority action list,
   see forecast vs actual for any product.
4. A live scoring service - look up any product's forecast and risk by ID, on demand.

## Current risk snapshot
| Category | Count |
|---|---|
| Reorder Now | 1 SKU |
| Markdown / Clear | 8 SKUs |
| Watch / Volatile | 0 SKUs |
| Healthy | 41 SKUs |

**Reorder Now (most urgent):** SKU012 (Home Decor) - current stock will run out before the next
replenishment arrives, at an estimated Rs 14.9 lakh in sales at risk if not reordered.

**Markdown / Clear (highest capital impact):** SKU020 (Storage) alone has ~Rs 44 lakh in capital tied up
in stock far exceeding likely demand over the next 4 weeks.

## How much to trust this
- The model was tested the honest way: trained only on the past, tested on periods it never saw,
  repeated four times across different months. It beat the naive baseline in all four.
- Average forecast error (WAPE): **22.6%** for the model vs **31.2%** for the naive baseline.
- This is a first version. Accuracy will likely improve further with more historical data and by
  incorporating store-level detail if that becomes available.

## What we'd recommend next
1. Act on the 1 urgent reorder and 8 markdown candidates this week - the dashboard has the full list.
2. Re-run the pipeline monthly as new sales data comes in; it's fully automated (one command).
3. Consider tracking actual vs forecast accuracy over the next quarter to validate the model in live use.

*Limitations: this analysis covers the 50 SKUs with both sales and product master data; 150 additional
SKUs in the inventory extract had no matching sales history and were excluded rather than guessed at.*

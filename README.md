# Project FORESIGHT — Demand & Inventory Intelligence

Client: NorthBay Living | Zidio Data Science Internship

**Live dashboard:** https://projectforesight-aryan-jaiswal.streamlit.app/
**Live scoring service:** _(pending deployment - see below)_

## Problem
<!-- 2-3 sentences: what NorthBay needs, in your own words -->

## Data
<!-- The four tables used: sales_daily, sku_master, calendar, inventory_snapshots -->
<!-- Where to place raw files: data/raw/ -->

## Setup
```bash
python -m venv venv
source venv/bin/activate      
pip install -r requirements.txt
```

## Run the pipeline (single command, reproducible)
```bash
python -m src.pipeline
```

## Run the dashboard
```bash
streamlit run app/dashboard.py
```

## Run the scoring service
```bash
uvicorn service.main:app --reload
# then: curl http://localhost:8000/score/SKU001
```

## Results
- Baseline WAPE (seasonal-naive): 0.312 (average across 4 backtest folds)
- Model WAPE (LightGBM): 0.226 (average across 4 backtest folds)
- Model beats baseline by 27.6%, consistently across all 4 folds
- Total revenue at risk (stockout): Rs 14,91,239
- Total capital locked (overstock): Rs 1,16,43,982

## Key assumptions
- Catalogue analysed: 50 active SKUs (SKU001-SKU050) with both sales and master data.
  Inventory data contained 200 SKUs; 150 with no matching sales/master record were dropped.
- Inventory snapshots are monthly, not daily - risk scoring uses the most recent snapshot per SKU.
- Forward demand rate for risk scoring uses the trailing 28-day average, not a recursive multi-step
  forecast - documented as a simple, explainable proxy per Section 08's transparency requirement.

## Repository structure
```
foresight/
├── data/
│   ├── raw/            # original extracts (gitignored)
│   └── processed/      # pipeline output (gitignored)
├── notebooks/           # exploration only — logic belongs in src/
├── src/                 # pipeline.py, features.py, forecast.py, risk.py, metrics.py
├── app/                 # Streamlit dashboard
├── service/              # FastAPI scoring endpoint
├── reports/              # data-quality memo, executive readout
└── tests/                # smoke tests for the pipeline
```

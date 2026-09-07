"""Scoring service - returns forecast + risk for a SKU or batch.
Run: uvicorn service.main:app --reload
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import pandas as pd

app = FastAPI(title="FORESIGHT Scoring Service", version="1.0")

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
_risk_df = None


def get_risk_df():
    global _risk_df
    if _risk_df is None:
        _risk_df = pd.read_csv(DATA_DIR / "risk_scores.csv")
    return _risk_df


class SKURequest(BaseModel):
    sku_ids: list[str]


@app.get("/")
def root():
    return {"service": "FORESIGHT scoring", "status": "ok"}


@app.get("/score/{sku_id}")
def score_sku(sku_id: str):
    df = get_risk_df()
    row = df[df["sku_id"] == sku_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"SKU '{sku_id}' not found")
    return row.iloc[0].to_dict()


@app.post("/score/batch")
def score_batch(req: SKURequest):
    df = get_risk_df()
    result = df[df["sku_id"].isin(req.sku_ids)]
    found = set(result["sku_id"])
    missing = [s for s in req.sku_ids if s not in found]
    return {
        "results": result.to_dict(orient="records"),
        "not_found": missing,
    }

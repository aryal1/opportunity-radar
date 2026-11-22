import os
import webbrowser
from pathlib import Path
from threading import Timer

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from opportunity_radar.analyst import analyze_dataset
from opportunity_radar.catalogue import CatalogueError, search_catalogue
from opportunity_radar.store import (
    list_datasets,
    save_analysis,
    save_datasets,
    set_saved,
    stats,
)

ROOT = Path(__file__).parent
app = FastAPI(title="Opportunity Radar API", version="0.2.0", description="Investigate evidence-backed business signals from Poland's public open data catalogue.")


class SyncRequest(BaseModel):
    query: str = Field(default="", max_length=160)


class SaveRequest(BaseModel):
    id: str = Field(min_length=1, max_length=180)
    saved: bool


class AnalyzeRequest(BaseModel):
    id: str = Field(min_length=1, max_length=180)


class InvestigateRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=10)


@app.get("/api/datasets", tags=["datasets"])
def datasets(q: str = Query(default="", max_length=160), saved: bool = False):
    return {"items": list_datasets(q, saved), "stats": stats()}


@app.get("/api/stats", tags=["datasets"])
def dashboard_stats():
    return stats()


@app.post("/api/sync", tags=["datasets"])
def sync_catalogue(request: SyncRequest):
    try:
        records = search_catalogue(request.query, pages=4)
        return {"count": save_datasets(records), "stats": stats()}
    except CatalogueError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post("/api/save", tags=["datasets"])
def save_signal(request: SaveRequest):
    if not set_saved(request.id, request.saved):
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return {"ok": True}


@app.post("/api/analyze", tags=["analysis"])
def analyze(request: AnalyzeRequest):
    record = next((item for item in list_datasets() if item["id"] == request.id), None)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    try:
        report = analyze_dataset(record)
        save_analysis(request.id, report)
        return {"analysis": report}
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/api/investigate", tags=["analysis"], summary="Retrieve source records and create a grounded opportunity brief")
def investigate(request: InvestigateRequest):
    from opportunity_radar.retrieval import investigate_query

    try:
        return investigate_query(request.query, request.top_k)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/{asset:path}", include_in_schema=False)
def static_asset(asset: str):
    root = ROOT / "static"
    target = (root / asset).resolve()
    if root.resolve() not in target.parents or not target.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(target)


def main() -> None:
    load_dotenv()
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8765"))
    print(f"Opportunity Radar running at http://{host}:{port} (API docs: /docs)")
    if host == "127.0.0.1":
        Timer(0.8, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    uvicorn.run(app, host=host, port=port)

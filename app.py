import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Orbita OS v0.2")

# Config
PORT = int(os.getenv("PORT", 8000))
OUTPUTS_DIR = Path("outputs")
LOGS_DIR = Path("logs")


class ScrapingRequest(BaseModel):
    objetivo: str
    limite: int = 50
    fuente: str = "linkedin"


class EnrichmentRequest(BaseModel):
    input_file: Optional[str] = None


def get_most_recent_json() -> dict:
    """Get the most recent JSON file from outputs/"""
    if not OUTPUTS_DIR.exists():
        return {"leads": [], "meta": {"total": 0}}

    json_files = list(OUTPUTS_DIR.glob("*.json"))
    if not json_files:
        return {"leads": [], "meta": {"total": 0}}

    # Get most recent by modification time
    latest = max(json_files, key=lambda p: p.stat().st_mtime)

    try:
        with open(latest, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"leads": [], "meta": {"total": 0, "error": str(e)}}


def run_scraping_agent(objetivo: str, limite: int, fuente: str):
    """Run agent_scraping.py as subprocess"""
    cmd = [
        "python3", "agent_scraping.py",
        "--objetivo", objetivo,
        "--limite", str(limite),
        "--fuente", fuente
    ]
    with open(LOGS_DIR / f"scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", "w") as log:
        subprocess.run(cmd, cwd="/app", stdout=log, stderr=log)


def run_enrichment_agent():
    """Run agent_enrichment.py as subprocess"""
    cmd = ["python3", "agent_enrichment.py"]
    with open(LOGS_DIR / f"enrichment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", "w") as log:
        subprocess.run(cmd, cwd="/app", stdout=log, stderr=log)


# Routes

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the dashboard HTML"""
    dashboard_path = Path("orbita-dashboard.html")
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    return HTMLResponse("<h1>Orbita OS v0.2 - Dashboard not found</h1><p>orbita-dashboard.html not found</p>")


@app.get("/api/leads")
async def get_leads():
    """Get most recent leads from outputs/"""
    return get_most_recent_json()


@app.get("/api/estado")
async def get_estado():
    """Get system status"""
    return {
        "status": "running",
        "version": "0.2",
        "timestamp": datetime.now().isoformat(),
        "outputs_count": len(list(OUTPUTS_DIR.glob("*.json"))) if OUTPUTS_DIR.exists() else 0,
        "logs_count": len(list(LOGS_DIR.glob("*.log"))) if LOGS_DIR.exists() else 0,
    }


@app.post("/api/scraping/lanzar")
async def lanzar_scraping(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """Launch scraping agent in background"""
    background_tasks.add_task(run_scraping_agent, request.objetivo, request.limite, request.fuente)
    return {
        "status": "launched",
        "objetivo": request.objetivo,
        "limite": request.limite,
        "fuente": request.fuente,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/enriquecimiento/lanzar")
async def lanzar_enriquecimiento(request: EnrichmentRequest, background_tasks: BackgroundTasks):
    """Launch enrichment agent in background"""
    background_tasks.add_task(run_enrichment_agent)
    return {
        "status": "launched",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Ensure directories exist
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    uvicorn.run(app, host="0.0.0.0", port=PORT)

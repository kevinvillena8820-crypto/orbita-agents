import os, json, glob, subprocess
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
estado = {"scraping": "idle", "enrichment": "idle"}

class CicloReq(BaseModel):
    objetivo: str = "inmobiliarias Valencia España"
    fuente: str = "google_maps"
    limite: int = 100
    dry_run: bool = False

class EnrReq(BaseModel):
    limite: int = 50
    dry_run: bool = False

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    p = Path("orbita-dashboard.html")
    return HTMLResponse(p.read_text(encoding="utf-8") if p.exists() else "<h1>Dashboard no encontrado</h1>")

@app.get("/api/estado")
async def get_estado():
    archivos = sorted(glob.glob("outputs/leads_*.json"), key=os.path.getctime, reverse=True)
    total = 0
    if archivos:
        with open(archivos[0]) as f: leads = json.load(f)
        total = len(leads)
    return {"leads_total": total, "agentes": estado, "ts": datetime.now().isoformat()}

@app.get("/api/leads")
async def get_leads():
    archivos = sorted(glob.glob("outputs/leads_*.json"), key=os.path.getctime, reverse=True)
    if not archivos: return {"leads": [], "total": 0}
    with open(archivos[0]) as f: leads = json.load(f)
    return {"leads": leads, "total": len(leads)}

def run_scraping(req):
    estado["scraping"] = "running"
    cmd = ["python3", "agent_scraping.py", "--fuente", req.fuente, "--objetivo", req.objetivo, "--limite", str(req.limite)]
    if req.dry_run: cmd.append("--dry-run")
    subprocess.run(cmd, timeout=300)
    estado["scraping"] = "idle"

def run_enrichment(req):
    estado["enrichment"] = "running"
    cmd = ["python3", "agent_enrichment.py", "--limite", str(req.limite)]
    if req.dry_run: cmd.append("--dry-run")
    subprocess.run(cmd, timeout=600)
    estado["enrichment"] = "idle"

@app.post("/api/scraping/lanzar")
async def lanzar_scraping(req: CicloReq, bg: BackgroundTasks):
    if estado["scraping"] == "running": raise HTTPException(400, "Ya en ejecución")
    bg.add_task(run_scraping, req)
    return {"ok": True, "msg": f"Lanzado: {req.objetivo}"}

@app.post("/api/enriquecimiento/lanzar")
async def lanzar_enr(req: EnrReq, bg: BackgroundTasks):
    if estado["enrichment"] == "running": raise HTTPException(400, "Ya en ejecución")
    bg.add_task(run_enrichment, req)
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

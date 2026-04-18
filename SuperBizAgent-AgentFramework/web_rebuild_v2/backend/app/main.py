from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


app = FastAPI(title="Web Rebuild V2")

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "frontend"

app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR)), name="assets")


@app.get("/api/health")
def health():
    return {"ok": True, "service": "web-rebuild-v2"}


@app.get("/")
def index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

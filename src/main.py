from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from src.config import SECRET_KEY, STATIC
from src.db import init_db
from src.routes import api_router
from src.services import MAINTENANCE_ALLOWED, maintenance


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    print(f'\n{"_" * 21}\nhttp://localhost:8000\nhttp://localhost:8000/admin\n{"_" * 21}\n')
    yield


app = FastAPI(title="Sentiment-Analyse Mitarbeiterzufriedenheit", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


@app.middleware("http")
async def maintenance_gate(request: Request, call_next):
    if maintenance["active"] and request.url.path not in MAINTENANCE_ALLOWED:
        headers = {"Retry-After": "120"}
        if "text/html" in request.headers.get("accept", ""):
            return FileResponse(STATIC / "maintenance.html", status_code=503, headers=headers)
        return JSONResponse({"detail": "Wartung läuft"}, status_code=503, headers=headers)
    return await call_next(request)


app.include_router(api_router)

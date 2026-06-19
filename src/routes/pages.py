from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, RedirectResponse

from src.config import STATIC

router = APIRouter()


@router.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@router.get("/app.css")
def app_css():
    return FileResponse(STATIC / "app.css", media_type="text/css")


@router.get("/favicon.png")
def favicon():
    return FileResponse(STATIC / "favicon.png", media_type="image/png")


@router.get("/admin")
def admin_page(request: Request):
    if not request.session.get("admin"):
        return RedirectResponse("/admin/login", status_code=303)
    return FileResponse(STATIC / "admin.html")

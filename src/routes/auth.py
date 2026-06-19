import hmac

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse

from src.config import ADMIN_PASSWORD, STATIC

router = APIRouter()


def require_admin(request: Request):
    if not request.session.get("admin"):
        raise HTTPException(status_code=401, detail="nicht angemeldet")


@router.get("/admin/login")
def login_page():
    return FileResponse(STATIC / "login.html")


@router.post("/admin/login")
def login(request: Request, password: str = Form()):
    if not hmac.compare_digest(password, ADMIN_PASSWORD):
        return RedirectResponse("/admin/login?error=1", status_code=303)
    request.session["admin"] = True
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=303)

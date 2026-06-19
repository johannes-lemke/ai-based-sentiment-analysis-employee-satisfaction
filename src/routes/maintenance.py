from fastapi import APIRouter

from src.services import maintenance

router = APIRouter()


# Bewusst ohne require_admin: muss auch waehrend der Wartung antworten, damit
# die Wartungsseite den Fortschritt anzeigen kann (siehe MAINTENANCE_ALLOWED).
@router.get("/admin/reevaluate/status")
def reevaluate_status():
    return {
        "active": maintenance["active"],
        "total": maintenance["total"],
        "done": maintenance["done"],
        "since": maintenance["since"].isoformat() if maintenance["since"] else None,
    }

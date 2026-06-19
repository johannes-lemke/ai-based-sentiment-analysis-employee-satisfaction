import threading
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from src.db import Category, engine
from src.routes.auth import require_admin
from src.schemas import CategorySave, check_unique
from src.services import maintenance, run_reevaluation

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/admin/categories")
def list_categories():
    with Session(engine) as session:
        cats = session.exec(select(Category).order_by(Category.name)).all()
        return [{"id": c.id, "name": c.name} for c in cats]


@router.post("/admin/categories/save")
def save_categories(payload: CategorySave):
    if maintenance["active"]:
        raise HTTPException(status_code=409, detail="Neuauswertung läuft bereits")
    names = check_unique(payload.categories, "Kategorienamen")
    # Kategorien werden von nichts referenziert (Aspect speichert den Namen als
    # Text), daher komplett ersetzen statt einzeln zu diffen.
    with Session(engine) as session:
        for cat in session.exec(select(Category)).all():
            session.delete(cat)
        session.flush()
        for name in names:
            session.add(Category(name=name))
        session.commit()
    maintenance.update(active=True, total=0, done=0, since=payload.since,
                       started_at=datetime.now(UTC), finished_at=None)
    threading.Thread(target=run_reevaluation, args=(payload.since,), daemon=True).start()
    return {"status": "started"}

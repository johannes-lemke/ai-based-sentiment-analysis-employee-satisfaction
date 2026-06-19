from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from src.db import Feedback, Location, engine
from src.routes.auth import require_admin
from src.schemas import LocationSave, check_unique

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/admin/locations")
def list_admin_locations():
    with Session(engine) as session:
        locs = session.exec(select(Location).order_by(Location.name)).all()
        return [{"id": loc.id, "name": loc.name} for loc in locs]


@router.post("/admin/locations/save")
def save_locations(payload: LocationSave):
    check_unique(payload.locations, "Bereichsnamen")
    with Session(engine) as session:
        existing = {loc.id: loc for loc in session.exec(select(Location)).all()}
        keep_ids = set()
        for item in payload.locations:
            loc = existing.get(item.id) if item.id is not None else None
            if loc is not None:
                loc.name = item.name
                session.add(loc)
                keep_ids.add(loc.id)
            else:
                session.add(Location(name=item.name))
        # Geloeschte Bereiche: Feedback-Verweise loesen, sonst zeigt das
        # Dashboard auf eine nicht mehr existierende ID.
        for loc_id, loc in existing.items():
            if loc_id in keep_ids:
                continue
            refs = session.exec(select(Feedback).where(Feedback.location_id == loc_id)).all()
            for fb in refs:
                fb.location_id = None
                session.add(fb)
            session.delete(loc)
        session.commit()
    return {"status": "saved"}

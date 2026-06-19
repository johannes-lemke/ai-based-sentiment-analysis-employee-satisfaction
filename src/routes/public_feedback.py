from datetime import date

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from sqlmodel import Session, select

from src.config import logger
from src.db import Category, Feedback, Location, engine
from src.schemas import FeedbackIn
from src.services import classify_feedback

router = APIRouter()


@router.get("/locations")
def list_locations():
    with Session(engine) as session:
        locations = session.exec(select(Location).order_by(Location.name)).all()
        items = [{"id": loc.id, "name": loc.name} for loc in locations]
    return {"locations": items}


@router.post("/feedback")
def feedback(payload: FeedbackIn, request: Request, background_tasks: BackgroundTasks):
    today = date.today().isoformat()
    if request.session.get("last_feedback_date") == today:
        raise HTTPException(status_code=429, detail="heute bereits Feedback abgegeben")
    text = payload.text
    logger.info("Query: %s", text)
    with Session(engine) as session:
        location_id = payload.location_id
        if location_id is not None and session.get(Location, location_id) is None:
            raise HTTPException(status_code=422, detail="unbekannter Bereich")
        entry = Feedback(text=text, location_id=location_id)
        session.add(entry)
        session.commit()
        feedback_id = entry.id
        categories = [c.name for c in session.exec(select(Category)).all()]
    request.session["last_feedback_date"] = today
    background_tasks.add_task(classify_feedback, feedback_id, text, categories)
    return {"status": "ok"}

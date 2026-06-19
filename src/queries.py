from datetime import UTC, date, datetime, time, timedelta

from sqlmodel import Session, select

from src.db import Aspect, Feedback, Location


def aspects_for(session: Session, feedback_id: int) -> list[Aspect]:
    return session.exec(select(Aspect).where(Aspect.feedback_id == feedback_id)).all()


def location_names(session: Session) -> dict[int, str]:
    return {loc.id: loc.name for loc in session.exec(select(Location)).all()}


def filter_by_date(stmt, date_from: date | None, date_to: date | None):
    if date_from:
        stmt = stmt.where(Feedback.created_at >= datetime.combine(date_from, time.min, UTC))
    if date_to:
        end = datetime.combine(date_to + timedelta(days=1), time.min, UTC)
        stmt = stmt.where(Feedback.created_at < end)
    return stmt

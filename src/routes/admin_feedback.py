import csv
import io
import zipfile
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func
from sqlmodel import Session, select

from src.db import Feedback, engine
from src.queries import aspects_for, filter_by_date, location_names
from src.routes.auth import require_admin

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/admin/feedback")
def list_feedback(page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=200),
                  date_from: date | None = Query(None, alias="from"),
                  date_to: date | None = Query(None, alias="to")):
    with Session(engine) as session:
        count_stmt = filter_by_date(select(func.count()).select_from(Feedback), date_from, date_to)
        total = session.exec(count_stmt).one()
        rows = session.exec(
            filter_by_date(select(Feedback), date_from, date_to)
            .order_by(desc(Feedback.created_at))
            .offset((page - 1) * size)
            .limit(size)
        ).all()
        names = location_names(session)
        items = []
        for fb in rows:
            aspects = aspects_for(session, fb.id)
            items.append({
                "id": fb.id,
                "created_at": fb.created_at.isoformat(),
                "location": names.get(fb.location_id),
                "text": fb.text,
                "aspects": [{"category": a.category, "score": a.score} for a in aspects],
            })
    return {"items": items, "page": page, "size": size, "total": total}


def export_filename(date_from: date | None, date_to: date | None) -> str:
    start = date_from.isoformat() if date_from else "anfang"
    end = date_to.isoformat() if date_to else "ende"
    return f"feedback_{start}_{end}.zip"


@router.get("/admin/feedback/export")
def export_feedback(date_from: date | None = Query(None, alias="from"),
                    date_to: date | None = Query(None, alias="to")):
    stmt = filter_by_date(select(Feedback), date_from, date_to).order_by(Feedback.created_at)

    buffer = io.StringIO()
    buffer.write("\ufeff")  # BOM, damit deutsches Excel UTF-8 erkennt
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(["feedback_id", "created_at", "location", "text", "category", "score"])
    with Session(engine) as session:
        names = location_names(session)
        for fb in session.exec(stmt).all():
            created = fb.created_at.isoformat()
            location = names.get(fb.location_id, "")
            aspects = aspects_for(session, fb.id)
            if aspects:
                for a in aspects:
                    writer.writerow([fb.id, created, location, fb.text, a.category, a.score])
            else:
                writer.writerow([fb.id, created, location, fb.text, "", ""])

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("feedback.csv", buffer.getvalue().encode("utf-8"))
    zip_buffer.seek(0)

    name = export_filename(date_from, date_to)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )

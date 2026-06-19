from collections import defaultdict
from datetime import UTC, date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select

from src.config import BERLIN
from src.db import Aspect, Feedback, engine
from src.queries import location_names
from src.routes.auth import require_admin

router = APIRouter(dependencies=[Depends(require_admin)])


def month_label(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def add_months(d: date, n: int) -> date:
    index = d.year * 12 + (d.month - 1) + n
    return date(index // 12, index % 12 + 1, 1)


def month_labels(date_from: date, date_to: date) -> list[str]:
    labels = []
    cur = date(date_from.year, date_from.month, 1)
    last = date(date_to.year, date_to.month, 1)
    while cur <= last:
        labels.append(month_label(cur))
        cur = add_months(cur, 1)
    return labels


def feedback_years(session: Session) -> list[int]:
    # Jahre mit Feedback, aus Berliner Sicht.
    years = set()
    for created_at in session.exec(select(Feedback.created_at)).all():
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        years.add(created_at.astimezone(BERLIN).year)
    return sorted(years)


@router.get("/admin/dashboard")
def dashboard(date_from: date | None = Query(None, alias="from"),
              date_to: date | None = Query(None, alias="to")):
    with Session(engine) as session:
        location_name = location_names(session)
        years = feedback_years(session)

        if date_from is None or date_to is None:
            # Default: neuestes Jahr mit Daten, ganzes Jahr.
            year = years[-1] if years else datetime.now(BERLIN).year
            date_from = date_from or date(year, 1, 1)
            date_to = date_to or date(year, 12, 31)
        if date_from > date_to:
            raise HTTPException(status_code=422, detail="from liegt nach to")

        start_utc = datetime.combine(date_from, time.min, BERLIN).astimezone(UTC)
        end_utc = datetime.combine(date_to + timedelta(days=1), time.min, BERLIN).astimezone(UTC)

        rows = session.exec(
            select(Aspect.category, Aspect.score, Feedback.created_at, Feedback.location_id)
            .join(Feedback, Aspect.feedback_id == Feedback.id)
            .where(Feedback.created_at >= start_utc, Feedback.created_at < end_utc)
        ).all()

        feedback_count = session.exec(
            select(func.count()).select_from(Feedback)
            .where(Feedback.created_at >= start_utc, Feedback.created_at < end_utc)
        ).one()

    # (location_name|None, category, month) und (category, month) fuer Gesamt.
    by_location = defaultdict(lambda: [0, 0])  # [score_sum, count]
    total = defaultdict(lambda: [0, 0])
    categories = set()
    # Kennzahlen fuer die KPI-Kopfzeile (ganzer Zeitraum, alle Bereiche).
    overall = [0, 0]                            # [score_sum, count]
    month_totals = defaultdict(lambda: [0, 0])  # je Monat ueber alle Kategorien
    distribution = {1: 0, 2: 0, 3: 0}
    for category, score, created_at, location_id in rows:
        if created_at.tzinfo is None:  # SQLite liefert naive Werte, als UTC lesen
            created_at = created_at.replace(tzinfo=UTC)
        month = month_label(created_at.astimezone(BERLIN).date())
        loc = location_name.get(location_id)  # None bleibt "ohne Angabe"
        by_location[(loc, category, month)][0] += score
        by_location[(loc, category, month)][1] += 1
        total[(category, month)][0] += score
        total[(category, month)][1] += 1
        categories.add(category)
        overall[0] += score
        overall[1] += 1
        month_totals[month][0] += score
        month_totals[month][1] += 1
        if score in distribution:
            distribution[score] += 1

    months = month_labels(date_from, date_to)
    categories = sorted(categories)

    def points(get) -> dict[str, list[dict]]:
        series = {}
        for category in categories:
            line = []
            for month in months:
                bucket = get(category, month)
                if bucket:
                    line.append({"month": month,
                                 "avg": round(bucket[0] / bucket[1], 2),
                                 "n": bucket[1]})
            if line:
                series[category] = line
        return series

    # Bereiche: None (ohne Angabe) zuerst, dann alle aus der Tabelle alphabetisch.
    ordered = [None, *sorted(location_name.values())]
    locations = [{"location": loc,
                  "series": points(lambda c, m, loc=loc: by_location.get((loc, c, m)))}
                 for loc in ordered]

    # KPI-Kennzahlen. Index = Durchschnittsscore auf 0-100 skaliert.
    def to_percent(avg: float) -> int:
        return round((avg - 1) / 2 * 100)

    index = to_percent(overall[0] / overall[1]) if overall[1] else None
    month_index = {m: s / c for m, (s, c) in month_totals.items() if c}
    present = [m for m in months if m in month_index]
    trend = None
    if len(present) >= 2:
        last, prev = present[-1], present[-2]
        trend = {"month": last,
                 "delta": to_percent(month_index[last]) - to_percent(month_index[prev])}

    summary = {
        "index": index,
        "feedback_count": feedback_count,
        "aspect_count": overall[1],
        "distribution": {"pos": distribution[3], "neu": distribution[2], "neg": distribution[1]},
        "trend": trend,
    }

    return {
        "from": date_from.isoformat(),
        "to": date_to.isoformat(),
        "years": years,
        "months": months,
        "categories": categories,
        "total": points(lambda c, m: total.get((c, m))),
        "locations": locations,
        "summary": summary,
    }

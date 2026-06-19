import json
from datetime import UTC, date, datetime, time

from openai import OpenAI
from sqlmodel import Session, select

from src.config import API_KEY, BASE_URL, BERLIN, MODEL, logger
from src.db import Aspect, Category, Feedback, engine

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


# Wartungsmodus: nur im Speicher, kein Resume nach Neustart.
maintenance: dict = {
    "active": False,
    "total": 0,
    "done": 0,
    "since": None,
    "started_at": None,
    "finished_at": None,
}

# Einziger Pfad, der waehrend der Wartung antwortet (Fortschritt fuer die Seite).
MAINTENANCE_ALLOWED = {"/admin/reevaluate/status"}


def build_system_prompt(categories: list[str]) -> str:
    joined = ", ".join(categories)
    return (
        "Du analysierst Mitarbeiter-Feedback. Zerlege den Text in einzelne "
        "Aussagen. Ordne jede Aussage genau einer der folgenden Kategorien zu: "
        f"{joined}. Fasse mehrere Aussagen zur selben Kategorie zusammen, jede "
        "Kategorie kommt höchstens einmal vor. "
        "Bewerte die Stimmung je Aussage mit einem Score: 1 = negativ, "
        "2 = neutral, 3 = positiv. "
        'Antworte ausschließlich als JSON: '
        '{"aspects": [{"category": "...", "score": 2}]}.'
    )


def classify_feedback(feedback_id: int, text: str, categories: list[str]) -> None:
    try:
        # noinspection PyTypeChecker
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": build_system_prompt(categories)},
                      {"role": "user", "content": text}],
            response_format={"type": "json_object"},
            stream=False,
            extra_body={"think": False},
        )
    except Exception as exc:
        logger.info("LLM nicht erreichbar: %s", exc)
        return
    # noinspection PyUnresolvedReferences
    content = response.choices[0].message.content
    if not content:
        logger.info("Response: leer")
        return
    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        logger.info("Response: ungueltiges JSON: %s", exc)
        return
    logger.info("Response: %s", result)
    aspects = []
    seen = set()
    for item in result.get("aspects", []):
        category = item.get("category")
        try:
            score = int(item.get("score"))
        except (TypeError, ValueError):
            continue
        if not category or score not in (1, 2, 3):
            continue
        if category in seen:
            continue
        seen.add(category)
        aspects.append({"category": category, "score": score})
    if not aspects:
        logger.info("Response: keine Aspekte")
        return
    with Session(engine) as session:
        for item in aspects:
            session.add(Aspect(feedback_id=feedback_id,
                               category=item["category"],
                               score=item["score"]))
        session.commit()


def run_reevaluation(since: date) -> None:
    # Alle Feedbacks ab Stichtag nacheinander neu klassifizieren.
    start_utc = datetime.combine(since, time.min, BERLIN).astimezone(UTC)
    with Session(engine) as session:
        categories = [c.name for c in session.exec(select(Category)).all()]
        rows = session.exec(
            select(Feedback).where(Feedback.created_at >= start_utc)
            .order_by(Feedback.created_at)
        ).all()
        items = [(fb.id, fb.text) for fb in rows]
    maintenance["total"] = len(items)
    maintenance["done"] = 0
    try:
        for feedback_id, text in items:
            with Session(engine) as session:
                old = session.exec(
                    select(Aspect).where(Aspect.feedback_id == feedback_id)
                ).all()
                for aspect in old:
                    session.delete(aspect)
                session.commit()
            classify_feedback(feedback_id, text, categories)
            maintenance["done"] += 1
    finally:
        maintenance["active"] = False
        maintenance["finished_at"] = datetime.now(UTC)

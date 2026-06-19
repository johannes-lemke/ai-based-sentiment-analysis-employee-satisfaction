import os
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlmodel import Field, Session, SQLModel, create_engine, select

DATABASE_URL = os.environ["DATABASE_URL"]

# Bei SQLite den Ordner der Datei anlegen, falls er fehlt.
if DATABASE_URL.startswith("sqlite:///"):
    path = Path(DATABASE_URL.removeprefix("sqlite:///"))
    path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)


class Location(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)


class Feedback(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    text: str
    location_id: int | None = Field(default=None, foreign_key="location.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Aspect(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    feedback_id: int = Field(foreign_key="feedback.id")
    category: str
    score: int


SEED_CATEGORIES = [
    "Arbeitszeit",
    "Vergütung",
    "Führung",
    "Team",
    "Ausstattung",
    "Weiterbildung",
    "Work-Life-Balance",
    "Kommunikation",
    "Sonstiges",
]

SEED_LOCATIONS = [
    "Leben + Wohnen",
    "Bildung + Beschäftigung",
    "Kinder, Jugend + Familie",
    "Treffpunkte + Begegnungsstätten",
    "Projekte + Initiativen",
]


# Textbausteine je Kategorie und Score (1 = negativ, 2 = neutral, 3 = positiv).
# Ein Seed-Feedback setzt sich aus den Bausteinen der gewaehlten Kategorien
# zusammen, die Aspekte ergeben sich direkt daraus.
SEED_PHRASES = {
    "Arbeitszeit": {
        1: ["Die Arbeitszeiten sind zu starr und lassen kaum Spielraum.",
            "Ständige Überstunden machen die Arbeitszeit zur Belastung."],
        2: ["Die Arbeitszeiten sind in Ordnung, nichts Besonderes.",
            "An den Arbeitszeiten hat sich zuletzt wenig geändert."],
        3: ["Die flexiblen Arbeitszeiten passen gut zu meinem Alltag.",
            "Gleitzeit funktioniert bei uns reibungslos."],
    },
    "Vergütung": {
        1: ["Das Gehalt ist für die Aufgaben deutlich zu niedrig.",
            "Bei der Vergütung hinken wir dem Markt hinterher."],
        2: ["Die Bezahlung ist durchschnittlich.",
            "An der Vergütung gibt es nichts Auffälliges."],
        3: ["Die Bezahlung ist fair und pünktlich.",
            "Mit der Vergütung bin ich zufrieden."],
    },
    "Führung": {
        1: ["Die Führung trifft Entscheidungen ohne das Team einzubeziehen.",
            "Vom Vorgesetzten kommt kaum Rückmeldung."],
        2: ["Die Führung ist okay, hält sich meist raus.",
            "Mit dem Vorgesetzten komme ich neutral aus."],
        3: ["Mein Vorgesetzter unterstützt mich, wo er kann.",
            "Die Führung ist klar und verlässlich."],
    },
    "Team": {
        1: ["Im Team gibt es viele Spannungen.",
            "Die Zusammenarbeit im Team klemmt oft."],
        2: ["Das Team funktioniert solide.",
            "Im Team läuft es unauffällig."],
        3: ["Im Team helfen wir uns gegenseitig.",
            "Der Zusammenhalt im Team ist stark."],
    },
    "Ausstattung": {
        1: ["Die Hardware ist veraltet und langsam.",
            "Mir fehlt vernünftiges Arbeitsmaterial."],
        2: ["Die Ausstattung reicht gerade so.",
            "An der Ausstattung gibt es wenig auszusetzen, aber nichts Besonderes."],
        3: ["Die technische Ausstattung ist modern und schnell.",
            "Mit der Ausstattung kann ich gut arbeiten."],
    },
    "Weiterbildung": {
        1: ["Für Weiterbildung gibt es weder Zeit noch Budget.",
            "Schulungen werden regelmäßig abgelehnt."],
        2: ["Weiterbildung ist möglich, wird aber selten genutzt.",
            "Beim Thema Weiterbildung tut sich wenig."],
        3: ["Ich konnte mehrere Schulungen besuchen.",
            "Die Firma fördert Weiterbildung aktiv."],
    },
    "Work-Life-Balance": {
        1: ["Die Work-Life-Balance leidet stark unter der Arbeitslast.",
            "Abschalten nach Feierabend ist kaum möglich."],
        2: ["Die Work-Life-Balance ist mittelmäßig.",
            "Die Balance zwischen Arbeit und Freizeit ist okay."],
        3: ["Ich kann Beruf und Privatleben gut vereinbaren.",
            "Die Work-Life-Balance stimmt für mich."],
    },
    "Kommunikation": {
        1: ["Informationen erreichen uns viel zu spät.",
            "Die interne Kommunikation ist chaotisch."],
        2: ["Die Kommunikation läuft normal.",
            "An der Kommunikation gibt es nichts Auffälliges."],
        3: ["Die Kommunikation im Haus ist offen und klar.",
            "Wichtige Infos kommen zuverlässig an."],
    },
    "Sonstiges": {
        1: ["Insgesamt bin ich derzeit unzufrieden.",
            "Vieles könnte besser organisiert sein."],
        2: ["Insgesamt ist alles im üblichen Rahmen.",
            "Nichts Besonderes zu berichten."],
        3: ["Insgesamt fühle ich mich hier wohl.",
            "Ich arbeite gerne hier."],
    },
}

SEED_FEEDBACK_COUNT = 400
SEED_RNG_SEED = 42
SEED_NO_LOCATION_SHARE = 0.15  # Anteil Feedbacks ohne Bereichsangabe
SEED_START = datetime(2025, 1, 1, tzinfo=UTC)  # frühester Zeitpunkt der Seed-Daten


def seed_feedbacks(session: Session) -> None:
    rng = random.Random(SEED_RNG_SEED)
    location_ids = [loc.id for loc in session.exec(select(Location)).all()]
    span_seconds = int((datetime.now(UTC) - SEED_START).total_seconds())
    for _ in range(SEED_FEEDBACK_COUNT):
        categories = rng.sample(list(SEED_PHRASES), rng.randint(1, 3))
        aspects = [(cat, rng.choice([1, 2, 3])) for cat in categories]
        text = " ".join(rng.choice(SEED_PHRASES[cat][score]) for cat, score in aspects)
        location_id = None if rng.random() < SEED_NO_LOCATION_SHARE else rng.choice(location_ids)
        created_at = SEED_START + timedelta(seconds=rng.randint(0, span_seconds))
        feedback = Feedback(text=text, location_id=location_id, created_at=created_at)
        session.add(feedback)
        session.flush()  # feedback.id verfuegbar machen
        for category, score in aspects:
            session.add(Aspect(feedback_id=feedback.id, category=category, score=score))


def init_db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        if session.exec(select(Category)).first() is None:
            session.add_all(Category(name=name) for name in SEED_CATEGORIES)
        if session.exec(select(Location)).first() is None:
            session.add_all(Location(name=name) for name in SEED_LOCATIONS)
        session.commit()
        if session.exec(select(Feedback)).first() is None:
            seed_feedbacks(session)
            session.commit()

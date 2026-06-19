# KI-basierte Sentiment-Analyse zur Mitarbeiterzufriedenheit

Prototyp im Rahmen einer Hausarbeit. Aus anonymem
Freitext-Feedback von Mitarbeitern wird automatisch die Stimmung erfasst, ein
Thema erkannt und das Ganze in einem kleinen Dashboard sichtbar gemacht.

Bewusst einfach und wartbar gehalten: [Ollama](https://ollama.com/) als lokales
KI-Modell (Qwen3, OpenAI-kompatibel und per `.env` austauschbar), FastAPI als
Backend, SQLite als Datenbank, Frontend in schlankem HTML/CSS ohne Framework.

---

## Setup

### 1. Ollama installieren und Modell laden

Ollama nach den Anweisungen auf https://ollama.com/download installieren. 

```
ollama pull qwen3:1.7b
```

Wird `ollama` direkt nach der Installation nicht gefunden, kennt das offene
Terminal den neuen PATH noch nicht. Ein neues Terminal öffnen oder den PATH neu
laden behebt das.


### 2. Konfiguration anlegen

```
cp .env.example .env
```

Dann `.env` anpassen (`BASE_URL`, `MODEL`, ...). Für lokales Ollama auf dem Host
passen die Defaults in der Regel unverändert.

### 3. Image bauen

```
docker compose build
```

### 4. Start

```
docker compose up
```

Erreichbar unter http://localhost:8000 (API-Doku: `/docs`).

### 5. Admin-Panel aufrufen und Stammdaten pflegen

Das Admin-Panel liegt unter http://localhost:8000/admin. Der Login erfolgt mit
dem Passwort aus `ADMIN_PASSWORD` (siehe `.env`).

Vor der ersten Nutzung müssen die Stammdaten gepflegt werden, sonst hat die KI
keine Grundlage für die Auswertung:

- **Kategorien**: Themen, denen die KI jede Aussage zuordnet und für die sie die
  Stimmung bewertet (z. B. *Arbeitsklima*, *Bezahlung*, *Ausstattung*). Ohne
  Kategorien kann eingehendes Feedback nicht sinnvoll klassifiziert werden.
- **Bereiche**: Abteilungen oder Standorte, die bei der Feedback-Abgabe optional
  ausgewählt werden und das Dashboard nach Bereich aufschlüsseln.

Beim Speichern von Kategorien wird vorhandenes Feedback ab einem wählbaren
Stichtag neu ausgewertet; währenddessen läuft die App im Wartungsmodus.

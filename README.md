# amd-act2-router — General-Purpose AI Agent (Track 1)

Ein Routing-Agent für den **AMD Developer Hackathon: ACT II**, Track 1
(*General-Purpose AI Agent*) — löst Aufgaben aus 8 Kategorien (Factual
Knowledge, Math Reasoning, Sentiment, Summarisation, NER, Code Debugging,
Logical Reasoning, Code Generation) über Fireworks-AI-Modelle, so
tokeneffizient wie möglich.

Der Agent entscheidet pro Aufgabe selbst, ob er ein **eigenes lokales Modell**
(Tokens zählen 0) oder ein **Remote-Modell über die Fireworks AI API** (Tokens
zählen) benutzt. Ziel: möglichst wenige Tokens verbrauchen, ohne das
Accuracy-Gate zu verfehlen.

## Idee (Cascade-Routing)

1. Jede Aufgabe geht **zuerst an das lokale Modell** (kostet 0 Tokens).
2. Das lokale Modell liefert Antwort **und** eine Selbsteinschätzung
   (`CONFIDENCE: 0–100`).
3. Ein **Judge** liest diese Zahl aus. Liegt sie über der Schwelle, wird die
   lokale Antwort behalten. Optional prüft ein zweiter, skeptischer
   **Kritiker** (ebenfalls lokal) die Antwort noch einmal.
4. Ist die Antwort nicht vertrauenswürdig, wird an **Fireworks eskaliert** —
   nur dann entstehen zählende Tokens. Alle Fireworks-Calls laufen über die
   vom Wettbewerbs-Harness injizierte `FIREWORKS_BASE_URL`, ausschließlich mit
   Modellen aus `ALLOWED_MODELS`.

```
Aufgabe
   │
   ▼
lokales Modell  ──►  Judge (Confidence ≥ Schwelle?)  ──► [ja]  lokale Antwort (0 Tokens)
                          │
                        [nein]
                          ▼
                    Fireworks (Remote)  ──►  Antwort (Tokens zählen)
```

## Projektstruktur

| Datei | Zweck |
|---|---|
| `router/config.py` | Zentrale Konfiguration — alles über Umgebungsvariablen steuerbar |
| `router/local_client.py` | Ruft das lokale Modell (OpenAI-kompatibel, z. B. Ollama) auf |
| `router/remote_client.py` | Ruft Fireworks AI auf, mit Timeout/Token-Telemetrie |
| `router/judge.py` | Wertet Selbsteinschätzung aus + optionaler skeptischer Kritiker |
| `router/main.py` | Die Cascade-Logik (`route()`) |
| `submission/run.py` | **Wettbewerbs-Entrypoint** — liest `/input/tasks.json`, schreibt `/output/results.json`; schaltet bei knappem Zeitbudget auf Remote-direkt um |
| `entrypoint.sh` | Container-Start: eingebautes Ollama hochfahren, dann `submission.run` |
| `requirements-submission.txt` | Schlanke Abhängigkeiten nur fürs Wettbewerbs-Image |
| `eval/tasks.jsonl` | 64 Testaufgaben (8 je Kategorie) mit Referenzantworten + objektiven Checks (exakte Zahlen, Code-Tests) |
| `eval/judge_llm.py` | Jury-naher LLM-Judge für die Eval (Rubrik wie im Participant Guide) |
| `eval/run_eval.py` | Misst Accuracy (deterministisch + LLM-Judge), Tokens (prompt/completion), Latenzen, Eskalationsraten; schreibt JSON-Reports |
| `demo/app.py` | FastAPI-Demo-App, wrappt `route()` — optionales Video-Hilfsmittel, keine Submission-Pflicht |
| `demo/static/index.html` | Ein-Seiten-UI für die Demo (Vanilla JS, kein Build-Schritt) |

## Konfiguration (Umgebungsvariablen)

Werden im Wettbewerb vom Harness injiziert — nie im Code hardcoden.

| Variable | Standard (nur lokale Entwicklung) | Bedeutung |
|---|---|---|
| `FIREWORKS_API_KEY` | — | **Pflicht** für Remote-Calls — im Wettbewerb vom Harness gestellt, nie den eigenen Key verwenden |
| `FIREWORKS_BASE_URL` | `https://api.fireworks.ai/inference/v1` | Pflicht-Endpoint für alle Fireworks-Calls, wird vom Harness überschrieben |
| `ALLOWED_MODELS` | `gemma-4-26b-a4b-it` | Komma-separierte erlaubte Modell-IDs, wird vom Harness überschrieben |
| `LOCAL_MODEL` | `gemma2:2b` | Eigenes lokales Modell (nicht Teil von `ALLOWED_MODELS`, zählt als 0 Tokens) |
| `REMOTE_MODEL` | erstes Modell aus `ALLOWED_MODELS` | Override für gezieltes Testen gegen ein bestimmtes erlaubtes Modell |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Adresse des lokalen Modells |
| `CONFIDENCE_THRESHOLD` | `70` | Ab wann der lokalen Antwort vertraut wird |
| `USE_CRITIQUE` | `0` | `1` schaltet die skeptische Zweitprüfung ein |

## Lokal ausführen (Eval-Harness, eigene Iteration)

Voraussetzung: [Ollama](https://ollama.com) läuft und das lokale Modell ist
geladen (`ollama pull gemma2:2b`).

```bash
pip install -r requirements.txt

# Fireworks-Key setzen (Windows PowerShell):
#   $env:FIREWORKS_API_KEY="dein-key"
# Linux/macOS:
#   export FIREWORKS_API_KEY="dein-key"

python -m eval.run_eval
```

## Wettbewerbs-Image bauen & lokal testen

Das Docker-Image ist der eigentliche Submission-Artefakt: liest
`/input/tasks.json`, schreibt `/output/results.json` (Participant-Guide-Vertrag,
siehe `submission/run.py`).

**Das Image ist self-contained:** Ollama-Server **und** die Modellgewichte des
lokalen Modells werden zur Build-Zeit eingebacken (`entrypoint.sh` startet
Ollama beim Containerstart). Auf der Judging-VM gibt es kein Host-Ollama und
keinen garantierten Internetzugang außer dem Fireworks-Proxy — das Image darf
sich auf nichts von außen verlassen.

```bash
docker buildx build --platform linux/amd64 -t amd-act2-router --load .

docker run --rm \
  -v "$(pwd)/input:/input" -v "$(pwd)/output:/output" \
  -e FIREWORKS_API_KEY="dein-key" \
  -e FIREWORKS_BASE_URL="https://api.fireworks.ai/inference/v1" \
  -e ALLOWED_MODELS="accounts/fireworks/models/kimi-k2p7-code" \
  amd-act2-router
```

`input/tasks.json` lokal selbst anlegen (Format: `[{"task_id": "t1", "prompt": "..."}]`),
Ergebnis erscheint danach in `output/results.json`. Kein `OLLAMA_BASE_URL`
nötig — der Container nutzt sein eingebautes Ollama (für lokale Entwicklung
per Env-Var weiterhin übersteuerbar).

> **Windows/Git-Bash-Hinweis (verifiziert):** `$(pwd)`-Pfade werden von Git
> Bash manchmal falsch nach Windows übersetzt, wodurch die Mounts leer
> bleiben (`could not read /input/tasks.json`). Funktioniert zuverlässig mit
> nativen Windows-Pfaden und `MSYS_NO_PATHCONV=1` davor, z. B.:
> `MSYS_NO_PATHCONV=1 docker run --rm -v "C:/Pfad/zu/input:/input" -v "C:/Pfad/zu/output:/output" ...`

### Für die Submission bauen & in eine Registry pushen

Die Judging-VM läuft `linux/amd64` — Image muss dieses Manifest enthalten,
sonst Pull-Fehler = 0 Punkte:

```bash
docker buildx build --platform linux/amd64 --tag ghcr.io/faber089/amd-act2-router:latest --push .
```

(Registry-Wahl: GitHub Container Registry `ghcr.io`, nutzt denselben
Faber089-GitHub-Account — Alternative wäre Docker Hub. Login vorher einmalig
mit `docker login ghcr.io` nötig.)

## Demo (optional, nur fürs Presentation-Video — keine Submission-Pflicht)

Eine minimale Web-Demo (`demo/app.py`, FastAPI) wrappt `route()` direkt — sie
zeigt pro Anfrage die gestellte Frage, ob lokal oder remote geantwortet wurde,
die Antwort selbst, den Tokenverbrauch dieser Anfrage sowie eine laufende
Gesamtstatistik (Anteil kostenlos lokal beantworteter Anfragen, Tokens
insgesamt). Für Track 1 nicht Teil der gewerteten Submission (die ist das
Docker-Image oben) — nützlich als Bildmaterial im 5-Minuten-Video.

```bash
docker build -f Dockerfile.demo -t amd-act2-demo .

docker run --rm -p 8000:8000 \
  -e FIREWORKS_API_KEY="dein-key" \
  -e OLLAMA_BASE_URL="http://host.docker.internal:11434/v1" \
  amd-act2-demo
```

Dann `http://localhost:8000` öffnen. Für eine öffentlich erreichbare URL
kann optional [ngrok](https://ngrok.com) genutzt werden:

```bash
ngrok http 8000
```

## Status

Grundgerüst fertig, an den offiziellen Participant Guide (Track 1: General-
Purpose AI Agent, 8 Kategorien, Docker-I/O-Vertrag) angepasst. Modelle,
Routing-Schwellen und der Confidence-Threshold sind ohne Code-Änderung über
Umgebungsvariablen anpassbar.

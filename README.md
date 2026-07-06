# amd-act2-router — Hybrid Token-Efficient Routing Agent

Ein Routing-Agent für den **AMD Developer Hackathon: ACT II**, Track 1
(*Hybrid Token-Efficient Routing Agent*).

Der Agent entscheidet pro Aufgabe selbst, ob er ein **lokales Modell** (Tokens
zählen 0) oder ein **Remote-Modell über die Fireworks AI API** (Tokens zählen)
benutzt. Ziel: möglichst wenige Tokens verbrauchen, ohne unter die
Genauigkeits-Schwelle zu fallen.

## Idee (Cascade-Routing)

1. Jede Aufgabe geht **zuerst an das lokale Modell** (kostet 0 Tokens).
2. Das lokale Modell liefert Antwort **und** eine Selbsteinschätzung
   (`VERTRAUEN: 0–100`).
3. Ein **Judge** liest diese Zahl aus. Liegt sie über der Schwelle, wird die
   lokale Antwort behalten. Optional prüft ein zweiter, skeptischer
   **Kritiker** (ebenfalls lokal) die Antwort noch einmal.
4. Ist die Antwort nicht vertrauenswürdig, wird an **Fireworks eskaliert** —
   nur dann entstehen zählende Tokens.

```
Aufgabe
   │
   ▼
lokales Modell  ──►  Judge (Vertrauen ≥ Schwelle?)  ──► [ja]  lokale Antwort (0 Tokens)
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
| `router/remote_client.py` | Ruft Fireworks AI auf und liest den Tokenverbrauch aus |
| `router/judge.py` | Wertet Selbsteinschätzung aus + optionaler skeptischer Kritiker |
| `router/main.py` | Die Cascade-Logik (`route()`) |
| `eval/tasks.jsonl` | Testaufgaben mit erwarteten Antworten |
| `eval/run_eval.py` | Misst Genauigkeit + Gesamt-Tokenverbrauch |
| `demo/app.py` | FastAPI-Demo-App, wrappt `route()` für die Submission-Pflicht "Demo-Application-URL" |
| `demo/static/index.html` | Ein-Seiten-UI für die Demo (Vanilla JS, kein Build-Schritt) |

## Konfiguration (Umgebungsvariablen)

| Variable | Standard | Bedeutung |
|---|---|---|
| `FIREWORKS_API_KEY` | — | **Pflicht** für Remote-Calls |
| `LOCAL_MODEL` | `gemma2:2b` | Lokales Modell |
| `REMOTE_MODEL` | `accounts/fireworks/models/gpt-oss-120b` | Remote-Modell |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Adresse des lokalen Modells |
| `CONFIDENCE_THRESHOLD` | `70` | Ab wann der lokalen Antwort vertraut wird |
| `USE_CRITIQUE` | `0` | `1` schaltet die skeptische Zweitprüfung ein |

## Lokal ausführen

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

## Mit Docker ausführen

```bash
docker build -t amd-act2-router .

docker run --rm \
  -e FIREWORKS_API_KEY="dein-key" \
  -e OLLAMA_BASE_URL="http://host.docker.internal:11434/v1" \
  amd-act2-router
```

> Hinweis: Aus dem Container heraus ist das Ollama auf dem Host über
> `host.docker.internal` erreichbar, nicht über `localhost`.

## Demo

Eine minimale Web-Demo (`demo/app.py`, FastAPI) wrappt `route()` direkt — sie
zeigt pro Anfrage die gestellte Frage, ob lokal oder remote geantwortet wurde,
die Antwort selbst, den Tokenverbrauch dieser Anfrage sowie eine laufende
Gesamtstatistik (Anteil kostenlos lokal beantworteter Anfragen, Tokens
insgesamt).

```bash
docker build -f Dockerfile.demo -t amd-act2-demo .

docker run --rm -p 8000:8000 \
  -e FIREWORKS_API_KEY="dein-key" \
  -e OLLAMA_BASE_URL="http://host.docker.internal:11434/v1" \
  amd-act2-demo
```

Dann `http://localhost:8000` öffnen. Für eine öffentlich erreichbare URL
(Submission-Pflicht) läuft die Demo lokal weiter und wird per
[ngrok](https://ngrok.com) getunnelt, damit das lokale Modell (Ollama) über
den Container hinweg erreichbar bleibt und "lokal = 0 Tokens" auch in der
Demo real gilt:

```bash
ngrok http 8000
```

**Live-Demo-URL:** _(hier vor der Einreichung eintragen)_

## Status

Funktionierendes Grundgerüst (Übungsphase vor dem Kickoff). Die echten
Track-Aufgaben, erlaubten Modelle und die Scoring-Umgebung werden zum
Hackathon-Start bekanntgegeben; Modelle und Routing-Schwellen sind dann ohne
Code-Änderung über die Umgebungsvariablen anpassbar.

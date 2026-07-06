# MASTERPLAN — AMD Developer Hackathon: ACT II (Solo-Teilnahme Sebastian)

> **Zweck dieses Dokuments:** Vollständiges, eigenständiges Briefing. Wer dieses Dokument liest (Mensch oder KI-Assistent), hat ALLEN nötigen Kontext, um Sebastian bei diesem Hackathon zu unterstützen — ohne Rückfragen zur Ausgangslage. Stand: 5. Juli 2026.

---

## 1. KONTEXT: Wer, was, warum

**Teilnehmer:** Sebastian, Deutschland. Erste Hackathon-Teilnahme überhaupt, **Solo** (kein Team).

**Skill-Profil (wichtig für jede Hilfestellung):**
- Programmiert überwiegend per **Vibe Coding** (KI schreibt den Code, Sebastian steuert und liest mit). Kann Code etwas lesen, aber wenig selbst schreiben.
- Kennt **Ollama** und lokale LLMs aus eigener Nutzung (Windows, CPU-only).
- Erklärungen bitte in **einfachem Deutsch**, ohne unnötigen Fachjargon; Fachbegriffe beim ersten Auftreten kurz erklären.

**Verfügbare Zeit:** ca. **12 Stunden pro Tag** während der Hackathon-Woche.

**Ziele (in dieser Reihenfolge):**
1. Maximal viel über AI-Engineering lernen (Agents, LLM-APIs, Evaluation, Docker)
2. Ein vorzeigbares GitHub-Portfolio-Projekt
3. Platzierung/Preis = Bonus, nicht Hauptziel

**Hardware/Setup (verifiziert am 5.7.):** Windows 11, CPU-only (keine dedizierte GPU — irrelevant, da der Hackathon komplett cloudbasiert ist). Installiert: Python 3.11, Git, Docker Desktop, Ollama, VS Code, Claude Code.

**Anmeldestatus:** ✅ Seit **1. Juli 2026** angemeldet (lablab.ai-Enrollment + AMD AI Developer Program) — also VOR dem Credit-Cutoff (2. Juli) → Hackathon-Credits ab Tag 1 verfügbar.

---

## 2. DAS EVENT: Alle Fakten

| Fakt | Detail |
|---|---|
| Name | AMD Developer Hackathon: ACT II |
| Veranstalter | lablab.ai mit AMD und NativelyAI; Technologie-Partner: Google DeepMind (Gemma), Fireworks AI, Native.Builder |
| Format | Komplett online, kostenlos, Solo erlaubt |
| Zeitraum | **6.–11. Juli 2026** |
| Submission-Deadline | **11. Juli 2026, 15:00 UTC = 17:00 deutsche Zeit** |
| Preisgeld | $20.000+ Haupt-Pool + $6.000 „Best Use of Gemma 4"-Sonderpreis (trackübergreifend) + Natively AI Challenge (Native.builder-Zugang) — offiziell laut Kickoff-Mail 6.7. |
| Infrastruktur | AMD Developer Cloud (AMD-GPUs, z. B. MI300X), ROCm, Fireworks AI API |
| Credits | $50 Fireworks-API-Credits für alle Teilnehmer + $100 AMD-Cloud- und $50 Fireworks-Credits für neue ADP-Mitglieder; zusätzliche Hackathon-Credits werden am Start verteilt |
| Event-Seite | https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii |
| Kommunikation | lablab.ai-Discord (Orga) + AMD-Discord (Technik-Support) — Task-Details kommen dort |

**Die drei Tracks:**
1. **Hybrid Token-Efficient Routing Agent** (Beginner, AI-Agent-Track) — GEWÄHLT, Details unten
2. **Video Captioning** (Beginner) — Pipeline captioned feste Videoclips (30 s–2 min) in 4 Stilen: formal, sarkastisch, humorous-tech, humorous-non-tech; Bewertung per LLM-Judge; Fallback-Option
3. **Unicorn Track** (alle Level) — freies Startup-Projekt, Jury-Bewertung (Kreativität, Originalität, Vollständigkeit, AMD-Nutzung, Marktpotenzial); als Solo-Erstling bewusst NICHT gewählt

---

## 3. GEWÄHLTER TRACK: Track 1 — "General-Purpose AI Agent" (offizielles Participant Submission Guide PDF, 6.7. abends erhalten)

**🎯 Das ist jetzt die maßgebliche, vollständige Quelle** — ersetzt alle vorherigen Vermutungen aus Stream-Folien/Kickoff-Mail. PDF: "Participant Guide: AMD Developer Hackathon (ACT II)", `C:\Users\iq\Downloads\Participant Guide_ AMD Developer Hackathon (ACT II).pdf`.

**Was gebaut wird:** Ein Agent, der Aufgaben aus 8 Kategorien via Fireworks-AI-Modelle so effizient wie möglich löst:

| # | Kategorie | Beschreibung |
|---|---|---|
| 1 | Factual knowledge | Konzepte, Definitionen, Funktionsweisen erklären |
| 2 | Mathematical reasoning | Mehrstufige Arithmetik, Prozentrechnung, Textaufgaben, Projektionen |
| 3 | Sentiment classification | Sentiment labeln + Klassifikation begründen |
| 4 | Text summarisation | Texte auf Format-/Längenvorgabe verdichten |
| 5 | Named entity recognition | Entitäten extrahieren/labeln (Person, Org, Ort, Datum) |
| 6 | Code debugging | Bugs in Code-Schnipseln finden + korrigierte Version liefern |
| 7 | Logical / deductive reasoning | Constraint-Rätsel, alle Bedingungen müssen erfüllt sein |
| 8 | Code generation | Korrekte, sauber strukturierte Funktionen aus einer Spec schreiben |

**✅ Erlaubte Modelle (`ALLOWED_MODELS`, alle über Fireworks, NICHT selbst hostbar):**
`minimax-m3`, `kimi-k2p7-code`, `gemma-4-31b-it`, `gemma-4-26b-a4b-it`, `gemma-4-31b-it-nvfp4`

**🔑 Auflösung der lokal/remote-Frage:** Diese 5 Modelle sind ALLE Remote-Optionen über Fireworks — keins davon ist zum Selbst-Hosten gedacht. "Lokal = 0 Tokens" bezieht sich auf UNSER eigenes, separat mitgebrachtes lokales Modell (unser bisheriges `gemma2:2b` via Ollama bleibt also die richtige Wahl für die kostenlose Stufe!). `nvfp4` ist nur eine Fireworks-seitige Quantisierungsvariante — kein NVIDIA-Hardware-Erfordernis für uns.

**Submission = Docker-Image mit festem I/O-Vertrag (NICHT die Demo-App/HTTP-Server, die wir gebaut haben!):**
- Container liest beim Start `/input/tasks.json`: `[{"task_id": "t1", "prompt": "..."}, ...]`
- Container schreibt vor Exit `/output/results.json`: `[{"task_id": "t1", "answer": "..."}, ...]`
- Exit-Code 0 = Erfolg, ungleich 0 = Fehler
- **Kein HTTP-Server nötig für Track 1** — reiner Batch-Lauf. Unsere Demo-App (Abschnitt 11) ist dafür NICHT das gewertete Artefakt, bleibt aber nützlich fürs Presentation-Video.

**Pflicht-Umgebungsvariablen (vom Harness zur Laufzeit injiziert, NICHT hardcoden):**
| Variable | Bedeutung |
|---|---|
| `FIREWORKS_API_KEY` | vom Harness gestellter Key — NICHT den eigenen verwenden |
| `FIREWORKS_BASE_URL` | Pflicht-Endpoint für ALLE Fireworks-Calls — Calls daran vorbei werden nicht gezählt/ungültig |
| `ALLOWED_MODELS` | Komma-separierte erlaubte Modell-IDs — zur Laufzeit auslesen, NICHT hardcoden |

**Regeln (hart, alle bestätigt im PDF):**
- Container muss innerhalb **60 Sekunden** startklar sein
- Antwortzeit pro Anfrage **unter 30 Sekunden**
- **Maximale Gesamtlaufzeit: 10 Minuten**
- **Alle Antworten müssen auf ENGLISCH sein** — unsere bisherigen deutschen Prompt-Vorlagen ("Frage:... ANTWORT:... VERTRAUEN:...") müssen auf Englisch umgestellt werden!
- Nur Modelle aus `ALLOWED_MODELS` erlaubt, sonst ungültig
- `/output/results.json` muss gültiges JSON sein, sonst 0 Punkte
- Keine hartkodierten/gecachten Antworten — Auswertung nutzt ungesehene Prompt-Varianten
- **Image-Größe (komprimiert) max. 10 GB**
- **Rate-Limit: 10 Submissions/Stunde/Team**
- **Image-Architektur: muss `linux/amd64`-Manifest haben**, sonst Pull-Fehler = 0 Punkte. Docker Desktop auf Windows baut i. d. R. schon amd64, aber sicherheitshalber explizit bauen: `docker buildx build --platform linux/amd64 --tag <image>:latest --push .`
- **Muss in eine öffentliche Container-Registry gepusht werden** (GitHub Container Registry oder Docker Hub) — zusätzlich zum GitHub-Repo, NEUER Schritt, den wir noch nicht gemacht haben

**Scoring (zweistufig, jetzt offiziell):**
1. **Accuracy-Gate:** ein LLM-Judge bewertet jede Antwort gegen die erwartete Absicht (nicht exaktes String-Matching — etwas Spielraum für freie Formulierung). Unter der Schwelle (Zahl nicht im PDF genannt) = vom Leaderboard ausgeschlossen.
2. **Tokeneffizienz:** wer das Gate besteht, wird aufsteigend nach vom Judging-Proxy gezählten Gesamt-Tokens gerankt. Weniger Tokens = besserer Rang.

**Bonus-Chance:** Sonderpreis „Best Use of Gemma 4" ($6.000-Pool, trackübergreifend) — 3 der 5 erlaubten Modelle sind Gemma-4-Varianten, Bonus ist also direkt erreichbar, einfach eines davon als Remote-Modell nutzen und im README dokumentieren.

**Warum dieser Track weiterhin richtig für Sebastian:** Objektives, automatisiertes Scoring (kein Jury-Pitch), passt zu seiner Ollama-Vorerfahrung, und das PDF bestätigt: unser bereits gebauter Cascade-Router (lokal zuerst, Fireworks bei Bedarf) ist architektonisch weiterhin goldrichtig — nur der Container-Vertrag (I/O-Dateien statt Web-Server) und ein paar Konfigurationsdetails müssen angepasst werden.

---

## 4. WAS GEBAUT WIRD: Architektur

**Projekt:** `amd-act2-router` — ein Cascade-Router. Öffentliches GitHub-Repo, MIT-Lizenz.

```
amd-act2-router/
├── router/
│   ├── local_client.py    # spricht lokales Modell (OpenAI-kompatible API, Tokens = 0)
│   ├── remote_client.py   # spricht Fireworks AI (OpenAI-kompatibel, Tokens zählen!)
│   ├── judge.py           # Selbst-Check: ist die lokale Antwort gut genug?
│   └── main.py            # Cascade-Logik
├── eval/
│   ├── tasks.jsonl        # Übungsaufgaben mit Soll-Lösungen (eigenes Format)
│   └── run_eval.py        # misst Accuracy + Remote-Tokens pro Lauf
├── submission/             # NEU (noch zu bauen) — der eigentliche Wettbewerbs-Entrypoint
│   └── run.py              # liest /input/tasks.json, ruft route() pro Task auf, schreibt /output/results.json, exit 0/1
├── demo/                   # Bonus/Video-Material, NICHT das gewertete Artefakt
│   ├── app.py              # FastAPI-Demo, wrappt route() für die Presentation
│   └── static/index.html
├── Dockerfile              # Wettbewerbs-Image: submission/run.py als Entrypoint (noch anzupassen)
├── Dockerfile.demo         # separates Image nur für die Video-Demo
├── README.md               # Setup, Architektur, Eval-Ergebnisse
└── LICENSE                 # MIT
```

**Wichtiger Architektur-Shift ggü. der ursprünglichen Annahme:** Das eigentliche Wettbewerbs-Docker-Image ist ein **Batch-Container** (liest eine Task-Datei, schreibt eine Ergebnis-Datei, beendet sich) — kein Web-Server. Die Demo-App (FastAPI/ngrok) bleibt nur fürs Presentation-Video sinnvoll, ist aber nicht das, was der Judging-Harness tatsächlich aufruft.

**Cascade-Logik (Kernidee):**
1. Aufgabe rein → **immer zuerst lokales Modell** (kostet 0)
2. **Judge** prüft die lokale Antwort (Selbstbefragung / Format-Check / Plausibilität)
3. Judge unsicher → Eskalation an Fireworks mit **maximal kurzem Prompt** und begrenztem `max_tokens`
4. Tokens werden geloggt; Eval-Skript liefert nach jedem Lauf: Accuracy % + Remote-Tokens gesamt

**Geplante Iterationen:** v1 = Cascade wie oben → v2 = zusätzlich Schwierigkeits-Klassifikation VOR der ersten Antwort (Heuristiken oder Mini-Modell), um lokale Fehlversuche bei offensichtlich schweren Aufgaben zu sparen. Eiserne Regel: **Jede Änderung wird gegen die Eval gemessen; nur behalten, was die Zahlen verbessert.**

**Technischer Schlüssel-Fakt:** Ollama UND Fireworks bieten OpenAI-kompatible APIs → derselbe Python-Code (`openai`-Paket) spricht beide, nur `base_url`/`api_key` unterscheiden sich.

---

## 5. ZEITPLAN Tag für Tag

| Tag | Phase | Inhalt | Fertig-Kriterium |
|---|---|---|---|
| **So 5.7.** | Vorbereitung | 0.1 Accounts checken (lablab-Dashboard, Fireworks-API-Key, beide Discords) · 0.2 Umgebung (Docker-hello-world, 2 Ollama-Modelle in 2 Größen, GitHub-Repo) · 0.3 Docker-Crashkurs 90 min · 0.4 LLM-API-Crashkurs 90 min (gleicher Code lokal + remote, Tokens auslesen) · 0.5 **Kernübung: kompletten Übungs-Router bauen** (4–6 h) · 0.6 abends 30 min DeepLearning.AI | `docker run` lässt Übungs-Eval durchlaufen und liefert Accuracy + Tokens |
| **Mo 6.7.** | Kickoff | Vormittags Kickoff verfolgen, `kickoff-notizen.md` anlegen: Aufgaben? erlaubte Modelle? Specs der Scoring-Umgebung? Accuracy-Schwelle? Submit-Prozess? · Hackathon-Credits einlösen · AMD-Cloud-Zugang einrichten · Nachmittags **2 Baselines**: alles-lokal (Tokens 0, Accuracy?) und alles-remote (Accuracy-Maximum, Token-Maximum) | Beide Baseline-Zahlen dokumentiert |
| **Di 7.7.** | Iteration | **`submission/run.py` bauen** (liest `/input/tasks.json`, ruft `route()` auf, schreibt `/output/results.json`) · `config.py` auf `ALLOWED_MODELS` umstellen (kein hartkodierter Modellname mehr) · Prompts auf Englisch umstellen · `eval/tasks.jsonl` um Beispiele aus allen 8 Kategorien erweitern | `submission/run.py` läuft lokal gegen Beispiel-`tasks.json`, Output ist valides JSON |
| **Mi 8.7.** | Iteration | Router v1 (Cascade) auf die echten 8 Kategorien tunen: Judge-Varianten, Eskalations-Schwelle, Prompt-Kürzung, `max_tokens` · Dockerfile fürs Wettbewerbs-Image anpassen (`--platform linux/amd64`) · Demo-App (Abschnitt 11) nur noch optional, falls Zeit übrig | Messbar besser als Di, Docker-Image baut mit amd64-Manifest |
| **Do 9.7.** | Iteration | v2 (Vorab-Klassifikation) testen · Gemma-4-Bonus einbauen (eines der 3 Gemma-4-Modelle als Remote nutzen) · Container-Registry einrichten + ersten Push testen (ghcr.io oder Docker Hub) · **abends Feature-Freeze**, Git-Tag `v1.0` | Beste Version eingefroren, Image erfolgreich in Registry gepusht |
| **Fr 10.7.** | Submission-Paket | Container von frischem Klon durchtesten (10-Min-/30s-/60s-Limits im Blick) · README (Architektur + Ergebnistabelle) · Presentation-Video **max. 5 min, MP4, max. 300 MB** (OBS, danach Dateigröße prüfen!) · finalen Image-Push in die Registry | Alles Material fertig, Video ≤ 300 MB bestätigt, Image öffentlich pullbar |
| **Sa 11.7.** | Abgabe | Alle lablab.ai-Felder ausfüllen, **spätestens 14:00 deutscher Zeit** submitten (Deadline 17:00), Bestätigung screenshotten | Submission bestätigt |

---

## 6. SUBMISSION-PFLICHTEN (jetzt Track-1-spezifisch bestätigt, Participant Guide PDF)

**Für Track 1 offiziell bestätigt — Demo-Application-URL ist NICHT Teil der Track-1-Pflichten** (das war die offene Frage aus der Deliverables-Folie — das Docker-Image-Kapitel im PDF erwähnt an keiner Stelle eine Live-URL für Track 1; nur Track 3 hat ein optionales "Live demo / hosted URL"-Feld):

- [x] **Docker-Image, öffentlich in einer Container-Registry** (GitHub Container Registry oder Docker Hub) — NEU, noch nicht erledigt, siehe Abschnitt 8
- [x] **Presentation-Video, ≤ 5 min, MP4, ≤ 300 MB**
- [x] **GitHub-Repo-Link** — öffentlich mit README (Setup + Nutzung, muss lauffähig sein)
- [x] **Product description** (Kurz-/Langbeschreibung, im Einreichungsformular auf lablab.ai)
- [ ] Original & MIT-kompatibel, keine API-Keys im Code (Umgebungsvariablen — bereits über `.gitignore`/Env-Vars sichergestellt)
- [ ] Einreichung über lablab.ai-Plattform vor Deadline

**Technische Pflicht-Constraints fürs Docker-Image (aus dem PDF, s. Abschnitt 3):** `linux/amd64`-Manifest, ≤10 GB komprimiert, Container startklar in 60s, Antwort pro Task <30s, Gesamtlaufzeit <10 Min, `/output/results.json` muss valides JSON sein, alle Antworten auf Englisch, nur `ALLOWED_MODELS` verwenden, alle Fireworks-Calls über `FIREWORKS_BASE_URL`.

Referenz-Guide (allgemeine Tipps, nicht Track-1-spezifisch): https://lablab.ai/how-to-be-successful-at-the-hackathon

---

## 7. LERN-REGELN (damit Sebastian wirklich lernt, nicht nur zuschaut)

Jede KI, die Sebastian unterstützt, hält sich an diese vier Regeln:
1. **Erst beschreiben lassen, dann bauen:** Sebastian formuliert vor jedem Baustein in 2–3 Sätzen, was gebaut wird und wie es grob funktioniert. Kann er das nicht, erst erklären, dann bauen.
2. **Jede Datei erklären:** Nach jedem Baustein auf Wunsch Zeile für Zeile in einfachem Deutsch erklären. Weiter erst, wenn er es einem Freund erklären könnte.
3. **Sebastian tippt die Kommandos selbst** (docker, git, python) — die KI diktiert, er führt aus.
4. **Abend-Reflexion:** 3 gelernte Dinge + 1 offene Frage notieren (Obsidian); die offene Frage wird am Folgetag zuerst geklärt.

Weitere Arbeitsprinzipien:
- Keine Änderung ohne Eval-Messung davor/danach
- Bei Zeitnot: Scope halbieren — eine saubere v1-Submission schlägt eine unfertige v2
- NICHT lernen/bauen: ROCm-/GPU-Programmierung im Detail (fertige Endpoints reichen), Fine-Tuning (erlaubt, aber falsche Baustelle in 5 Tagen)
- **Klargestellt (Participant Guide PDF):** Für Track 1 ist **kein** Web-Frontend/Demo-URL nötig — die Submission ist ein Batch-Docker-Image (s. Abschnitt 3/6). Die bereits gebaute Demo-App (Abschnitt 11) bleibt trotzdem sinnvoll fürs Presentation-Video, ist aber keine Pflicht-Checkbox mehr — kein weiterer Aufwand hier nötig (kein Hosting/ngrok-Zwang)

---

## 8. OFFENE PUNKTE (werden am Kickoff geklärt → hier nachtragen!)

**KORREKTUR 6.7. (per offizieller Kickoff-Mail von lablab.ai, heute erhalten):** Die frühere Annahme „Kickoff-Inhalte kommen erst morgen (7.7.)" war **falsch** — es gab schlicht noch keine Veröffentlichung, weil der Kickoff-Stream erst **heute Abend, 18:00 CET** läuft (danach 19:00 CET Discord-Q&A auf lablab.ai-Discord). **Phase 1 (Kickoff) findet also wie ursprünglich geplant HEUTE (6.7.) statt, keine Tagesverschiebung.** Baselines (Schritt 1.2) und `kickoff-notizen.md` entsprechend heute Abend/danach angehen, nicht erst morgen.

Zusätzlich aus der Kickoff-Mail bestätigt/neu:
- Prize Pool offiziell **$20.000+** (Tabelle in Abschnitt 2 unten korrigiert von $21.000)
- Gemma-Bonus heißt **„Best Use of Gemma 4"**, $6.000-Pool, **trackübergreifend** (nicht $1.000 exklusiv für Track 1 — Abschnitt 3 korrigiert)
- Neue Bonus-Challenge „Natively AI Challenge" (Zugang zu Native.builder) — für Track 1 nicht nötig, kein Handlungsbedarf
- Workshop „Build Your First Lightweight App with Native.Builder": **Di 7.7., 18:00 CET**, lablab.ai-Discord — optional, betrifft Track 1 nicht direkt
- **Offene Frage für den Discord-Q&A heute 19:00 CET:** Braucht Track 1 wirklich eine live erreichbare Demo-URL, oder reicht ein einfacher Link (Repo/Video)? Antwort hier nachtragen. Der Bau der Demo-App (Abschnitt 11) läuft unabhängig davon weiter — lohnt sich so oder so fürs Demo-Video —, nur der Hosting-Aufwand (ngrok, siehe Abschnitt 11) könnte sich dadurch erübrigen.
- **Nach dem Kickoff prüfen — TOON-Format für Tokensparen:** Falls die echten Aufgaben strukturierte/tabellarische Eingabedaten enthalten (Listen, mehrere gleich aufgebaute Datensätze), die an Fireworks eskaliert werden: TOON (Token-Oriented Object Notation) statt JSON prüfen — spart laut aktuellen Benchmarks 30–60 % Tokens, teils sogar mit besserer Genauigkeit ([toon-format/toon](https://github.com/toon-format/toon)). Nur einbauen, wenn Eval-Vergleich (vorher/nachher) Tokens senkt UND Accuracy nicht verschlechtert. Bei reinen Fließtext-Fragen (wie aktuell) irrelevant.

**Stand Ende 6.7. — Grundgerüst fertig & getestet (Ordner `amd-act2-router/`):**
- ✅ Cascade-Router läuft (lokal zuerst → bei Unsicherheit Fireworks), komplett über Umgebungsvariablen konfigurierbar (`router/config.py`)
- ✅ Eval-Harness misst Genauigkeit + Tokenverbrauch (`eval/run_eval.py`, 13 Übungsaufgaben)
- ✅ Containerized — Docker-Image baut, Container erreicht Host-Ollama via `host.docker.internal` (verifiziert)
- ✅ README, MIT-LICENSE, .gitignore (schützt vor Key-Leak), requirements.txt
- ✅ **GitHub-Push erledigt:** Repo live unter https://github.com/Faber089/amd-act2-router (aktuell **privat** — vor Submission auf öffentlich stellen). Account-Diskrepanz gelöst: Sebastians echter GitHub-Account ist **Faber089**; der lokal via `git`/`gh` angemeldete Account (Sebastian0890) hat keinen Zugriff auf Faber089-Repos → Pushes über die Kommandozeile schlagen deshalb fehl. **Für alle künftigen Commits: Push über GitHub Desktop**, nicht über CLI.
- Projektordner lokal auch gespiegelt unter `C:\Users\iq\Documents\GitHub\amd-act2-router` (das ist die per GitHub Desktop verbundene Kopie).
- 🔧 **Modellwahl aktuell:** lokal `gemma2:2b` (schnell), remote-Default jetzt `gemma-4-26b-a4b-it` (aus `ALLOWED_MODELS`, ersetzt den erfundenen `gpt-oss-120b`). Kritiker (`USE_CRITIQUE`) standardmäßig AUS (eskalierte in der Übung zu viel).
- ✅ **Docker-Wettbewerbs-Image End-zu-Ende getestet (6.7. abends):** `docker build` + `docker run` mit echten `/input`/`/output`-Mounts, 3 Testaufgaben (Faktenwissen, Code-Generierung, Mathe) alle korrekt lokal beantwortet, Exit-Code 0, valides JSON. Windows/Git-Bash-Pfad-Stolperstein gefunden + im README dokumentiert (`MSYS_NO_PATHCONV=1` + native Windows-Pfade nötig, `$(pwd)` funktioniert nicht zuverlässig).
- ✅ **Regex-Bug behoben:** `ANSWER`-Extraktion in `judge.py` brach am ersten Zeilenumbruch ab — mehrzeiliger Code wurde dadurch fast komplett abgeschnitten. Nach dem Fix + Prompt-Klarstellung für Code-Aufgaben: **Eval-Accuracy 100 % (16/16)** auf den eigenen Testaufgaben, 0 Tokens.
- ⚠️ **Bekannte Lücke, jetzt mit echtem Key bestätigt (6.7. spät):** Mit Sebastians echtem Fireworks-Key getestet (`.env`, `config.py` lädt sie jetzt automatisch via `python-dotenv`) — **keines der 5 Hackathon-Modelle ist auf dem Account sichtbar/deployt**. `client.models.list()` zeigt nur 7 generische Katalog-Modelle (`gpt-oss-120b`, `glm-5p1/p2`, `deepseek-v4-pro`, `kimi-k2p6/p5`, `flux-1-schnell-fp8`) — keins davon `gemma-4-*`, `minimax-m3` oder `kimi-k2p7-code`. Bestätigt: die Hackathon-Modelle werden erst zur Laufzeit vom Harness freigeschaltet, für die Submission kein Problem, lokal aber weiterhin nicht mit den echten Modellen testbar.
- ⚠️ **Neuer Fund beim echten Test:** Ein voller Eskalations-Roundtrip mit `gpt-oss-120b` (dem einzigen aktuell erreichbaren größeren Modell) funktionierte technisch einwandfrei (Antwort "Paris" korrekt) — aber **45 Completion-Tokens für eine Ein-Wort-Antwort**, weil `gpt-oss-120b` ein Reasoning-Modell mit unsichtbaren Denk-Tokens ist, die trotzdem gezählt werden. Falls eines der echten erlaubten Modelle ebenfalls ein Reasoning-Modell ist: unbedingt prüfen, ob die API einen Parameter zum Abschalten/Reduzieren des Reasoning-Aufwands bietet (oft `reasoning_effort` o. Ä.) — das wäre ein sehr großer Tokeneffizienz-Hebel, den reine Prompt-Kürze allein nicht löst.

**✅ AUFGELÖST (Participant Guide PDF, 6.7. abends erhalten):** Aufgaben-Kategorien, erlaubte Modelle, Docker-I/O-Vertrag, Umgebungsvariablen, Laufzeit-/Größen-Limits und der zweistufige Scoring-Mechanismus sind jetzt alle in Abschnitt 3 dokumentiert. Das PDF ist die vollständigste bisher erhaltene Quelle — deutlich detaillierter als Stream-Folien oder Kickoff-Mail.

**Jetzt noch offen (fürs Q&A oder Discord, falls Zweifel bleiben):**
- [ ] Exakte Zahl der Accuracy-Gate-Schwelle (PDF nennt nur den Mechanismus: LLM-Judge, keine konkrete Prozentzahl)
- [ ] Genaue Anzahl/Beispiele der Test-Prompts pro Kategorie (PDF sagt bewusst: "Exact evaluation inputs are intentionally omitted" — müssen selbst Testfragen pro der 8 Kategorien bauen)
- [ ] Container-Registry-Wahl: GitHub Container Registry (ghcr.io, nutzt denselben Faber089-GitHub-Account) vs. Docker Hub — noch zu entscheiden und einzurichten
- [ ] Details AMD-Cloud-GPU-Zugang + zusätzliche Hackathon-Credits (falls für Fine-Tuning/Entwicklung relevant — für reines Fireworks-Routing evtl. nicht nötig)

**✅ Code-Änderungen umgesetzt (6.7. abends) und lokal verifiziert (ohne Docker, Daemon lief nicht — Ollama war verfügbar):**
- ✅ **`submission/run.py` (neu):** liest `/input/tasks.json`, ruft `router.main.route()` pro Task auf, schreibt `/output/results.json`, exit 0/1. Enthält zusätzlich einen Warm-up-Call vor der Aufgaben-Schleife (behebt einen echten Cold-Start-Bug: erster Ollama-Call brauchte >30s und schlug fehl, bevor das Modell im Speicher war — mit Warm-up läuft's in ~2s)
- ✅ **`router/config.py`:** `ALLOWED_MODELS` wird jetzt aus der Umgebungsvariable gelesen (Komma-Liste), `REMOTE_MODEL` fällt auf das erste erlaubte Modell zurück statt auf den erfundenen `gpt-oss-120b`-Default
- ✅ **Prompts auf Englisch umgestellt** (`router/local_client.py`: ANSWER/CONFIDENCE statt ANTWORT/VERTRAUEN; `router/judge.py`: VERDICT/CORRECT/INCORRECT statt URTEIL/KORREKT/FEHLERHAFT)
- ✅ **Dockerfile angepasst:** `submission/run.py` ist jetzt der Standard-CMD; README dokumentiert `--platform linux/amd64`-Build + Registry-Push (ghcr.io vorgeschlagen, nutzt Faber089-Account)
- ✅ **`eval/tasks.jsonl` erweitert:** 16 Aufgaben, 2 pro Kategorie, komplett auf Englisch. Eval-Lauf: **68,8 % Accuracy (11/16), 0 Remote-Tokens** (alles lokal beantwortet, nie eskaliert)

**🐛 Konkreter Befund aus dem Eval-Lauf, noch zu beheben (Iterationstag):** Bei **Code Debugging** und **Code Generation** (4 von 16 Aufgaben, alle "FALSCH" im groben Substring-Check) beschreibt `gemma2:2b` den Fehler/die Funktion nur in Prosa, statt den tatsächlichen korrigierten/neuen Code zu liefern — das aktuelle generische Prompt-Format ("ANSWER: ...") lädt nicht klar genug dazu ein, echten Code zurückzugeben. Für diese 2 Kategorien braucht der Prompt vermutlich eine explizite Zusatzanweisung ("return the actual corrected code, not just an explanation"). Noch nicht behoben — für morgen (Iterationstag) vorgemerkt.

**Optimale lokale Modellgröße (aus der Übung, weiterhin gültig):** 0,5B (qwen2.5) zu schwach — hält Format nicht ein, inhaltlich falsch. 6,6B (qwen3.5) inhaltlich zuverlässig, aber auf CPU zu langsam (~30 Min für 13 Testfragen — würde das 10-Minuten-Gesamtlimit sprengen). 2B (gemma2:2b) ist schnell (~2s/Antwort, passt gut ins 30s-Pro-Task-/10-Min-Gesamtlimit) UND hält das Format ein, ABER: liefert bei schweren Fragen selbstbewusst falsche Antworten und eskaliert nicht — bleibt der Kern-Zielkonflikt beim Judge-Design.

**🔑 Kern-Erkenntnis aus der Übung (5./6.7.):** Reines Selbst-Vertrauen des lokalen Modells als Judge ist nicht robust genug — ein Modell kann überzeugt falsch liegen. Für die finale Lösung braucht es vermutlich eine zusätzliche Absicherung, z. B.: Aufgaben-Typ-Erkennung vor der Antwort (z. B. Rechenaufgaben mit großen Zahlen grundsätzlich eskalieren), Selbst-Konsistenz-Check (Frage zweimal anders formuliert stellen, bei Widerspruch eskalieren), oder härtere Heuristiken statt nur einer Vertrauens-Zahl vom Modell selbst.

**✅ Umgesetzt (6.7. spät, nach Recherche zu tokeneffizientem Routing — Quellen: UCCI-Paper arxiv 2605.18796 zu kalibrierten Cascade-Schwellen, Concise-CoT arxiv 2401.05618):**
- **Selbst-Konsistenz-Check** (`USE_SELFCHECK=1`, default an): kurze vertrauenswürdige lokale Antworten (≤80 Zeichen) werden ein zweites Mal lokal erfragt — kostenlos, da lokale Tokens = 0. Widerspruch → Eskalation. **Eval-Beleg:** Kalibrierungstabelle zeigte 3 von 5 Fehlern bei Confidence=100 (Schwelle allein kann die nie fangen); mit Selbst-Check eskalieren alle 6 schweren Fehlaufgaben korrekt, nur 2 unnötige Eskalationen bei richtigen Antworten. Kern-Insight: **lokale Rechenzeit ist im Scoring gratis** — beliebig viele lokale Gegenchecks kosten nichts außer Latenz (~2s/Task, Budget 30s).
- **Remote-Kappung:** `REMOTE_MAX_TOKENS` (default 512) + Kürze-Anweisung im Eskalations-Prompt ("Answer concisely and directly, no preamble"). Knappe Antworten sparen Completion-Tokens und verbessern laut Concise-CoT-Forschung bei großen Modellen teils sogar die Accuracy.
- **Remote-Fehler-Fallback:** schlägt die Eskalation fehl, wird die (unsichere) lokale Antwort geliefert statt `""` — leer fällt beim Accuracy-Gate garantiert durch, lokal hat eine Chance.
- **Kalibrierungs-Tabelle in der Eval** (`run_eval.py`): zeigt pro Confidence-Bereich, wie oft die lokale Antwort korrekt war → `CONFIDENCE_THRESHOLD` datenbasiert wählen statt raten.
- **Eval verschärft:** 22 Aufgaben (16 normale + 6 schwere: große Multiplikation, obskures Wissen, harte Logik). Stand: 72,7 % lokal-only — die 6 schweren würden auf dem echten Harness eskalieren und vom großen Modell sehr wahrscheinlich korrekt beantwortet (lokal nicht testbar wegen der bekannten Modell-ID-Lücke, s. o.).

## 9. SUPPORT-WEGE

| Problem | Anlaufstelle |
|---|---|
| Credits/Zugänge | AMD-Discord, Support-Channel |
| Track-Regeln unklar | lablab.ai-Discord, Track-1-Channel — früh fragen, nicht raten |
| Technik festgefahren | KI-Assistent mit Fehlermeldung + Kontext füttern |

## 10. QUELLEN

- Offizielle Event-Seite: https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii
- AMD-Ankündigung: https://www.amd.com/en/developer/resources/technical-articles/2026/build-across-the-ai-stack--join-the-amd-x-lablab-ai-hackathon-.html
- Fireworks-Doku: https://docs.fireworks.ai · ROCm-Doku: https://rocm.docs.amd.com · Gemma: https://ai.google.dev/gemma
- "How to be successful at the hackathon"-Guide (von der Deliverables-Folie im Kickoff-Stream verlinkt): https://lablab.ai/how-to-be-successful-at-the-hackathon
- Kickoff-E-Mail von lablab.ai, erhalten 6.7.2026, 18:00 CET Stream angekündigt („AMD AI DEVELOPER HACKATHON ACT II KICKS OFF TODAY")
- **"Participant Guide: AMD Developer Hackathon (ACT II)" (PDF, 6.7.2026 abends erhalten)** — vollständigste offizielle Quelle, Track-1-Details in Abschnitt 3 wörtlich daraus übernommen. Lokal: `C:\Users\iq\Downloads\Participant Guide_ AMD Developer Hackathon (ACT II).pdf`

---

## 11. DEMO-APP (jetzt: optionales Video-Hilfsmittel, KEINE Submission-Pflicht mehr)

**Update (Participant Guide PDF, 6.7. abends):** Für Track 1 ist die Demo-Application-URL **keine Pflicht** — die Submission ist ein Batch-Docker-Image (Abschnitt 3/6). Diese Demo-App bleibt trotzdem nützlich, um im 5-Minuten-Presentation-Video zu zeigen, wie der Router live entscheidet (lokal vs. Fireworks) — aber kein Hosting-/ngrok-Zwang mehr, kann für einen kurzen Screen-Recording-Ausschnitt auch einfach lokal laufen, ohne öffentlich erreichbar sein zu müssen.

**Ursprüngliche Begründung (nicht mehr Pflicht, aber Kontext):** Die Submission-Checkliste hatte anfangs für **alle Tracks** eine Demo-Application-URL vermuten lassen. Das Router-Projekt war zuvor ein reines CLI-/Batch-Eval-Tool ohne Web-Anbindung — diese Lücke wurde vorsorglich geschlossen, bevor klar war, dass sie für Track 1 nicht gebraucht wird.

**Entscheidung:** Erst selbst bauen (bekannter Stack, garantiert die Pflicht) — Native.builder-Version ist optionaler Stretch-Goal für den „Natively AI Challenge"-Bonus, kein kritischer Pfad. Hosting: eigener Rechner + ngrok-Tunnel (Ollama bleibt lokal → „lokal = 0 Tokens" bleibt für die Demo echt wahr).

**Stack:** FastAPI + eine statische `index.html` (Vanilla-JS `fetch()`, kein Build-Schritt) — schnellster Weg ohne neue Denkmodelle, ruft `router.main.route()` direkt auf (keine Duplikat-Logik).

**Neue/geänderte Dateien in `amd-act2-router/`:**
- `demo/app.py` — FastAPI-App. `GET /` liefert `index.html`, `POST /ask {question}` ruft `route(question, verbose=False)` auf (Rückgabe: `(answer, tokens, source)`), hängt an In-Memory-Historie an, gibt JSON inkl. laufender Gesamtwerte zurück.
- `demo/static/index.html` — Texteingabe + Submit, Ergebnisbereich, Statistik-Fußzeile.
- `requirements.txt` — ergänzt um `fastapi`, `uvicorn[standard]`.
- `Dockerfile.demo` (neu, Projekt-Root) — gleiche COPY-Schritte wie das bestehende `Dockerfile`, CMD auf `uvicorn demo.app:app --host 0.0.0.0 --port 8000`. Bestehendes `Dockerfile` (Eval-Pfad) bleibt unangetastet.
- `README.md` — neuer Abschnitt „Demo": was sie zeigt, Build-/Run-Befehle, ngrok-Hinweis, Platzhalter für die finale URL.

**UI zeigt pro Anfrage:** gestellte Frage, Quelle (Badge „Lokal — 0 Tokens" vs. „Remote (Fireworks) — eskaliert"), Antworttext, Tokens dieser Anfrage, laufende Gesamtstatistik (z. B. „3/5 Anfragen kostenlos lokal beantwortet").

**Hosting-Ablauf:** `docker build -f Dockerfile.demo` → `docker run -p 8000:8000 --env-file .env` (gleiches `OLLAMA_BASE_URL`/`host.docker.internal`-Setup wie beim Eval-Container) → `ngrok http 8000` für die öffentliche URL. Finale URL erst kurz vor der Einreichung erzeugen (Free-Tier-URLs rotieren bei Neustart). Rechner + Ollama + Container + ngrok müssen laufen, wenn jemand den Link öffnet.

**Sicherheit:** `FIREWORKS_API_KEY` nie in `Dockerfile.demo` einbacken oder committen, nur per `--env-file`/`-e`. Da der Endpunkt öffentlich erreichbar ist, im README kurz auf mögliches Kostenrisiko durch ungebremste Nutzung hinweisen (einfaches Rate-Limit ist optionaler Nice-to-have).

**Zeitplan-Slot:** Mi 8.7. (siehe Abschnitt 5), ~2–3 h, explizit Nebenaufgabe — nicht auf Do 9.7. (Feature-Freeze) oder Fr 10.7. (bereits voll) legen.

---
*Dieses Dokument ersetzt die früheren Entwürfe unter `Juli_Sprint/hackathon-amd-act2/`. Nach dem Kickoff am 6.7. werden Abschnitt 8 aufgelöst und die Erkenntnisse hier eingepflegt.*

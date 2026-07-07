# MASTERPLAN — AMD Developer Hackathon: ACT II (Solo-Teilnahme Sebastian)

> **Zweck dieses Dokuments:** Vollständiges, eigenständiges Briefing. Wer dieses Dokument liest (Mensch oder KI-Assistent), hat ALLEN nötigen Kontext, um Sebastian bei diesem Hackathon zu unterstützen — ohne Rückfragen zur Ausgangslage. **Stand: 7. Juli 2026, abends.**

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

**Bonus-Chance „Best Use of Gemma 4" — bewusst NICHT verfolgt (7.7., Entscheidung):** Die 3 Gemma-4-Varianten benötigen dediziertes Deployment ($28–40/h echtes Geld, nicht nur Tokens) statt Serverless-Zugriff wie die anderen 2 Modelle. Erwarteter Nutzen (Bonus ist kompetitiv, unser Use-Case simpel) rechtfertigt das Kostenrisiko nicht, vor allem da das begrenzte Fireworks-Guthaben fürs Kern-Testing gebraucht wird. **Kein Ausschluss für später:** falls kurz vor Abgabe noch Budget/Zeit übrig ist, optionaler kurzer Effizienztest (s. Abschnitt 5, Do 9.7.) — aber nicht als Ziel verfolgt, nur als Kür falls Zeit bleibt.

**Warum dieser Track weiterhin richtig für Sebastian:** Objektives, automatisiertes Scoring (kein Jury-Pitch), passt zu seiner Ollama-Vorerfahrung, und das PDF bestätigt: unser bereits gebauter Cascade-Router (lokal zuerst, Fireworks bei Bedarf) ist architektonisch weiterhin goldrichtig — nur der Container-Vertrag (I/O-Dateien statt Web-Server) und ein paar Konfigurationsdetails müssen angepasst werden.

---

## 4. WAS GEBAUT WIRD: Architektur

**Projekt:** `amd-act2-router` — ein Cascade-Router. Öffentliches GitHub-Repo, MIT-Lizenz.

```
amd-act2-router/
├── router/
│   ├── config.py           # Zentrale Konfiguration, alles per Env-Var (inkl. .env fuer lokale Entwicklung)
│   ├── local_client.py     # spricht lokales Modell (OpenAI-kompatible API, Tokens = 0)
│   ├── remote_client.py    # spricht Fireworks AI (OpenAI-kompatibel, Tokens zählen! max_tokens gedeckelt)
│   ├── judge.py            # Confidence-Parsing, Kritiker, Code-Syntax-Check, semantic_judge (nur Eval)
│   └── main.py             # Cascade-Logik: route()
├── eval/
│   ├── tasks.jsonl         # 22 Testaufgaben, alle 8 Kategorien, Englisch
│   └── run_eval.py         # misst Accuracy (2 Methoden) + Tokens, Kalibrierungstabelle
├── submission/
│   └── run.py              # ✅ FERTIG — liest /input/tasks.json, ruft route() pro Task, schreibt /output/results.json
├── demo/                   # optionales Video-Hilfsmittel, KEINE Submission-Pflicht
│   ├── app.py               # FastAPI-Demo, wrappt route()
│   └── static/index.html
├── Dockerfile              # ✅ Wettbewerbs-Image, submission/run.py als Entrypoint, linux/amd64 verifiziert
├── Dockerfile.demo         # separates Image nur für die Video-Demo
├── README.md               # Setup, Architektur, Build-/Run-/Push-Befehle
└── LICENSE                 # MIT
```

**Architektur-Kernfakt:** Das Wettbewerbs-Docker-Image ist ein **Batch-Container** (liest eine Task-Datei, schreibt eine Ergebnis-Datei, beendet sich) — kein Web-Server. Die Demo-App bleibt nur fürs Presentation-Video sinnvoll.

**Cascade-Logik (aktueller Stand, alle Schritte lokal = 0 Tokens bis auf den letzten):**
1. Aufgabe rein → **immer zuerst lokales Modell** (`gemma2:2b`, inkl. Warm-up gegen Cold-Start)
2. **Confidence-Check:** Modell liefert ANSWER + eigene CONFIDENCE-Einschätzung; unter Schwelle (70) → eskalieren
3. **Selbst-Konsistenz-Check** (nur Antworten ≤80 Zeichen): Frage nochmal lokal stellen, bei Widerspruch → eskalieren
4. **Code-Syntax-Check** (nur bei Code-Antworten): `ast.parse()`, bei Syntaxfehler → eskalieren
5. Eskalation → Fireworks (`kimi-k2p7-code`, tokeneffizientestes verfügbares Modell), Kürze-Prompt + `max_tokens=512`
6. Bei Remote-Fehler: Fallback auf die unsichere lokale Antwort statt leerem String

**Eiserne Regel:** Jede Änderung wird gegen `eval/run_eval.py` gemessen; nur behalten, was die Zahlen verbessert.

**Technischer Schlüssel-Fakt:** Ollama UND Fireworks bieten OpenAI-kompatible APIs → derselbe Python-Code (`openai`-Paket) spricht beide, nur `base_url`/`api_key` unterscheiden sich.

---

## 5. ZEITPLAN Tag für Tag

| Tag | Phase | Inhalt | Fertig-Kriterium |
|---|---|---|---|
| **So 5.7.** | Vorbereitung | 0.1 Accounts checken (lablab-Dashboard, Fireworks-API-Key, beide Discords) · 0.2 Umgebung (Docker-hello-world, 2 Ollama-Modelle in 2 Größen, GitHub-Repo) · 0.3 Docker-Crashkurs 90 min · 0.4 LLM-API-Crashkurs 90 min (gleicher Code lokal + remote, Tokens auslesen) · 0.5 **Kernübung: kompletten Übungs-Router bauen** (4–6 h) · 0.6 abends 30 min DeepLearning.AI | `docker run` lässt Übungs-Eval durchlaufen und liefert Accuracy + Tokens |
| **Mo 6.7.** | Kickoff | Vormittags Kickoff verfolgen, `kickoff-notizen.md` anlegen: Aufgaben? erlaubte Modelle? Specs der Scoring-Umgebung? Accuracy-Schwelle? Submit-Prozess? · Hackathon-Credits einlösen · AMD-Cloud-Zugang einrichten · Nachmittags **2 Baselines**: alles-lokal (Tokens 0, Accuracy?) und alles-remote (Accuracy-Maximum, Token-Maximum) | Beide Baseline-Zahlen dokumentiert |
| **Di 7.7.** ✅ | Iteration | **Erledigt, deutlich mehr als geplant:** `submission/run.py` gebaut+getestet · `ALLOWED_MODELS`-Umstellung · Prompts auf Englisch · `eval/tasks.jsonl` auf 22 Aufgaben (8 Kategorien) erweitert · Regex-Bug + Cold-Start-Bug behoben · Docker-Image inkl. `linux/amd64`-Verifikation · echter Fireworks-Key getestet, Modellvergleich (`kimi-k2p7-code` gewinnt) · Selbst-Konsistenz-Check + Code-Syntax-Check gebaut · Eval-Accuracy-Messung verbessert (semantic_judge) | Alles oben verifiziert und committet |
| **Mi 8.7.** | Iteration/Puffer | Da Di 7.7. schon den Großteil von Mi+Do vorgezogen hat: Rest-Feinschliff Router (falls noch Ideen), **README fertig polieren**, ggf. weitere Eval-Aufgaben für Summarization/NER | README vorzeigbar, Router stabil |
| **Do 9.7.** | Submission-Vorbereitung | **Container-Registry einrichten + Push** (ghcr.io, aktuell bewusst zurückgestellt) · optionaler kurzer Gemma-4-Effizienztest, falls Zeit/Budget übrig · **abends Feature-Freeze**, Git-Tag `v1.0` | Image öffentlich in Registry, beste Version eingefroren |
| **Fr 10.7.** | Submission-Paket | Container von frischem Klon durchtesten (10-Min-/30s-/60s-Limits im Blick) · Presentation-Video **max. 5 min, MP4, max. 300 MB** (OBS, danach Dateigröße prüfen!) · finaler Image-Push | Alles Material fertig, Video ≤ 300 MB bestätigt, Image öffentlich pullbar |
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

## 8. AKTUELLER STAND & OFFENE PUNKTE (Stand 7.7. abends)

### 8.1 Fertig & verifiziert

- ✅ **Cascade-Router komplett funktionsfähig:** lokal (`gemma2:2b`) → Confidence-Check → Selbst-Konsistenz-Check → Code-Syntax-Check → Eskalation an `kimi-k2p7-code` bei Bedarf. Alle Schritte bis auf die Eskalation selbst kosten 0 Tokens.
- ✅ **`submission/run.py`:** liest `/input/tasks.json`, schreibt `/output/results.json`, mit Zeitbudget-Schutz (9-Min-Grenze, Puffer vor dem 10-Min-Hardlimit) und Ollama-Warm-up (behebt realen Cold-Start-Bug: erster Call brauchte sonst >30s).
- ✅ **`linux/amd64`-Pflicht verifiziert:** `docker buildx build --platform linux/amd64 --load .` baut fehlerfrei, `docker inspect` bestätigt `Architecture: amd64` + `Os: linux`. Funktionstest im Image erfolgreich (Exit 0, korrekte Antwort). Die härteste, leicht übersehbare Anforderung ist bestätigt erfüllt, nicht nur angenommen.
- ✅ **Modellwahl datenbasiert getroffen:** Von den 5 offiziell erlaubten Modellen (`minimax-m3`, `kimi-k2p7-code`, `gemma-4-31b-it`, `gemma-4-26b-a4b-it`, `gemma-4-31b-it-nvfp4`) sind aktuell nur die ersten 2 auf Sebastians Fireworks-Account freigeschaltet (Gemma-4-Varianten brauchen kostenpflichtiges Deployment, $28-40/h — bewusst nicht verfolgt, siehe Abschnitt 3). Direkter Vergleich auf allen 22 Eval-Aufgaben: `kimi-k2p7-code` 22/22 korrekt bei 4189 Tokens gesamt, `minimax-m3` 22/22 korrekt bei 5239 Tokens — **`kimi-k2p7-code` ~20 % effizienter, jetzt als Default gesetzt.**
- ✅ **Eval-Messung verlässlicher gemacht:** grober Substring-Check ergänzt um `semantic_judge()` (lokales Modell als informeller Zweit-Gutachter, 0 Tokens) — beide Methoden stimmen aktuell auf allen 22 Aufgaben überein (90,9 %). Kalibrierungstabelle zeigt Trefferquote pro Confidence-Bereich.
- ✅ **GitHub-Repo lebendig:** https://github.com/Faber089/amd-act2-router (aktuell privat). Lokaler Ordner `C:\Users\iq\Documents\GitHub\amd-act2-router` ist die aktive, GitHub-Desktop-verbundene Kopie — **dort arbeiten**, nicht in der älteren Kopie unter `D:\Obsidian_Gedächtnis\AMD hackathon act2\amd-act2-router\`. CLI-Push schlägt fehl (falscher lokaler Git-Account) — Push nur über GitHub Desktop, und **aktuell bewusst noch nicht pushen** (Sebastians Anweisung, Stand 7.7.).
- ✅ `.env`-Unterstützung (`python-dotenv`) für lokale Entwicklung eingebaut, `.gitignore` schützt sie vor versehentlichem Commit.

### 8.2 Bewusste Entscheidungen (nicht vergessen, sondern absichtlich so)

- **Gemma-4-Bonus ("Best Use of Gemma 4", $6.000-Pool) nicht verfolgt:** Kostenrisiko ($28-40/h dediziertes Deployment) rechtfertigt den kompetitiven, unsicheren Bonus nicht. Optionaler kurzer Effizienztest bleibt als Kür vorgemerkt, kurz vor Abgabe, falls Zeit/Budget übrig.
- **Demo-App (`demo/`) ist keine Submission-Pflicht mehr**, bleibt aber als Video-Hilfsmittel bestehen — kein weiterer Hosting-/ngrok-Aufwand nötig.
- **TOON-Format** (Token-Oriented Object Notation) wurde geprüft, aber verworfen — unsere Aufgaben sind reiner Fließtext, keine strukturierten/tabellarischen Daten, die TOON komprimieren könnte.

### 8.3 Noch offen

- [ ] **Container-Registry-Push** (ghcr.io empfohlen, nutzt den Faber089-GitHub-Account) — technisch vorbereitet (README dokumentiert den Befehl), aber noch nicht ausgeführt.
- [ ] **Exakte Accuracy-Gate-Schwelle unbekannt** — PDF nennt nur den Mechanismus (LLM-Judge), keine Zahl. Nach dem abgeschlossenen Discord-Q&A (7.7., laut Sebastian keine offenen Rückfragen mehr) auch extern nicht klärbar — akzeptierte Unsicherheit.
- [ ] **Summarization & NER ohne objektiven Check** — anders als Code (Syntax-Check) oder kurze Antworten (Selbst-Konsistenz) gibt es hier keine einfache automatische Prüfung; verlassen sich auf Confidence + `semantic_judge()`.
- [ ] **Presentation-Video** (≤5 Min, MP4, ≤300 MB) noch nicht erstellt.
- [ ] **README-Feinschliff** für die finale Abgabe.
- [ ] **Reasoning-Token-Risiko:** `gpt-oss-120b` (nicht Teil der erlaubten Modelle, nur zum Testen genutzt) brauchte 45 Tokens für eine Ein-Wort-Antwort wegen unsichtbarer Denk-Tokens. `kimi-k2p7-code` zeigte dieses Verhalten in den Tests NICHT (deutlich günstiger), aber falls sich das Verhalten je ändert: prüfen ob ein `reasoning_effort`-Parameter o. Ä. existiert.
- [ ] AMD-Cloud-GPU-Zugang / zusätzliche Hackathon-Credits — vermutlich nicht nötig, da alles über Fireworks läuft, nicht über eigene GPU-Instanzen.

### 8.4 Wichtige technische Lektionen (falls ähnliche Bugs wieder auftauchen)

- **Regex-Fallstrick:** Eine frühere `ANSWER`-Extraktion stoppte am ersten Zeilenumbruch — bei mehrzeiligem Code wurde fast alles abgeschnitten. Fix: bis zum `CONFIDENCE`-Marker (oder Textende) einfangen, nicht bis zum ersten `\n`.
- **Cold-Start:** der allererste Ollama-Call nach Prozessstart kann das Modell noch laden müssen und >30s brauchen. Fix: expliziter Warm-up-Call vor der eigentlichen Aufgaben-Schleife.
- **Windows/Git-Bash + Docker-Volumes:** `-v "$(pwd)/...":...` wird von Git Bash manchmal falsch übersetzt. Fix: `MSYS_NO_PATHCONV=1` + native Windows-Pfade (`C:/...`) verwenden.
- **Lokale Rechenzeit ist im Scoring gratis** — beliebig viele lokale Gegenchecks (Selbst-Konsistenz, Code-Syntax) kosten 0 Tokens, nur Latenz (~2s/Check, Budget 30s/Aufgabe). Dieser Fakt ist der Kern-Hebel der ganzen Architektur.
- **Reine Selbsteinschätzung (Confidence-Zahl) ist nicht robust** — ein Modell kann überzeugt falsch liegen. Deshalb zusätzliche objektive/statistische Absicherungen (Selbst-Konsistenz, Code-Syntax-Check, Kalibrierungstabelle) statt blind einer einzelnen Zahl zu vertrauen.

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

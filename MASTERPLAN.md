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
| Preisgeld | $21.000 Haupt-Pool (pro Track: $2.500/$1.500/$1.000) + $6.000 Gemma-Sonderpreise |
| Infrastruktur | AMD Developer Cloud (AMD-GPUs, z. B. MI300X), ROCm, Fireworks AI API |
| Credits | $50 Fireworks-API-Credits für alle Teilnehmer + $100 AMD-Cloud- und $50 Fireworks-Credits für neue ADP-Mitglieder; zusätzliche Hackathon-Credits werden am Start verteilt |
| Event-Seite | https://lablab.ai/ai-hackathons/amd-developer-hackathon-act-ii |
| Kommunikation | lablab.ai-Discord (Orga) + AMD-Discord (Technik-Support) — Task-Details kommen dort |

**Die drei Tracks:**
1. **Hybrid Token-Efficient Routing Agent** (Beginner, AI-Agent-Track) — GEWÄHLT, Details unten
2. **Video Captioning** (Beginner) — Pipeline captioned feste Videoclips (30 s–2 min) in 4 Stilen: formal, sarkastisch, humorous-tech, humorous-non-tech; Bewertung per LLM-Judge; Fallback-Option
3. **Unicorn Track** (alle Level) — freies Startup-Projekt, Jury-Bewertung (Kreativität, Originalität, Vollständigkeit, AMD-Nutzung, Marktpotenzial); als Solo-Erstling bewusst NICHT gewählt

---

## 3. GEWÄHLTER TRACK: Track 1 — Hybrid Token-Efficient Routing Agent

**Aufgabe (offiziell):** Baue einen AI-Agenten, der die am Kickoff (6.7.) enthüllten Aufgaben **autonom** löst. Pro Anfrage entscheidet der Agent in Echtzeit:
- **Lokales Modell** nutzen → alle Tokens zählen als **0** für den Score
- oder **Remote-Modell via Fireworks AI API** → Tokens zählen voll

**Gewinnbedingung:** So wenige (Remote-)Tokens wie möglich verbrauchen, OHNE unter die Accuracy-Schwelle zu fallen. **Leaderboard-Wertung: Token-Anzahl + Output-Genauigkeit.** Keine Jury, kein Pitch — objektive Zahlen.

**Wichtige Regeln:**
- Finales Scoring läuft ausschließlich in einer **standardisierten Umgebung** (Specs werden am Kickoff enthüllt) → lokale Modelle müssen in deren Limits passen; Routing-Intelligenz gewinnt, nicht Rechenpower
- Entwickeln/Testen darf man auf beliebiger Hardware
- Prompt-basierte und fine-getunte Ansätze werden identisch bewertet
- Erlaubte Modelle werden am Launch-Tag bekannt gegeben
- Veranstalter-Empfehlung: eigenen lokalen Eval-Schritt bauen, um Output-Qualität vor dem Submitten zu prüfen

**Warum dieser Track für Sebastian:** Beginner-Track mit dem höchsten Lernwert (genau die Kernskills modernen AI-Engineerings), objektives Leaderboard = kein Solo-Nachteil, und seine Ollama-Vorerfahrung passt exakt (lokale vs. Remote-Modelle ist das Kernthema).

**Bonus-Chance:** Gemma-Sonderpreis „Best Use of Gemma via Fireworks" ($1.000 extra in Track 1) — wenn die erlaubten Modelle Gemma enthalten, Gemma einsetzen und im README dokumentieren.

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
│   ├── tasks.jsonl        # Aufgaben mit Soll-Lösungen
│   └── run_eval.py        # misst Accuracy + Remote-Tokens pro Lauf
├── Dockerfile             # Pflicht: Submission muss containerized sein
├── README.md              # Setup, Architektur, Eval-Ergebnisse
└── LICENSE                # MIT
```

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
| **Sa 5.7.** | Vorbereitung | 0.1 Accounts checken (lablab-Dashboard, Fireworks-API-Key, beide Discords) · 0.2 Umgebung (Docker-hello-world, 2 Ollama-Modelle in 2 Größen, GitHub-Repo) · 0.3 Docker-Crashkurs 90 min · 0.4 LLM-API-Crashkurs 90 min (gleicher Code lokal + remote, Tokens auslesen) · 0.5 **Kernübung: kompletten Übungs-Router bauen** (4–6 h) · 0.6 abends 30 min DeepLearning.AI | `docker run` lässt Übungs-Eval durchlaufen und liefert Accuracy + Tokens |
| **So 6.7.** | Kickoff | Vormittags Kickoff verfolgen, `kickoff-notizen.md` anlegen: Aufgaben? erlaubte Modelle? Specs der Scoring-Umgebung? Accuracy-Schwelle? Submit-Prozess? · Hackathon-Credits einlösen · AMD-Cloud-Zugang einrichten · Nachmittags **2 Baselines**: alles-lokal (Tokens 0, Accuracy?) und alles-remote (Accuracy-Maximum, Token-Maximum) | Beide Baseline-Zahlen dokumentiert |
| **Mo 7.7.** | Iteration | Eval-Harness auf echte Aufgaben umstellen · Router v1 (Cascade) auf echte Modelle portieren | v1 läuft gegen echte Aufgaben, Zahlen protokolliert |
| **Di 8.7.** | Iteration | v1 tunen: Judge-Varianten, Eskalations-Schwelle, Prompt-Kürzung, `max_tokens` | Messbar besser als Mo |
| **Mi 9.7.** | Iteration | v2 (Vorab-Klassifikation) testen · Gemma-Bonus einbauen falls möglich · **abends Feature-Freeze**, Git-Tag `v1.0` | Beste Version eingefroren |
| **Do 10.7.** | Submission-Paket | Container von frischem Klon durchtesten · README (Architektur + Ergebnistabelle) · Demo-Video 2–3 min (OBS) · Slides 5–7 Stück · Cover-Bild | Alles Material fertig |
| **Fr 11.7.** | Abgabe | Alle lablab.ai-Felder ausfüllen, **spätestens 14:00 deutscher Zeit** submitten (Deadline 17:00), Bestätigung screenshotten | Submission bestätigt |

---

## 6. SUBMISSION-PFLICHTEN (Checkliste, alle Tracks)

- [ ] Projekt-Titel, Kurzbeschreibung, Langbeschreibung, Technologie-/Kategorie-Tags
- [ ] Cover-Bild
- [ ] Video-Präsentation
- [ ] Slide-Präsentation
- [ ] Öffentliches GitHub-Repo mit README (Setup + Nutzung; Projekt muss damit lauffähig sein)
- [ ] Demo-Application-URL
- [ ] **Containerized (Docker) — harte Pflicht**
- [ ] Original & MIT-kompatibel, keine API-Keys im Code (Umgebungsvariablen!)
- [ ] Einreichung über lablab.ai-Plattform vor Deadline

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
- NICHT lernen/bauen: ROCm-/GPU-Programmierung im Detail (fertige Endpoints reichen), Fine-Tuning (erlaubt, aber falsche Baustelle in 5 Tagen), Web-Frontend (Leaderboard-Track, keine UI nötig)

---

## 8. OFFENE PUNKTE (werden am Kickoff geklärt → hier nachtragen!)

**Update 6.7.:** Kickoff-Inhalte (Aufgaben, Modelle, Credits) sind laut lablab-Dashboard/Discord noch nicht veröffentlicht — kommen **morgen (7.7.)**. Phase 1 im Zeitplan verschiebt sich entsprechend um einen Tag; wir nutzen den heutigen Tag weiter für Übung/Vorbereitung (Phase 0).

**Stand Ende 6.7. — Grundgerüst fertig & getestet (Ordner `amd-act2-router/`):**
- ✅ Cascade-Router läuft (lokal zuerst → bei Unsicherheit Fireworks), komplett über Umgebungsvariablen konfigurierbar (`router/config.py`)
- ✅ Eval-Harness misst Genauigkeit + Tokenverbrauch (`eval/run_eval.py`, 13 Übungsaufgaben)
- ✅ Containerized — Docker-Image baut, Container erreicht Host-Ollama via `host.docker.internal` (verifiziert)
- ✅ README, MIT-LICENSE, .gitignore (schützt vor Key-Leak), requirements.txt
- ✅ Lokal committet auf Branch `main` (Git-Account: **Sebastian0890**)
- ⏳ **OFFEN: GitHub-Push** — blockiert, weil zwei Entscheidungen anstehen:
  1. **Account-Diskrepanz:** Git/`gh` ist als **Sebastian0890** angemeldet, aber im AMD-Formular wurde **github.com/faber089** als Verifizierungsprofil angegeben. Für eine konsistente Submission sollten Repo-Account und AMD-Profil zusammenpassen → klären, welcher Account gilt.
  2. **Öffentlich vs. privat:** Submission verlangt am Ende ein **öffentliches** Repo; bis dahin könnte es privat bleiben.
- 🔧 **Modellwahl aktuell:** lokal `gemma2:2b` (schnell), remote `gpt-oss-120b`. Kritiker (`USE_CRITIQUE`) standardmäßig AUS (eskalierte in der Übung zu viel). Morgen mit echten Aufgaben/Modellen neu justieren.

- [ ] Konkrete Aufgaben des Tracks (Input-/Output-Format)
- [ ] Liste der erlaubten Modelle (lokal + remote)
- [ ] Specs der standardisierten Scoring-Umgebung (CPU/GPU/RAM, Runtime: Ollama? vLLM? transformers?)
- [ ] **Gibt es ein Zeit-/Timeout-Limit pro Aufgabe in der Scoring-Umgebung?** (offiziell wird nur „Token count + accuracy" gewertet, kein Speed-Kriterium — aber „lokale Modelle müssen in die Umgebung passen" deutet auf ein implizites Ressourcen-/Zeitlimit hin. Im Discord nachfragen, falls bei Kickoff nicht klar.)
- [ ] Höhe der Accuracy-Schwelle, Anzahl erlaubter Scoring-Läufe
- [ ] Details AMD-Cloud-GPU-Zugang + zusätzliche Hackathon-Credits
- [ ] **Optimale lokale Modellgröße finden:** 0,5B (qwen2.5) zu schwach — hält Format nicht ein, inhaltlich falsch. 6,6B (qwen3.5) inhaltlich zuverlässig, aber auf CPU zu langsam zum Iterieren (~30 Min für 13 Testfragen). 2B (gemma2:2b) ist schnell (~2s/Antwort) UND hält das Format ein, ABER: liefert bei schweren Fragen (große Multiplikation, obskures Wissen) **selbstbewusst falsche Antworten und eskaliert nicht**. Nach Kickoff mit den erlaubten Modellen testen.

**🔑 Kern-Erkenntnis aus der Übung (5./6.7.):** Reines Selbst-Vertrauen des lokalen Modells als Judge ist nicht robust genug — ein Modell kann überzeugt falsch liegen. Für die finale Lösung braucht es vermutlich eine zusätzliche Absicherung, z. B.: Aufgaben-Typ-Erkennung vor der Antwort (z. B. Rechenaufgaben mit großen Zahlen grundsätzlich eskalieren), Selbst-Konsistenz-Check (Frage zweimal anders formuliert stellen, bei Widerspruch eskalieren), oder härtere Heuristiken statt nur einer Vertrauens-Zahl vom Modell selbst.

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

---
*Dieses Dokument ersetzt die früheren Entwürfe unter `Juli_Sprint/hackathon-amd-act2/`. Nach dem Kickoff am 6.7. werden Abschnitt 8 aufgelöst und die Erkenntnisse hier eingepflegt.*

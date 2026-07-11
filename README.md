# amd-act2-router — General-Purpose AI Agent (Track 1)

Ein **Cascade-Routing-Agent** für den **AMD Developer Hackathon: ACT II**, Track 1
(*Hybrid Token-Efficient Routing Agent*) — löst Aufgaben aus 8 Kategorien
(Factual Knowledge, Math Reasoning, Sentiment, Summarisation, NER, Code
Debugging, Logical Reasoning, Code Generation) so tokeneffizient wie möglich.

**Kernidee:** Lokale Rechenzeit ist im Wettbewerb kostenlos, nur
Fireworks-Tokens zählen. Also wird jede Aufgabe zuerst **lokal** beantwortet
(Qwen3 1.7B, eingebacken im Image, 0 Tokens) und **lokal verifiziert** — erst
wenn die Verifikation die Antwort nicht absichern kann, wird an **Fireworks
eskaliert**. Tokens fließen nur dorthin, wo lokale Intelligenz nachweislich
nicht reicht.

```
Aufgabe
   │
   ▼
1. Kategorie-Erkennung (Regex, paraphrasen-robust, 0 Tokens)
   │
   ▼
2. Lokales Modell (Qwen3 1.7B via Ollama im Container, 0 Tokens)
   │
   ▼
3. Kategorie-spezifische Verifikation (0 Tokens)
   │        bestanden ──► lokale Antwort (0 Tokens)
   ▼
4. Lokaler Retry bei behebbaren Fehlern (Format, fehlender Code; 0 Tokens)
   │        bestanden ──► lokale Antwort (0 Tokens)
   ▼
5. Eskalation an Fireworks (kimi-k2p7-code, reasoning_effort=none)
           ──► Antwort (Tokens zählen)
```

## Warum nicht einfach eine Confidence-Zahl?

Gemessen: Antworten mit selbstberichteter Confidence 100 waren nur zu 66–87 %
korrekt — Selbsteinschätzung allein ist wertlos. Stattdessen prüft jede
Kategorie **objektiv**:

| Kategorie | Lokale Absicherung (alle 0 Tokens) |
|---|---|
| Factual Knowledge | Vollständigkeits-Hint; zweiteilige Fragen ("…, and what…") eskalieren immer (gemessen: confident-wrong-Risiko) |
| Math Reasoning | **Gegenrechnung**: lokales Modell schreibt unabhängig einen Python-Ausdruck, `safe_eval` rechnet deterministisch nach; Widerspruch zur finalen Zahl → Eskalation |
| Sentiment | Label-Pflichtformat + **2-von-3-Mehrheitsvotum** über lokale Läufe bei Label-Streit |
| Summarisation | Format-Gate (Satzzahl/Wortlimit/Bullets exakt geparst) + Kopie-Erkennung (wörtlich übernommener Quelltext ist keine Zusammenfassung) + lokaler Rewrite-Retry |
| NER | **Entity-Union** aus zwei Läufen + Normalisierung (zerhackte Namen wie "Maria (PERSON); Sanchez (PERSON)" verschmelzen, aufs Jahr gestutzte Daten expandieren) |
| Code Debugging | AST-Syntax-Check + Identisch-zum-Original-Erkennung + Code-Pflicht (Prosa-Antwort → lokaler Retry → sonst Eskalation) |
| Logical Reasoning | **Immer eskalieren** (Politik): lokal 3/8–9/15 korrekt bei durchweg Confidence 100 — unerkennbar falsch |
| Code Generation | AST-Syntax-Check + Code-Pflicht + Retry |

Bei Eskalationen wird `reasoning_effort=none` gesetzt: kimi-k2p7-code ist ein
Reasoning-Modell und verbrennt sonst ~30–40 unsichtbare Denk-Tokens selbst bei
Ein-Wort-Antworten (gemessen: 40 → 3 completion-Tokens). Nur Logik bekommt
einen minimalen sichtbaren Reasoning-Hint (gemessen: ohne CoT 0/2, mit
Minimal-Hint 22/22 bei 105 Tokens/Aufgabe — verstecktes Denken via
`effort=low` wäre TEURER, 141/Aufgabe).

## Robustheit gegen ungesehene Aufgaben

Die finale Bewertung nutzt **neu randomisierte Prompt-Varianten** — deshalb:

- Die Kategorie-Erkennung wurde gegen ein eigenes **120-Aufgaben-Paraphrasen-Set**
  gehärtet (Formulierungen ohne die offensichtlichen Schlüsselwörter,
  strukturelle Code-Erkennung statt reiner Keywords): 184/184 korrekt
  klassifiziert über beide Test-Sets.
- Kein Hardcoding, kein Antwort-Caching, keine aufgabenspezifischen Tricks —
  alle Checks sind generische Eigenschaften der Kategorie (Formattreue,
  Nachrechenbarkeit, Syntax), nicht der Testfragen.
- `ALLOWED_MODELS` wird zur Laufzeit gelesen; kimi wird per Substring
  bevorzugt, unabhängig von der Reihenfolge in der Env; fällt ein Modell aus,
  greift ein 404-Fallback auf das Default-Modell.
- Zeitbudgets auf jeder Ebene: lokale Schritte teilen sich ein Budget pro
  Aufgabe (30s-Limit), der Batch-Lauf schaltet bei knappem Gesamtbudget
  (10-Minuten-Limit) auf Remote-direkt um, und `results.json` wird IMMER
  geschrieben (vollständig, valide, beide Felder als Strings) — auch nach
  Fehlern.

## Gemessene Ergebnisse (eigener jury-naher LLM-Judge, minimax-m3)

| Messung | 64-Task-Benchmark | 120-Task-Paraphrasen-Set |
|---|---|---|
| Judge-Accuracy | ~92 % | ~90 % |
| Fireworks-Tokens gesamt | ~2.100 | ~3.600 |
| Eskalationsrate | ~39 % | ~35 % |
| max. Latenz/Aufgabe (VM-Sim 2 vCPU/4 GB) | < 15 s | < 15 s |

Offizielle Practice-Tasks (8 Stück, frisch gepulltes Image, `--cpus=2
--memory=4g`): alle 8 korrekt beantwortet, 5–6 davon komplett lokal
(0 Tokens), Exit 0, gültiges JSON.

## Projektstruktur

| Datei | Zweck |
|---|---|
| `router/config.py` | Zentrale Konfiguration, alles über Umgebungsvariablen |
| `router/categories.py` | Kategorie-Erkennung + Politik pro Kategorie + alle deterministischen Checks (Gegenrechnung, Format-Gate, Entity-Normalisierung …) |
| `router/local_client.py` | Lokales Modell — zwei Backends: `ollama` (nativ, im Container) / `lmstudio` (OpenAI-kompatibel, Dev auf GPU) |
| `router/remote_client.py` | Fireworks-Client: Timeout, Token-Telemetrie, reasoning_effort-Steuerung, Modell-Auflösung aus `ALLOWED_MODELS` mit 404-Fallback |
| `router/judge.py` | ANSWER/CONFIDENCE-Parsing, Code-Extraktion, AST-Syntax-Check |
| `router/main.py` | Die Cascade-Logik (`route()`) mit allen Guards und Retries |
| `submission/run.py` | **Wettbewerbs-Entrypoint** — liest `/input/tasks.json`, schreibt `/output/results.json`; Zeitbudget-Flip auf Remote-direkt (mit Kategorie-Politik) |
| `entrypoint.sh` | Container-Start: eingebautes Ollama hochfahren, dann `submission.run` |
| `eval/tasks.jsonl` | 64 Testaufgaben (8 je Kategorie) mit Referenzantworten + objektiven Checks (exakte Zahlen, ausführbare Code-Tests) |
| `eval/tasks_extended.jsonl` | 120 Paraphrasen-Aufgaben (15 je Kategorie) — testet Generalisierung statt Overfitting |
| `eval/judge_llm.py` | Jury-naher LLM-Judge (Rubrik im Wortlaut des Participant Guide) |
| `eval/run_eval.py` | Misst Accuracy (deterministisch + Judge), Token-Split, Latenzen, Eskalationsraten, Fehlklassifikationen; JSON-Reports |
| `demo/app.py` | FastAPI-Demo (optionales Video-Hilfsmittel, keine Submission-Pflicht) |
| `docs/index.html` | Projekt-Showcase-Seite (GitHub Pages) |

## Konfiguration (Umgebungsvariablen)

Werden im Wettbewerb vom Harness injiziert — nie im Code hardcoden.

| Variable | Standard | Bedeutung |
|---|---|---|
| `FIREWORKS_API_KEY` | — | **Pflicht** für Remote-Calls; im Wettbewerb vom Harness gestellt |
| `FIREWORKS_BASE_URL` | `https://api.fireworks.ai/inference/v1` | Pflicht-Endpoint für ALLE Fireworks-Calls |
| `ALLOWED_MODELS` | Fireworks-Modellliste | Komma-separierte erlaubte IDs; kimi wird per Substring bevorzugt |
| `LOCAL_BACKEND` | `lmstudio` (Dev) / `ollama` (Container, via Dockerfile) | Backend fürs lokale Modell |
| `LOCAL_MODEL` | `qwen/qwen3-1.7b` bzw. `qwen3:1.7b` | Eigenes lokales Modell (zählt 0 Tokens) |
| `CONFIDENCE_THRESHOLD` | `70` | Ab wann der lokalen Selbsteinschätzung vertraut wird |
| `AGGRESSIVE` | `0` | `1` = Logik lokal (Token-Minimum, Accuracy-Risiko), `2` = Ultra |
| `SUMMARISATION_ALWAYS_ESCALATE` | `0` | Not-Schalter: Summarisation immer remote |

## Lokal ausführen (Eval-Harness)

```bash
pip install -r requirements.txt
# Fireworks-Key setzen: export FIREWORKS_API_KEY="dein-key"  (oder .env)

# Dev-Backend: LM Studio (GPU) auf Port 1234 mit qwen/qwen3-1.7b geladen —
# oder LOCAL_BACKEND=ollama fuer Ollama auf Port 11434.
python -m eval.run_eval                                        # 64er-Set
python -m eval.run_eval --tasks eval/tasks_extended.jsonl      # Paraphrasen-Set
python -m eval.run_eval --classify-only                        # nur Kategorie-Erkennung (0 LLM-Calls)
```

## Wettbewerbs-Image bauen & testen

Das Docker-Image ist der Submission-Artefakt: liest `/input/tasks.json`,
schreibt `/output/results.json`. **Self-contained** — Ollama-Server und
Qwen3-1.7B-Gewichte werden zur Build-Zeit eingebacken; auf der Judging-VM
gibt es keinen Internetzugang außer dem Fireworks-Proxy.

```bash
docker buildx build --platform linux/amd64 -t amd-act2-router --load .

# Judging-VM-Simulation (2 vCPU / 4 GB, wie im Guide spezifiziert):
docker run --rm --cpus=2 --memory=4g \
  -v "C:/Pfad/zu/smoke_input:/input" -v "C:/Pfad/zu/smoke_output:/output" \
  -e FIREWORKS_API_KEY="dein-key" \
  amd-act2-router
```

`smoke_input/tasks.json` enthält die 8 offiziellen Practice-Tasks.

### Registry-Push (Submission)

```bash
docker buildx build --platform linux/amd64 --provenance=false \
  --tag ghcr.io/faber089/amd-act2-router:latest --push .
```

Das Package muss auf **Public** stehen (GitHub → Packages → Settings →
Change visibility), sonst PULL_ERROR.

## Demo (optional, fürs Presentation-Video)

`demo/app.py` (FastAPI) wrappt `route()` und zeigt pro Anfrage
lokal/remote-Entscheidung, Antwort und Tokenverbrauch:

```bash
docker build -f Dockerfile.demo -t amd-act2-demo .
docker run --rm -p 8000:8000 -e FIREWORKS_API_KEY="dein-key" \
  -e OLLAMA_BASE_URL="http://host.docker.internal:11434/v1" amd-act2-demo
```

Projekt-Showcase: https://faber089.github.io/amd-act2-router/

## Lizenz

MIT

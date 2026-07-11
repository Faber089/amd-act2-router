"""
Zentrale Konfiguration. Alles ueber Umgebungsvariablen umstellbar,
damit wir am Kickoff-Tag Modelle/Adressen/Schwellen aendern koennen,
OHNE Code anzufassen.
"""
import os

from dotenv import load_dotenv

# Nur fuer lokale Entwicklung (Participant Guide erlaubt das explizit).
# Im Wettbewerbs-Container gibt es keine .env-Datei -- der Harness injiziert
# die echten Werte direkt als Umgebungsvariablen, das hier greift dann einfach
# nicht (load_dotenv() ist ein no-op, wenn keine .env gefunden wird).
load_dotenv()

# --- Lokales Modell (Tokens zaehlen 0) ---
# Zwei Backends (Sebastians Anweisung 11.7.: LM Studio fuer alle Dev-Laeufe,
# weil es auf seiner AMD-GPU deutlich schneller laeuft):
#   lmstudio — OpenAI-kompatibles API auf Port 1234, Dev-Default
#   ollama   — natives API auf Port 11434; bleibt die Engine IM
#              Submission-Container (Judging-VM hat keine GPU, LM Studio ist
#              nicht containerisierbar) -> Dockerfile setzt LOCAL_BACKEND.
LOCAL_BACKEND = os.environ.get("LOCAL_BACKEND", "lmstudio")
_DEFAULT_LOCAL_URL = ("http://localhost:1234/v1" if LOCAL_BACKEND == "lmstudio"
                      else "http://localhost:11434/v1")
LOCAL_BASE_URL = os.environ.get("OLLAMA_BASE_URL", _DEFAULT_LOCAL_URL)
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "qwen/qwen3-1.7b"
              if LOCAL_BACKEND == "lmstudio" else "qwen3:1.7b")

# --- Remote-Modell (Fireworks, Tokens zaehlen) ---
# FIREWORKS_BASE_URL und ALLOWED_MODELS werden vom Harness zur Laufzeit
# injiziert (Participant Guide) -> NIE einen Modellnamen hardcoden, immer aus
# ALLOWED_MODELS lesen. Fallback unten ist nur fuer die lokale Entwicklung,
# bevor der echte Wert vom Harness kommt.
REMOTE_BASE_URL = os.environ.get(
    "FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1"
)
ALLOWED_MODELS = [
    m.strip()
    for m in os.environ.get(
        "ALLOWED_MODELS",
        "accounts/fireworks/models/kimi-k2p7-code,"
        "accounts/fireworks/models/minimax-m3,"
        "accounts/fireworks/models/gemma-4-26b-a4b-it,"
        "accounts/fireworks/models/gemma-4-31b-it,"
        "accounts/fireworks/models/gemma-4-31b-it-nvfp4",
    ).split(",")
    if m.strip()
]
# REMOTE_MODEL erlaubt gezieltes Testen gegen ein bestimmtes Modell aus der
# Liste; ohne Override wird einfach das erste erlaubte Modell verwendet.
REMOTE_MODEL = os.environ.get("REMOTE_MODEL") or ALLOWED_MODELS[0]
FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY")

# Obergrenze fuer Remote-Antworten: verhindert beliebig teure Eskalationen.
# Hoch genug fuer Code-Aufgaben (abruptes Abschneiden wuerde Accuracy kosten),
# niedrig genug um Laber-Antworten zu kappen.
REMOTE_MAX_TOKENS = int(os.environ.get("REMOTE_MAX_TOKENS", "512"))
# Harte Zeitgrenze pro Remote-Call: das 30s-pro-Aufgabe-Limit des Wettbewerbs
# darf nie durch einen haengenden HTTP-Call gerissen werden.
REMOTE_TIMEOUT_SECONDS = float(os.environ.get("REMOTE_TIMEOUT_SECONDS", "25"))
# temperature=0: deterministisch, keine Kreativ-Streuung — kuerzere, stabilere
# Antworten und reproduzierbare Eval-Zahlen.
REMOTE_TEMPERATURE = float(os.environ.get("REMOTE_TEMPERATURE", "0"))
# kimi-k2p7-code ist ein Reasoning-Modell: unsichtbare Denk-Tokens zaehlen
# voll als completion_tokens (gemessen 7.7.: 40 Tokens fuer die Ein-Wort-
# Antwort "Tokyo"). Fireworks akzeptiert reasoning_effort="none" -> 3 Tokens.
# Werte: "none" (aus), "low", "" (= Parameter gar nicht senden).
# Bei 400-Fehler (falls der Wettbewerbs-Proxy den Parameter nicht kennt)
# wiederholt remote_client den Call automatisch ohne den Parameter.
REMOTE_REASONING_EFFORT = os.environ.get("REMOTE_REASONING_EFFORT", "none")

# --- Lokale Generierung begrenzen (Latenz-Schutz) ---
# Auf der Judging-VM (Hardware unbekannt, vermutlich reine CPU) darf eine
# lokale Antwort nie das 30s-Budget sprengen. max_tokens deckelt die
# Generierungsdauer hart; Hauptantwort deterministisch (temperature 0),
# der Selbst-Konsistenz-Check sampelt bewusst mit Temperatur >0 — nur so
# misst der Vergleich echte Instabilitaet statt zweimal denselben Text.
LOCAL_MAX_TOKENS = int(os.environ.get("LOCAL_MAX_TOKENS", "320"))
# Zeitbudget fuer ALLE lokalen Schritte einer Aufgabe zusammen. Judging-VM
# laut Guide-Update: 2 vCPU/4GB — gemessen (Simulation 8.7.): gestapelte
# lokale Calls erreichen sonst 25s beim 30s-Hardlimit pro Aufgabe. Ist das
# Budget verbraucht, wird nicht weiter geprueft, sondern entschieden
# (eskalieren geht in 1-5s).
LOCAL_TIME_BUDGET_SECONDS = float(os.environ.get("LOCAL_TIME_BUDGET_SECONDS", "18"))
LOCAL_TEMPERATURE = float(os.environ.get("LOCAL_TEMPERATURE", "0"))
SELFCHECK_TEMPERATURE = float(os.environ.get("SELFCHECK_TEMPERATURE", "0.8"))
# Qwen3-Modelle denken per Default in <think>-Bloecken. Lokal kostet das
# 0 Tokens, aber viel CPU-Zeit -> Default AUS (/no_think). Pro Kategorie
# per Politik-Flag "local_think" gezielt einschaltbar (z. B. Logik).
LOCAL_THINK = os.environ.get("LOCAL_THINK", "0") == "1"

# --- Eval-Judge (NUR eval/, nie Teil der Submission-Logik) ---
# Der echte Wettbewerbs-Judge ist ein unbekanntes, starkes LLM. Beste
# Annaeherung: remote = minimax-m3 (bewusst ANDERE Modellfamilie als das
# Eskalations-Modell kimi -> keine Selbst-Bevorzugung), local = qwen3.5 via
# Ollama als kostenlose Offline-Alternative.
EVAL_JUDGE_BACKEND = os.environ.get("EVAL_JUDGE_BACKEND", "remote")
EVAL_JUDGE_MODEL = os.environ.get(
    "EVAL_JUDGE_MODEL", "accounts/fireworks/models/minimax-m3"
)
EVAL_JUDGE_LOCAL_MODEL = os.environ.get("EVAL_JUDGE_LOCAL_MODEL", "qwen3.5:latest")

# Aggressivitaets-STUFEN fuer die Doppel-Submission-Strategie (im Image per
# --build-arg AGGRESSIVE=N baken; erst einsetzen, wenn die sichere Variante
# das Gate nachweislich besteht!):
#   0 = sichere Kaskade (Default)
#   1 = Logik bleibt LOKAL (teuerste Kategorie; gemessen 65% statt 100%
#       Logik-Accuracy, ~-4 Gesamtpunkte, ~-900 Tokens auf 64er-Skala)
#   2 = ULTRA: zusaetzlich Summarisation/Zwei-Teil-Factual nie eskalieren
#       + Confidence-Schwelle 40 — Token-Minimum, Gate-Roulette (~-8 Punkte)
try:
    AGGRESSIVE = int(os.environ.get("AGGRESSIVE", "0") or "0")
except ValueError:
    AGGRESSIVE = 0

# --- Routing-Verhalten ---
# Ab welcher Selbsteinschaetzung wird der lokalen Antwort vertraut.
CONFIDENCE_THRESHOLD = int(os.environ.get("CONFIDENCE_THRESHOLD", "70"))
# Zweite, skeptische Pruefung zusaetzlich einschalten? ("1" = an, "0" = aus)
# Standard aus: in der Uebung eskalierte der Kritiker zu viel. Am Kickoff-Tag
# mit den echten Aufgaben neu bewerten.
USE_CRITIQUE = os.environ.get("USE_CRITIQUE", "0") == "1"
# Selbst-Konsistenz-Check: kurze, vertrauenswuerdige lokale Antworten einmal
# gegenpruefen (zweiter lokaler Lauf, kostenlos). Widerspruch -> eskalieren.
# Fanggt "selbstbewusst falsch" ab, was die Confidence-Zahl allein nicht kann.
USE_SELFCHECK = os.environ.get("USE_SELFCHECK", "1") == "1"
# Nur kurze Antworten gegenpruefen (Zahlen, Namen, Ja/Nein) — lange Antworten
# (Code, Zusammenfassungen) sind nie zeichengleich, dort wuerde der Check
# immer faelschlich eskalieren.
SELFCHECK_MAX_ANSWER_LEN = int(os.environ.get("SELFCHECK_MAX_ANSWER_LEN", "80"))

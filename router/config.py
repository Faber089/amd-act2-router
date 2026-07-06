"""
Zentrale Konfiguration. Alles ueber Umgebungsvariablen umstellbar,
damit wir am Kickoff-Tag Modelle/Adressen/Schwellen aendern koennen,
OHNE Code anzufassen.
"""
import os

# --- Lokales Modell (Tokens zaehlen 0) ---
# Standard: Ollama auf dem Host. Im Docker-Container muss die Adresse auf
# host.docker.internal zeigen -> per Env-Var OLLAMA_BASE_URL ueberschreibbar.
LOCAL_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "gemma2:2b")

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
    for m in os.environ.get("ALLOWED_MODELS", "gemma-4-26b-a4b-it").split(",")
    if m.strip()
]
# REMOTE_MODEL erlaubt gezieltes Testen gegen ein bestimmtes Modell aus der
# Liste; ohne Override wird einfach das erste erlaubte Modell verwendet.
REMOTE_MODEL = os.environ.get("REMOTE_MODEL") or ALLOWED_MODELS[0]
FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY")

# --- Routing-Verhalten ---
# Ab welcher Selbsteinschaetzung wird der lokalen Antwort vertraut.
CONFIDENCE_THRESHOLD = int(os.environ.get("CONFIDENCE_THRESHOLD", "70"))
# Zweite, skeptische Pruefung zusaetzlich einschalten? ("1" = an, "0" = aus)
# Standard aus: in der Uebung eskalierte der Kritiker zu viel. Am Kickoff-Tag
# mit den echten Aufgaben neu bewerten.
USE_CRITIQUE = os.environ.get("USE_CRITIQUE", "0") == "1"

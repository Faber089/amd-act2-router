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
REMOTE_BASE_URL = os.environ.get(
    "FIREWORKS_BASE_URL", "https://api.fireworks.ai/inference/v1"
)
REMOTE_MODEL = os.environ.get(
    "REMOTE_MODEL", "accounts/fireworks/models/gpt-oss-120b"
)
FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY")

# --- Routing-Verhalten ---
# Ab welcher Selbsteinschaetzung wird der lokalen Antwort vertraut.
CONFIDENCE_THRESHOLD = int(os.environ.get("CONFIDENCE_THRESHOLD", "70"))
# Zweite, skeptische Pruefung zusaetzlich einschalten? ("1" = an, "0" = aus)
# Standard aus: in der Uebung eskalierte der Kritiker zu viel. Am Kickoff-Tag
# mit den echten Aufgaben neu bewerten.
USE_CRITIQUE = os.environ.get("USE_CRITIQUE", "0") == "1"

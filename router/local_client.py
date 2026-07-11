import json
import re
import time
import urllib.error
import urllib.request

from router import config

# Zwei lokale Backends (Sebastians Anweisung 11.7.):
#   lmstudio — OpenAI-kompatibles API (Port 1234). Dev-Standard: laeuft auf
#              der AMD-GPU deutlich schneller als Ollama auf der CPU.
#              Denk-Steuerung fuer Qwen3 ueber den /no_think-Soft-Switch im
#              Prompt; Denkspuren liegen in reasoning_content und werden
#              bewusst ignoriert (nur content ist die Antwort).
#   ollama   — natives /api/chat (Port 11434). Bleibt die Engine IM
#              Submission-Container (Judging-VM ohne GPU; LM Studio ist
#              nicht containerisierbar). Denk-Steuerung ueber den nativen
#              "think"-Parameter (der /v1-Endpoint von Ollama ignoriert
#              /no_think UND extra_body — gemessen 10.7.).

# Aeltere/andere Modelle koennen <think>-Bloecke inline in den Antworttext
# schreiben — die gehoeren nie in eine Antwort, die bewertet wird.
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _post_json(url, payload, timeout=300):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.URLError:
        # Transienter Verbindungsfehler (Server startet gerade neu o. ae.):
        # EIN Wiederholungsversuch nach kurzer Pause — hat am 11.7. drei
        # komplette Eval-Laeufe gekostet, im Container schadet es nie.
        time.sleep(2)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())


def ask_local_raw(prompt, model=None, temperature=None, max_tokens=None, think=None):
    """Schickt den Prompt unveraendert ans lokale Modell, ohne Format-Vorgabe.
    think: Denkmodus fuer faehige Modelle (qwen3 ...). None = Config-Default.
    Denken kostet 0 Leaderboard-Tokens, nur lokale Rechenzeit."""
    model = model or config.LOCAL_MODEL
    if think is None:
        think = config.LOCAL_THINK
    temperature = config.LOCAL_TEMPERATURE if temperature is None else temperature
    # Deckelt die Generierungsdauer: auf der 2-vCPU-Judging-VM darf eine
    # ausufernde lokale Antwort nie das 30s-Budget sprengen.
    max_tokens = config.LOCAL_MAX_TOKENS if max_tokens is None else max_tokens

    if config.LOCAL_BACKEND == "lmstudio":
        if not think and "qwen3" in model.lower():
            prompt = f"{prompt} /no_think"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = _post_json(config.LOCAL_BASE_URL.rstrip("/") + "/chat/completions", payload)
        text = data["choices"][0]["message"].get("content") or ""
    else:
        payload = {
            "model": model,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if "qwen3" in model:
            # Nur Denker-Modelle kennen den Parameter — bei anderen (gemma2)
            # wuerde Ollama den Request ablehnen.
            payload["think"] = bool(think)
        native_url = config.LOCAL_BASE_URL.rsplit("/v1", 1)[0] + "/api/chat"
        try:
            data = _post_json(native_url, payload)
        except Exception:
            if "think" in payload:
                # Unbekannter Parameter (aeltere Ollama-Version o. ae.):
                # einmal ohne wiederholen statt komplett auszufallen.
                payload.pop("think")
                data = _post_json(native_url, payload)
            else:
                raise
        text = data.get("message", {}).get("content") or ""

    return _THINK_RE.sub("", text).strip(), 0  # lokale Tokens zaehlen immer als 0


def ask_local(question, model=None, temperature=None, hint=None, max_tokens=None,
              think=None):
    # Prompt-Text muss Englisch sein: alle Antworten muessen laut Participant
    # Guide auf Englisch sein, egal welche Sprache die Aufgabe selbst hat.
    # hint: kategoriespezifische Format-Anweisung (router/categories.py) —
    # kostet 0 Tokens (lokal!) und verhindert Judge-Fails wegen fehlender
    # Begruendung/Typ-Labels (Eval v2: 4 Sentiment-Fails nur deshalb).
    # Zusatzhinweis fuer Code-Aufgaben (Debugging/Generation): ohne diesen
    # erklaert das Modell den Code nur in Prosa, statt ihn zu liefern.
    hint_block = f"{hint}\n\n" if hint else ""
    prompt = (
        f"Question: {question}\n\n"
        f"{hint_block}"
        "Respond in exactly this format:\n"
        "ANSWER: <your answer, in English>\n"
        "CONFIDENCE: <number from 0 to 100, how sure you are>\n\n"
        "If the question asks you to write, fix, or generate code, the ANSWER "
        "must contain the actual code itself (e.g. a complete function), not "
        "a description of what the code does or what is wrong with it."
    )
    return ask_local_raw(prompt, model=model, temperature=temperature,
                         max_tokens=max_tokens, think=think)

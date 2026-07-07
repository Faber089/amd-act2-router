import re

from openai import OpenAI

from router import config

_client = OpenAI(base_url=config.LOCAL_BASE_URL, api_key="ollama")

# Manche Modelle (z. B. qwen3.5 als Eval-Judge) denken in <think>-Bloecken —
# die gehoeren nie in eine Antwort, die weiterverarbeitet oder bewertet wird.
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def ask_local_raw(prompt, model=None, temperature=None, max_tokens=None):
    """Schickt den Prompt unveraendert ans lokale Modell, ohne Format-Vorgabe."""
    model = model or config.LOCAL_MODEL
    response = _client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=config.LOCAL_TEMPERATURE if temperature is None else temperature,
        # Deckelt die Generierungsdauer: auf unbekannter Judging-Hardware darf
        # eine ausufernde lokale Antwort nie das 30s-Budget sprengen.
        max_tokens=config.LOCAL_MAX_TOKENS if max_tokens is None else max_tokens,
    )
    text = _THINK_RE.sub("", response.choices[0].message.content or "").strip()
    return text, 0  # lokale Tokens zaehlen immer als 0


def ask_local(question, model=None, temperature=None, hint=None, max_tokens=None):
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
    return ask_local_raw(prompt, model=model, temperature=temperature, max_tokens=max_tokens)

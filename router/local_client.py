from openai import OpenAI

from router import config

_client = OpenAI(base_url=config.LOCAL_BASE_URL, api_key="ollama")


def ask_local_raw(prompt, model=None):
    """Schickt den Prompt unveraendert ans lokale Modell, ohne Format-Vorgabe."""
    model = model or config.LOCAL_MODEL
    response = _client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.choices[0].message.content
    return text, 0  # lokale Tokens zaehlen immer als 0


def ask_local(question, model=None):
    # Prompt-Text muss Englisch sein: alle Antworten muessen laut Participant
    # Guide auf Englisch sein, egal welche Sprache die Aufgabe selbst hat.
    # Zusatzhinweis fuer Code-Aufgaben (Debugging/Generation): ohne diesen
    # erklaert das Modell den Code nur in Prosa, statt ihn zu liefern.
    prompt = (
        f"Question: {question}\n\n"
        "Respond in exactly this format:\n"
        "ANSWER: <your answer, in English>\n"
        "CONFIDENCE: <number from 0 to 100, how sure you are>\n\n"
        "If the question asks you to write, fix, or generate code, the ANSWER "
        "must contain the actual code itself (e.g. a complete function), not "
        "a description of what the code does or what is wrong with it."
    )
    return ask_local_raw(prompt, model=model)

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
    prompt = (
        f"Frage: {question}\n\n"
        "Antworte in genau diesem Format:\n"
        "ANTWORT: <deine Antwort>\n"
        "VERTRAUEN: <Zahl von 0 bis 100, wie sicher du dir bist>"
    )
    return ask_local_raw(prompt, model=model)

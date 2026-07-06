from openai import OpenAI

from router import config

_client = OpenAI(
    base_url=config.REMOTE_BASE_URL,
    api_key=config.FIREWORKS_API_KEY,
)


def ask_remote(question, model=None):
    model = model or config.REMOTE_MODEL
    # Kuerze-Anweisung: kostet ~10 Prompt-Tokens, spart oft hunderte
    # Completion-Tokens — und knappe Antworten schneiden bei grossen Modellen
    # in Benchmarks sogar besser ab (Concise-CoT-Forschung). max_tokens als
    # harte Obergrenze gegen Ausreisser.
    prompt = (
        f"{question}\n\n"
        "Answer concisely and directly, no preamble. "
        "If code is requested, provide the actual code."
    )
    response = _client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=config.REMOTE_MAX_TOKENS,
    )
    text = response.choices[0].message.content
    tokens = response.usage.total_tokens
    return text, tokens

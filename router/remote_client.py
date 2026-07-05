from openai import OpenAI

from router import config

_client = OpenAI(
    base_url=config.REMOTE_BASE_URL,
    api_key=config.FIREWORKS_API_KEY,
)


def ask_remote(question, model=None):
    model = model or config.REMOTE_MODEL
    response = _client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": question}],
    )
    text = response.choices[0].message.content
    tokens = response.usage.total_tokens
    return text, tokens

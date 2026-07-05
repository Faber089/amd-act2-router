import os
from openai import OpenAI

api_key = os.environ.get("FIREWORKS_API_KEY")
if not api_key:
    raise SystemExit("FIREWORKS_API_KEY ist nicht gesetzt. Siehe Anleitung.")

client = OpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key=api_key,
)

response = client.chat.completions.create(
    model="accounts/fireworks/models/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "Nenne mir 3 Hauptstädte in Europa."}
    ],
)

print("Antwort:", response.choices[0].message.content)
print("Prompt-Tokens:", response.usage.prompt_tokens)
print("Antwort-Tokens:", response.usage.completion_tokens)
print("Gesamt-Tokens:", response.usage.total_tokens)

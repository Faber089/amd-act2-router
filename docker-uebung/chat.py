from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

response = client.chat.completions.create(
    model="qwen3.5:latest",
    messages=[
        {"role": "user", "content": "Nenne mir 3 Hauptstädte in Europa."}
    ],
)

print("Antwort:", response.choices[0].message.content)
print("Prompt-Tokens:", response.usage.prompt_tokens)
print("Antwort-Tokens:", response.usage.completion_tokens)
print("Gesamt-Tokens:", response.usage.total_tokens)

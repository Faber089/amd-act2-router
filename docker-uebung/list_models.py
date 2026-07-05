import os
from openai import OpenAI

api_key = os.environ.get("FIREWORKS_API_KEY")

client = OpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key=api_key,
)

models = client.models.list()
for m in models.data:
    print(m.id)

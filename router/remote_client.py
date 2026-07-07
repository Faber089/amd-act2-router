import re

from openai import OpenAI

from router import config

# timeout: ein haengender HTTP-Call darf nie das 30s-pro-Aufgabe-Limit reissen.
# max_retries=1: EIN Wiederholungsversuch bei transienten Fehlern (429/5xx) —
# jeder abgeschlossene Call zaehlt Tokens, unbegrenzte Retries waeren teuer.
_client = OpenAI(
    base_url=config.REMOTE_BASE_URL,
    api_key=config.FIREWORKS_API_KEY,
    timeout=config.REMOTE_TIMEOUT_SECONDS,
    max_retries=1,
)

# Reasoning-Modelle (kimi-k2p7-code, minimax-m3) koennen Denk-Bloecke in den
# Antworttext leaken — die wuerden vom Wettbewerbs-Judge als Rauschen gewertet.
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def ask_remote(question, model=None, max_tokens=None, stats=None, reasoning_effort=None):
    model = model or config.REMOTE_MODEL
    # Kuerze-Anweisung: kostet ~19 Prompt-Tokens, spart oft hunderte
    # Completion-Tokens — und knappe Antworten schneiden bei grossen Modellen
    # in Benchmarks sogar besser ab (Concise-CoT-Forschung). max_tokens als
    # harte Obergrenze gegen Ausreisser.
    prompt = (
        f"{question}\n\n"
        "Answer concisely and directly, no preamble. "
        "If code is requested, provide the actual code."
    )
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens or config.REMOTE_MAX_TOKENS,
        "temperature": config.REMOTE_TEMPERATURE,
    }
    # Denk-Tokens abschalten (gemessen: 40 -> 3 completion_tokens bei
    # Ein-Wort-Antworten). Der Wettbewerbs-Proxy ist ein unbekannter Wrapper:
    # lehnt er den Parameter ab (400), Call einmal OHNE wiederholen — lieber
    # Denk-Tokens zahlen als gar keine Antwort.
    effort = config.REMOTE_REASONING_EFFORT if reasoning_effort is None else reasoning_effort
    if effort:
        kwargs["extra_body"] = {"reasoning_effort": effort}
    try:
        response = _client.chat.completions.create(**kwargs)
    except Exception as exc:
        if "extra_body" in kwargs and "400" in str(exc):
            kwargs.pop("extra_body")
            response = _client.chat.completions.create(**kwargs)
        else:
            raise
    text = _THINK_RE.sub("", response.choices[0].message.content or "").strip()
    usage = response.usage
    tokens = usage.total_tokens
    if stats is not None:
        # Telemetrie fuer die Eval: Prompt/Completion getrennt (versteckte
        # Denk-Tokens eines Reasoning-Modells zeigen sich als completion_tokens
        # weit ueber der sichtbaren Antwortlaenge) + Truncation-Erkennung.
        stats["remote_model"] = model
        stats["remote_prompt_tokens"] = usage.prompt_tokens
        stats["remote_completion_tokens"] = usage.completion_tokens
        stats["remote_finish_reason"] = response.choices[0].finish_reason
    return text, tokens

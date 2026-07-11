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


def resolve_model(preference):
    """Multi-Modell-Routing: findet das erste Modell aus ALLOWED_MODELS
    (Laufzeit-Env, nie hardcoden!), dessen ID den Praeferenz-Substring
    enthaelt. Kein Treffer -> Default-Modell. So kann die Kategorie-Politik
    z. B. Logik auf gemma-4-26b-a4b schicken, ohne dass ein falscher/alter
    Modellname je einen MODEL_VIOLATION ausloest."""
    if preference:
        for m in config.ALLOWED_MODELS:
            if preference in m:
                return m
    return config.REMOTE_MODEL


def ask_remote(question, model=None, max_tokens=None, stats=None, reasoning_effort=None,
               hint=None):
    model = model or config.REMOTE_MODEL
    # Prompt-Diaet (gemessen 7.7. abends): mit reasoning_effort=none antwortet
    # Kimi von sich aus knapp (2-6 completion-Tokens bei Kurzantwort-Aufgaben)
    # — die fruehere pauschale Kuerze-Anweisung (~19 Prompt-Tokens/Call) ist
    # ueberfluessig. Nur die Kategorie-Politik haengt noch gezielt einen Hint
    # an: Kurz-CoT fuer Logik (ohne CoT nachweislich 0/2 richtig) bzw.
    # Code-only-Hinweis fuer Code-Aufgaben.
    prompt = f"{question}\n\n{hint}" if hint else question
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
        elif (kwargs["model"] != config.REMOTE_MODEL
                and ("404" in str(exc) or "NOT_FOUND" in str(exc))):
            # Ein per Politik gewaehltes Alternativ-Modell ist auf dem
            # Wettbewerbs-Proxy nicht verfuegbar -> einmal mit dem Default-
            # Modell wiederholen statt die Aufgabe zu verlieren.
            kwargs["model"] = config.REMOTE_MODEL
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

"""
Jury-naher LLM-Judge — NUR fuer die eigene Eval, NIE Teil der Submission.

Der echte Wettbewerbs-Judge (Participant Guide, woertlich): "LLM-Judge
evaluates each answer against the expected intent." Modell und Schwelle sind
geheim. Beste Annaeherung an die Jury:
  * ein STARKES Modell statt gemma2:2b (ein 2B-Modell ist als Richter zu
    schwach und bewertet zu milde — die alte semantic_judge()-Messung hat
    die Jury systematisch unterschaetzt/verzerrt),
  * dieselbe Rubrik-Formulierung wie im Guide ("expected intent"),
  * defaultmaessig eine ANDERE Modellfamilie (minimax-m3) als das
    Eskalationsmodell (kimi) — Judges bevorzugen nachweislich Antworten aus
    der eigenen Familie (Self-Preference-Bias).

Backends (Env: EVAL_JUDGE_BACKEND=remote|local):
  remote (Default): minimax-m3 ueber den EIGENEN Fireworks-Key. Kostet
    Cent-Betraege pro Lauf (Dev-Budget, zaehlt NICHT fuers Leaderboard) und
    laeuft parallel -> schnell.
  local: qwen3.5 via Ollama — kostenlos/offline, aber langsamer (CPU) und
    etwas schwaecher. Fallback, wenn Credits geschont werden sollen.
"""
import re
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI

from router import config

_JUDGE_PROMPT = """You are the evaluation judge of an AI competition.

TASK given to the agent:
{question}

EXPECTED INTENT (reference for a correct answer — different wording is fine):
{expected}

AGENT'S ANSWER:
{answer}

Judge whether the agent's answer correctly fulfills the expected intent of the task.
- Correct content in different wording is CORRECT.
- Wrong facts, wrong numbers, wrong labels, missing required parts, empty,
  non-English, or clearly truncated answers are INCORRECT.
- If the task demands a specific format or length (e.g. "only the number",
  "one sentence", "three bullet points"), major violations are INCORRECT.

Reply with exactly one word: CORRECT or INCORRECT."""

# INCORRECT zuerst pruefen und den LETZTEN Treffer nehmen: Reasoning-Modelle
# diskutieren manchmal beide Woerter, das Verdikt steht am Ende.
_VERDICT_RE = re.compile(r"\b(INCORRECT|CORRECT)\b", re.IGNORECASE)

_remote_client = None


def _get_remote_client():
    global _remote_client
    if _remote_client is None:
        _remote_client = OpenAI(
            base_url=config.REMOTE_BASE_URL,
            api_key=config.FIREWORKS_API_KEY,
            timeout=90,
            max_retries=2,
        )
    return _remote_client


def _parse_verdict(text):
    hits = _VERDICT_RE.findall(text or "")
    if not hits:
        return False  # kein Verdikt = streng werten (wie eine echte Jury)
    return hits[-1].upper() == "CORRECT"


def judge_one(question, answer, expected, backend=None, model=None):
    """Bewertet EINE Antwort. Rueckgabe: (correct: bool, judge_dev_tokens: int).
    judge_dev_tokens ist reiner Entwicklungs-Kostenzaehler (eigener Key),
    hat nichts mit dem Leaderboard zu tun."""
    backend = backend or config.EVAL_JUDGE_BACKEND
    prompt = _JUDGE_PROMPT.format(
        question=question, expected=expected, answer=(answer or "").strip() or "(empty)"
    )
    if backend == "remote":
        response = _get_remote_client().chat.completions.create(
            model=model or config.EVAL_JUDGE_MODEL,
            messages=[{"role": "user", "content": prompt}],
            # Reasoning-Modell: genug Platz zum Denken lassen, sonst wird das
            # Verdikt abgeschnitten und faelschlich als INCORRECT gewertet.
            max_tokens=2048,
            temperature=0,
        )
        message = response.choices[0].message
        # Manche Reasoning-Modelle liefern Denkspur separat (reasoning_content)
        # und das Verdikt in content — beides absuchen, content gewinnt zuletzt.
        text = f"{getattr(message, 'reasoning_content', None) or ''}\n{message.content or ''}"
        return _parse_verdict(text), response.usage.total_tokens
    else:
        from router.local_client import ask_local_raw

        text, _ = ask_local_raw(
            prompt,
            model=model or config.EVAL_JUDGE_LOCAL_MODEL,
            temperature=0,
            max_tokens=1024,
        )
        return _parse_verdict(text), 0


def judge_many(items, backend=None, max_workers=8):
    """Bewertet viele Antworten. items: Liste von Dicts mit question/answer/
    expected. Remote parallel (ThreadPool), lokal seriell (Ollama-CPU).
    Rueckgabe: Liste (correct, judge_dev_tokens) in Eingabereihenfolge."""
    backend = backend or config.EVAL_JUDGE_BACKEND
    if backend != "remote":
        return [
            judge_one(it["question"], it["answer"], it["expected"], backend=backend)
            for it in items
        ]
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            pool.submit(judge_one, it["question"], it["answer"], it["expected"], backend)
            for it in items
        ]
        results = []
        for future in futures:
            try:
                results.append(future.result())
            except Exception:
                # Ein einzelner Judge-Fehler (Netz, Timeout) soll den Lauf
                # nicht killen: streng als INCORRECT werten und weiter.
                results.append((False, 0))
        return results

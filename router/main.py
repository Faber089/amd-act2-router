from router import config
from router.local_client import ask_local
from router.remote_client import ask_remote
from router.judge import parse_local_answer, critique


def route(question, confidence_threshold=None, local_model=None,
          use_critique=None, verbose=True):
    """
    Cascade-Router: erst lokal (0 Tokens), bei Unsicherheit remote (Tokens zaehlen).
    Alle Parameter fallen auf die zentrale Config zurueck, wenn nicht gesetzt.
    """
    confidence_threshold = (
        config.CONFIDENCE_THRESHOLD if confidence_threshold is None else confidence_threshold
    )
    local_model = local_model or config.LOCAL_MODEL
    use_critique = config.USE_CRITIQUE if use_critique is None else use_critique

    local_text, _ = ask_local(question, model=local_model)
    answer, is_trustworthy, confidence = parse_local_answer(
        local_text, threshold=confidence_threshold
    )

    escalate = not is_trustworthy
    reason = f"Vertrauen={confidence} < {confidence_threshold}"

    # Optionale zweite, skeptische Pruefung (immer noch lokal, 0 Tokens).
    if is_trustworthy and use_critique:
        if not critique(question, answer, model=local_model):
            escalate = True
            reason = f"Vertrauen={confidence} ok, aber Kritiker sieht Fehler"

    if not escalate:
        if verbose:
            print(f"[LOKAL, Vertrauen={confidence}] -> keine Eskalation, 0 Tokens")
        return answer, 0, "local"

    if verbose:
        print(f"[ESKALATION: {reason}] -> Fireworks")
    remote_text, remote_tokens = ask_remote(question)
    return remote_text, remote_tokens, "remote"


if __name__ == "__main__":
    frage = "Nenne mir 3 Hauptstaedte in Europa."
    antwort, tokens, quelle = route(frage)
    print(f"\nQuelle: {quelle}")
    print(f"Antwort: {antwort}")
    print(f"Verbrauchte Tokens (fuers Leaderboard): {tokens}")

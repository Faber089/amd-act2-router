import re

from router import config
from router.local_client import ask_local
from router.remote_client import ask_remote
from router.judge import parse_local_answer, critique


def _norm(s):
    """Antworten fuer den Konsistenz-Vergleich vereinheitlichen."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def route(question, confidence_threshold=None, local_model=None,
          use_critique=None, verbose=True, stats=None):
    """
    Cascade-Router: erst lokal (0 Tokens), bei Unsicherheit remote (Tokens zaehlen).
    Alle Parameter fallen auf die zentrale Config zurueck, wenn nicht gesetzt.
    stats: optionales dict — wird, falls uebergeben, mit Diagnose-Werten
    gefuellt (confidence), ohne die Rueckgabe-Signatur zu aendern.
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
    if stats is not None:
        stats["confidence"] = confidence

    escalate = not is_trustworthy
    reason = f"Vertrauen={confidence} < {confidence_threshold}"

    # Optionale zweite, skeptische Pruefung (immer noch lokal, 0 Tokens).
    if is_trustworthy and use_critique:
        if not critique(question, answer, model=local_model):
            escalate = True
            reason = f"Vertrauen={confidence} ok, aber Kritiker sieht Fehler"

    # Selbst-Konsistenz-Check (lokal = 0 Tokens): kurze Antworten ein zweites
    # Mal erfragen; weicht die Zweitantwort ab, ist die Antwort instabil ->
    # eskalieren. Faengt selbstbewusst-falsche Antworten (Confidence 100 bei
    # grossen Rechnungen / obskurem Wissen), die die Confidence-Zahl allein
    # nicht erkennt.
    if (not escalate and config.USE_SELFCHECK
            and len(answer) <= config.SELFCHECK_MAX_ANSWER_LEN):
        check_text, _ = ask_local(question, model=local_model)
        check_answer, _, _ = parse_local_answer(check_text, threshold=confidence_threshold)
        if _norm(check_answer) != _norm(answer):
            escalate = True
            reason = f"Selbst-Check widerspricht ('{answer[:30]}' vs '{check_answer[:30]}')"
            if stats is not None:
                stats["selfcheck_disagreed"] = True

    if not escalate:
        if verbose:
            print(f"[LOKAL, Vertrauen={confidence}] -> keine Eskalation, 0 Tokens")
        return answer, 0, "local"

    if verbose:
        print(f"[ESKALATION: {reason}] -> Fireworks")
    try:
        remote_text, remote_tokens = ask_remote(question)
    except Exception as exc:
        # Remote kaputt/nicht erreichbar: die unsichere lokale Antwort ist
        # strikt besser als eine leere — leer faellt beim Accuracy-Gate
        # garantiert durch, die lokale Antwort hat zumindest eine Chance.
        if verbose:
            print(f"[REMOTE-FEHLER: {exc}] -> Fallback auf lokale Antwort")
        return answer, 0, "local-fallback"
    return remote_text, remote_tokens, "remote"


if __name__ == "__main__":
    frage = "Nenne mir 3 Hauptstaedte in Europa."
    antwort, tokens, quelle = route(frage)
    print(f"\nQuelle: {quelle}")
    print(f"Antwort: {antwort}")
    print(f"Verbrauchte Tokens (fuers Leaderboard): {tokens}")

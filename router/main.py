import re
import time

from router import config
from router.categories import (
    SUMMARISATION_ALWAYS_ESCALATE,
    classify,
    format_number,
    get_policy,
    math_answers_disagree,
    merge_entities,
    normalize_entities,
    numbers_in,
    postprocess_answer,
    safe_eval_expression,
    summarisation_format_violated,
)
from router.judge import (
    critique,
    extract_code,
    is_valid_python,
    looks_like_code,
    parse_local_answer,
)
from router.local_client import ask_local, ask_local_raw
from router.remote_client import ask_remote, resolve_model


def _norm(s):
    """Antworten fuer den Konsistenz-Vergleich vereinheitlichen."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


_SENTIMENT_LABEL_RE = re.compile(r"\b(positive|negative|neutral|mixed)\b", re.I)
_TWO_PART_RE = re.compile(
    r",\s*and\s+(what|which|who|when|where|how|in which)\b", re.I)


def _local_math_expression(question, local_model, temperature=None):
    """Laesst das lokale Modell die Aufgabe in einen reinen Arithmetik-
    Ausdruck uebersetzen und wertet ihn sicher aus. None = kein brauchbarer
    Ausdruck. Kostet 0 Tokens, nur lokale Rechenzeit."""
    expr_text, _ = ask_local_raw(
        f"Task: {question}\n"
        "Write ONE single Python arithmetic expression that computes the "
        "final answer. Reply with ONLY the expression — no words, no "
        "backticks, no equals sign.",
        model=local_model,
        max_tokens=64,
        temperature=temperature,
    )
    if not expr_text.strip():
        return None
    expr_line = expr_text.strip().splitlines()[-1].strip("` ")
    return safe_eval_expression(expr_line)


def _ask_remote_with_policy(question, policy, stats):
    """Eskalation mit Kategorie-Feintuning: eigener max_tokens-Deckel,
    reasoning_effort (Denk-Tokens aus) und Hint nur wo noetig (Kurz-CoT
    fuer Logik, Code-only fuer Code-Aufgaben — sonst nackte Frage)."""
    text, tokens = ask_remote(
        question,
        model=resolve_model(policy.get("remote_model")),
        max_tokens=policy.get("remote_max_tokens"),
        stats=stats,
        reasoning_effort=policy.get("remote_effort"),
        hint=policy.get("remote_hint"),
    )
    # Kurz-CoT darf bei "only the number/name"-Aufgaben nicht in der
    # finalen Antwort landen — nur den Wert hinter 'Answer:' ausliefern.
    return postprocess_answer(question, text), tokens


def route(question, confidence_threshold=None, local_model=None,
          use_critique=None, verbose=True, stats=None):
    """
    Cascade-Router: erst lokal (0 Tokens), bei Unsicherheit remote (Tokens zaehlen).
    Alle Parameter fallen auf die zentrale Config zurueck, wenn nicht gesetzt.
    stats: optionales dict — wird, falls uebergeben, mit Diagnose-Werten
    gefuellt (confidence, category, escalation_reason, Token-Split), ohne die
    Rueckgabe-Signatur zu aendern.
    """
    confidence_threshold = (
        config.CONFIDENCE_THRESHOLD if confidence_threshold is None else confidence_threshold
    )
    local_model = local_model or config.LOCAL_MODEL
    use_critique = config.USE_CRITIQUE if use_critique is None else use_critique

    category = classify(question)
    policy = get_policy(category)
    if stats is not None:
        stats["category"] = category

    # Lokal aussichtslose Kategorien sofort eskalieren. Datenlage (Eval v2,
    # 7.7.): logic_puzzle lokal 3/8 korrekt und ALLE Fehler mit Confidence
    # 100 — die Kaskade kann diese Fehler nicht erkennen, nur vermeiden.
    escalate_pattern = policy.get("escalate_if")
    if policy.get("always_escalate") or (escalate_pattern and escalate_pattern.search(question)):
        if stats is not None:
            stats["escalation_reason"] = f"policy: {category} direkt remote"
        if verbose:
            print(f"[POLICY: {category} -> direkt remote]")
        try:
            answer, tokens = _ask_remote_with_policy(question, policy, stats)
            return answer, tokens, "remote"
        except Exception as exc:
            if verbose:
                print(f"[REMOTE-FEHLER: {exc}] -> lokaler Notversuch")
            # faellt durch in den lokalen Pfad — besser als leere Antwort

    # Zeitbudget fuer alle lokalen Schritte dieser Aufgabe (2-vCPU-VM:
    # gestapelte lokale Calls rissen in der Simulation fast das 30s-Limit).
    route_start = time.monotonic()

    def local_time_left():
        return config.LOCAL_TIME_BUDGET_SECONDS - (time.monotonic() - route_start)

    local_text, _ = ask_local(
        question,
        model=local_model,
        hint=policy.get("local_hint"),
        max_tokens=policy.get("local_max_tokens"),
        think=policy.get("local_think"),
    )
    answer, is_trustworthy, confidence = parse_local_answer(
        local_text, threshold=confidence_threshold,
        default_confidence=policy.get("default_confidence", 0),
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
    # eskalieren. Der Zweitlauf sampelt bewusst mit Temperatur >0: die
    # Hauptantwort ist deterministisch (temperature 0), erst ein gesampelter
    # Gegenlauf macht Instabilitaet ueberhaupt sichtbar.
    if (not escalate and config.USE_SELFCHECK
            and not policy.get("skip_selfcheck")
            and len(answer) <= config.SELFCHECK_MAX_ANSWER_LEN
            and local_time_left() > 6):
        check_text, _ = ask_local(
            question,
            model=local_model,
            temperature=config.SELFCHECK_TEMPERATURE,
            hint=policy.get("local_hint"),
            max_tokens=policy.get("local_max_tokens"),
            think=policy.get("local_think"),
        )
        check_answer, _, _ = parse_local_answer(check_text, threshold=confidence_threshold)
        # Zahlen numerisch vergleichen: '30' vs '30.0' ist KEIN Widerspruch
        # (gemessen: 35 verschenkte Tokens durch genau diesen Fall — die
        # String-Normalisierung macht aus '30.0' sonst '300').
        nums_a, nums_b = numbers_in(answer), numbers_in(check_answer)
        numerically_equal = (
            len(nums_a) == 1 and len(nums_b) == 1
            and abs(nums_a[0] - nums_b[0]) < max(1e-9, abs(nums_a[0]) * 1e-9)
        )
        if not numerically_equal and _norm(check_answer) != _norm(answer):
            escalate = True
            reason = f"Selbst-Check widerspricht ('{answer[:30]}' vs '{check_answer[:30]}')"
            if stats is not None:
                stats["selfcheck_disagreed"] = True

    # Mathe-Gegenrechnung (lokal + deterministisch, 0 Tokens): das lokale
    # Modell uebersetzt die Aufgabe in EINEN Arithmetik-Ausdruck, Python
    # rechnet nach. Widerspruch zur direkten Antwort -> eines von beiden ist
    # falsch -> eskalieren (~35 Tokens). KEIN 2:1-Override durch einen
    # Doppel-Ausdruck (getestet 8.7.): beide Ausdruecke machen oft DENSELBEN
    # Uebersetzungsfehler und ueberstimmen dann eine korrekte Direktantwort.
    if not escalate and policy.get("math_crosscheck"):
        if local_time_left() <= 6:
            # Keine Zeit mehr fuer die Gegenrechnung: ungeprueftes Mathe ist
            # zu riskant (confident-wrong!) -> lieber die schnelle Eskalation.
            escalate = True
            reason = "Zeitbudget: Mathe-Gegenrechnung nicht mehr moeglich"
        else:
            expr_result = _local_math_expression(question, local_model)
            if stats is not None:
                stats["math_crosscheck_result"] = expr_result
            if math_answers_disagree(answer, expr_result):
                escalate = True
                reason = f"Gegenrechnung widerspricht (Ausdruck ergibt {expr_result})"
                if stats is not None:
                    stats["math_crosscheck_disagreed"] = True

    # Summarisation-Format-Gate (lokal = 0 Tokens): geforderte Satzzahl/
    # Wortlimit/Bullet-Anzahl aus der Aufgabe parsen und pruefen. Ein
    # Formatverstoss ist ein sicherer Judge-Fail — dann lieber eskalieren.
    # Env SUMMARISATION_ALWAYS_ESCALATE=1 als harte Variante, falls das
    # Leaderboard zeigt, dass die lokale Summarisation-Qualitaet nicht reicht.
    if not escalate and category == "summarisation":
        if SUMMARISATION_ALWAYS_ESCALATE:
            escalate = True
            reason = "Politik: Summarisation immer eskalieren (Env-Schalter)"
        elif summarisation_format_violated(question, answer):
            escalate = True
            reason = "Summarisation-Formatvorgabe verletzt"
            if stats is not None:
                stats["summary_format_violated"] = True

    # NER-Vereinigungsmenge (0 Tokens): der Zweitlauf findet oft Entitaeten,
    # die der Erstlauf ausgelassen hat (Eval v2: alle NER-Fails waren
    # FEHLENDE Entitaeten, nie erfundene). Nur ergaenzen, nie ersetzen.
    if not escalate and policy.get("entity_union") and local_time_left() > 5:
        try:
            second_text, _ = ask_local(
                question,
                model=local_model,
                temperature=config.SELFCHECK_TEMPERATURE,
                hint=policy.get("local_hint"),
                max_tokens=policy.get("local_max_tokens"),
                think=policy.get("local_think"),
            )
            second_answer, _, _ = parse_local_answer(
                second_text, threshold=confidence_threshold
            )
            merged = merge_entities(answer, second_answer)
            if merged:
                answer = merged
                if stats is not None:
                    stats["entity_union_added"] = True
        except Exception:
            pass
        # Zerhackte Mehrwort-Namen reparieren ('Maria (PERSON); Sanchez
        # (PERSON)' -> 'Maria Sanchez (PERSON)') — deterministisch, 0 Tokens.
        normalized = normalize_entities(question, answer)
        if normalized:
            answer = normalized

    # Objektiver Code-Check (lokal = 0 Tokens, kein exec, nur ast.parse):
    # deckt Code Debugging/Generation ab, wo Selbst-Konsistenz wegen der
    # Antwortlaenge nicht greift. Syntaktisch kaputter Code kann in keiner
    # der beiden Kategorien jemals korrekt sein -> zwingend eskalieren.
    if not escalate and looks_like_code(answer):
        code = extract_code(answer)
        if not is_valid_python(code):
            escalate = True
            reason = f"Vertrauen={confidence} ok, aber Code-Syntax ungueltig"
            if stats is not None:
                stats["code_syntax_invalid"] = True
        # Debugging-Spezialfall (Eval v2): Modell gibt den Original-Code
        # unveraendert als "Fix" zurueck — dann wurde nichts repariert.
        elif policy.get("reject_identical") and code and _norm(code) in _norm(question):
            escalate = True
            reason = "Antwort-Code ist identisch mit dem fehlerhaften Original"
            if stats is not None:
                stats["identical_code"] = True

    # Code-Pflicht (11.7.): Debugging-/Codegen-Antworten, die den Fix nur in
    # PROSA beschreiben statt Code zu liefern, sind sichere Judge-Fails
    # (3 Fails im qwen3-Router-Lauf). Ohne Code -> eskalieren.
    if not escalate and policy.get("require_code") and not looks_like_code(answer):
        escalate = True
        reason = "Code-Aufgabe, aber keine Code-Antwort"
        if stats is not None:
            stats["no_code_answer"] = True

    # Label-Selfcheck fuer Sentiment (11.7., billiger als der volle
    # Selbstkonsistenz-Check): (a) mehrteilige Aufgaben ((1)...(2)...) muessen
    # pro Teil ein Label liefern (Fail 143: nur Teil 1 beantwortet),
    # (b) das Label des Zweitlaufs muss zum Erstlauf passen (Fails 133/136:
    # instabile Labels bei neutralen Texten). Nur Label vergleichen, nicht
    # den Begruendungstext — der variiert immer.
    if not escalate and policy.get("label_selfcheck"):
        parts = len(re.findall(r"\(\d\)", question))
        labels_found = _SENTIMENT_LABEL_RE.findall(answer)
        if parts >= 2 and len(labels_found) < parts:
            escalate = True
            reason = f"mehrteilige Sentiment-Aufgabe: {len(labels_found)}/{parts} Labels"
        elif not labels_found:
            escalate = True
            reason = "kein Sentiment-Label in der Antwort erkennbar"
        elif local_time_left() > 5:
            check_text, _ = ask_local(
                question,
                model=local_model,
                temperature=config.SELFCHECK_TEMPERATURE,
                hint=policy.get("local_hint"),
                max_tokens=policy.get("local_max_tokens"),
                think=policy.get("local_think"),
            )
            check_answer, _, _ = parse_local_answer(
                check_text, threshold=confidence_threshold
            )
            check_label = _SENTIMENT_LABEL_RE.search(check_answer)
            if check_label and check_label.group(1).lower() != labels_found[0].lower():
                escalate = True
                reason = (f"Label-Selfcheck widerspricht "
                          f"('{labels_found[0]}' vs '{check_label.group(1)}')")
                if stats is not None:
                    stats["label_selfcheck_disagreed"] = True

    # Zweiteilige Wissensfragen (Practice-Task-Stil "..., and what/which..."):
    # eine verdaechtig kurze Antwort beantwortet fast sicher nur einen Teil
    # (qwen3-Lauf 11.7., Fail 109: 'France' ohne das Jahrzehnt). Die
    # Eskalation kostet ~25-30 Tokens — billiger als ein Gate-Fail.
    if (not escalate and category == "factual_knowledge"
            and _TWO_PART_RE.search(question) and len(answer.strip()) < 40):
        escalate = True
        reason = "zweiteilige Frage, verdaechtig kurze Antwort"

    # Sentiment-Sicherheitsnetz (Eval v2: 5 Judge-Fails, weil gemma2:2b nur
    # das nackte Label lieferte, obwohl die Aufgabe eine Begruendung verlangt).
    # Nacktes Label erkannt -> Begruendung lokal nachfordern (0 Tokens) und
    # anhaengen. Bewusst NACH dem Selbst-Konsistenz-Check, der das rohe Label
    # vergleicht. Schlaegt es fehl, bleibt das Label allein stehen.
    if (not escalate and policy.get("needs_justification")
            and len(answer.strip()) < 25 and local_time_left() > 4):
        try:
            reason_text, _ = ask_local_raw(
                f"Text: {question}\n"
                f"The sentiment label is: {answer.strip()}\n"
                "In ONE short English sentence, justify why this label fits. "
                "Reply with only that sentence.",
                model=local_model,
                max_tokens=60,
            )
            reason_line = reason_text.strip().splitlines()[0] if reason_text.strip() else ""
            if reason_line:
                answer = f"{answer.strip()} - {reason_line}"
        except Exception:
            pass

    if not escalate:
        if verbose:
            print(f"[LOKAL, Vertrauen={confidence}] -> keine Eskalation, 0 Tokens")
        # postprocess auch lokal: '$83,600' bei "only the number" waere ein
        # Formatverstoss, egal woher die Antwort kommt.
        return postprocess_answer(question, answer), 0, "local"

    if stats is not None:
        stats["escalation_reason"] = reason
    if verbose:
        print(f"[ESKALATION: {reason}] -> Fireworks")
    try:
        remote_text, remote_tokens = _ask_remote_with_policy(question, policy, stats)
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

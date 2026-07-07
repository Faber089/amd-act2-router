"""
Kategorie-Erkennung + Politik pro Aufgabentyp. Alles lokal/regelbasiert =
0 Tokens. Datenbasis: Eval-v2-Lauf vom 7.7. (64 Aufgaben, jury-naher Judge):

  * logic_puzzle lokal 3/8 korrekt, alle Fehler mit Confidence 100
    -> lokal chancenlos UND unerkennbar: immer eskalieren.
  * sentiment 8/8 Label korrekt, aber 4/8 vom Judge abgelehnt weil die
    verlangte Begruendung fehlte -> Format-Hint an das lokale Modell.
  * ner: 1 Judge-Fail weil Entitaeten ohne Typ-Label -> Format-Hint.
  * math: 2 lokale Fehler (Zinseszins, Prozent-Summe) mit Conf 95-100 ->
    Gegenrechnung ueber einen lokal generierten, sicher ausgewerteten
    Python-Ausdruck; Widerspruch -> eskalieren.
  * code_debugging: 1 Fall gab den Original-Code unveraendert als "Fix"
    zurueck -> identische Antwort erkennen und eskalieren.
  * Eskalationen: Kimi-Denk-Tokens per reasoning_effort steuern — "none"
    fuer Wissens-/Format-Aufgaben, sichtbares Kurz-CoT statt verstecktem
    Denken fuer Mathe/Logik (kontrollierbar ueber max_tokens).
"""
import ast
import re

# --- Kategorie-Erkennung (Reihenfolge = Prioritaet) ---

_RULES = [
    ("summarisation", re.compile(r"summari[sz]e|write a headline|bullet points", re.I)),
    ("sentiment", re.compile(r"sentiment", re.I)),
    ("ner", re.compile(r"named entit|entities|labelled by type|label each entity", re.I)),
    ("code_debugging", re.compile(r"find the bug|fix (this|the) (code|function)|corrected version|debug", re.I)),
    ("code_generation", re.compile(r"write a (python )?function|implement (a|the) function", re.I)),
    ("logic_puzzle", re.compile(
        r"knight|knave|liar|tells? the truth|labels? (is|are) wrong"
        r"|finished (before|after)|older than|younger than"
        r"|which day works|each (have|has|own)|exactly one", re.I)),
    ("math_reasoning", re.compile(
        r"(percent|%|\btimes\b|plus|minus|divided|discount|grows?|interest"
        r"|how (many|much)|total|average|price|cost|speed|per (year|month|hour))", re.I)),
]


def classify(question):
    for category, pattern in _RULES:
        if pattern.search(question):
            # Mathe-Regel feuert nur, wenn auch Ziffern vorkommen (sonst ist
            # "how many" oft eine Wissensfrage).
            if category == "math_reasoning" and not re.search(r"\d", question):
                continue
            return category
    return "factual_knowledge"


# --- Politik pro Kategorie ---
# local_hint: Zusatz fuer den lokalen Prompt (0 Tokens, erzwingt das Format,
#   das der Wettbewerbs-Judge laut Aufgabenstellung erwartet).
# remote_max_tokens / remote_effort: Eskalations-Steuerung. "none" schaltet
#   Kimis versteckte Denk-Tokens ab; Mathe/Logik bekommen stattdessen
#   sichtbares Kurz-CoT (remote_hint), dessen Laenge max_tokens deckelt —
#   sichtbares Denken ist steuerbar, verstecktes nicht.
# always_escalate: Kategorie ist lokal aussichtslos (Datenlage!).

_COT_HINT = "Think briefly step by step, then give the final line as 'Answer: <result>'."

POLICY = {
    "factual_knowledge": {"remote_max_tokens": 128, "remote_effort": "none"},
    "math_reasoning": {
        "remote_max_tokens": 300, "remote_effort": "none", "remote_hint": _COT_HINT,
        "math_crosscheck": True,
    },
    "sentiment": {
        "remote_max_tokens": 96, "remote_effort": "none",
        # Eval v2: ein weicher Hint wurde von gemma2:2b ignoriert (5 Judge-
        # Fails: Label ohne Begruendung). Deshalb Beispiel-Format vorgeben
        # UND main.py haengt notfalls eine nachgeforderte Begruendung an.
        "local_hint": ('Your ANSWER must follow exactly this pattern: '
                       '<label> - <one short reason>. Example: "negative - the '
                       'reviewer complains about slow delivery." Never answer '
                       'with the label alone.'),
        "needs_justification": True,
    },
    "summarisation": {
        "remote_max_tokens": 192, "remote_effort": "none",
        "local_hint": ("Obey the requested format EXACTLY (number of sentences, "
                       "word limit, bullet count) and keep the key facts and figures."),
    },
    "ner": {
        "remote_max_tokens": 128, "remote_effort": "none",
        "local_hint": ("List EVERY entity with its type label, e.g. "
                       "Tim Cook (PERSON); Apple (ORGANIZATION); Paris (LOCATION); 1911 (DATE)."),
    },
    "code_debugging": {
        "remote_max_tokens": 512, "remote_effort": "none",
        "local_max_tokens": 512, "reject_identical": True,
    },
    "logic_puzzle": {
        "always_escalate": True,
        # 400 statt 220: Eval v2 zeigte eine bei Token 313 abgeschnittene
        # CoT-Antwort ohne finale "Answer:"-Zeile -> Judge-Fail. Der Deckel
        # begrenzt nur den Schadensfall, normale Antworten bleiben kurz.
        "remote_max_tokens": 400, "remote_effort": "none", "remote_hint": _COT_HINT,
    },
    "code_generation": {
        "remote_max_tokens": 512, "remote_effort": "none",
        "local_max_tokens": 512,
    },
}


def get_policy(category):
    return POLICY.get(category, {})


# --- Mathe-Gegenrechnung (0 Tokens, deterministisch) ---

_ALLOWED_EXPR = re.compile(r"^[\d\s+\-*/().,%]+$")
_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def safe_eval_expression(expr):
    """Wertet einen REINEN Arithmetik-Ausdruck aus. Whitelist statt Sandbox:
    nur Ziffern/Operatoren/Klammern erlaubt, ast-geprueft, kein Namenszugriff
    moeglich -> eval ist hier sicher. Rueckgabe None wenn nicht auswertbar."""
    expr = expr.strip().rstrip("=").replace("^", "**").replace(",", "")
    if not expr or not _ALLOWED_EXPR.match(expr.replace("**", "")):
        return None
    try:
        tree = ast.parse(expr, mode="eval")
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Expression, ast.BinOp, ast.UnaryOp,
                                     ast.Constant, ast.operator, ast.unaryop)):
                return None
        return eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, {})
    except Exception:
        return None


def numbers_in(text):
    result = []
    for raw in _NUM_RE.findall((text or "").replace(",", "")):
        try:
            result.append(float(raw))
        except ValueError:
            pass
    return result


def math_answers_disagree(local_answer, expr_result):
    """True, wenn die direkte lokale Antwort dem Rechenergebnis widerspricht
    (dann ist mindestens eines falsch -> eskalieren)."""
    if expr_result is None:
        return False  # keine Gegenrechnung moeglich -> kein Urteil
    answer_numbers = numbers_in(local_answer)
    if not answer_numbers:
        return True  # Zahl gefordert, keine Zahl geliefert
    return not any(abs(n - expr_result) < max(1e-6, abs(expr_result) * 1e-9)
                   for n in answer_numbers)


# --- Antwort-Nachbearbeitung ---

_ONLY_RE = re.compile(r"answer with (?:only )?(?:the |a )?(number|name|day|word|yes or no)", re.I)
_FINAL_ANSWER_RE = re.compile(r"(?:^|\n)\s*Answer:\s*(.+?)\s*$", re.I | re.DOTALL)


def postprocess_answer(question, text):
    """Wenn die Aufgabe 'Answer with only the number/name/...' verlangt und
    die (Remote-)Antwort Kurz-CoT enthaelt, nur den finalen Wert ausliefern —
    der Judge soll keinen Formatverstoss sehen. Konservativ: nur eingreifen,
    wenn ein klarer 'Answer:'-Marker existiert."""
    if not text:
        return text
    match = _FINAL_ANSWER_RE.search(text)
    if match:
        final = match.group(1).strip()
        if _ONLY_RE.search(question):
            return final
        # Auch ohne "only"-Vorgabe: steht ein expliziter Answer-Marker am
        # Ende, ist alles davor Rechenweg — final reicht, spart nichts an
        # Tokens (schon bezahlt), aber haelt die Antwort judge-sauber...
        # ausser der Weg IST die geforderte Antwort (Erklaer-Aufgaben) ->
        # dann lieber alles behalten.
        if len(final) <= 80:
            return final
    return text

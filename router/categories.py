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

_COT_HINT = ("Think in at most 3 short steps, no restating the question, "
             "then give the final line as 'Answer: <result>'.")
_CODE_HINT = "State the bug in one short sentence, then give the complete corrected code."

# Token-Diaet-Experiment 7.7. spaetabends (nackte Frage, effort=none):
# Mathe 3/3 korrekt bei 2-3 completion-Tokens (inkl. Zinseszins, 347*289)
# -> Mathe braucht KEIN CoT. Logik 0/2 korrekt ohne CoT ("Ann", "apples")
# -> Logik BEHAELT das Kurz-CoT zwingend. Factual korrekt ohne alles.
POLICY = {
    "factual_knowledge": {"remote_max_tokens": 128, "remote_effort": "none"},
    "math_reasoning": {
        "remote_max_tokens": 128, "remote_effort": "none",
        "math_crosscheck": True,
        # Zahl + kurzer Weg reichen lokal — kleiner Deckel = schnellere
        # Generierung auf der 2-vCPU-VM (Latenz, nicht Tokens).
        "local_max_tokens": 96,
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
        # VM-Simulation 8.7.: Antwort+Selfcheck+Nachforderung stapelten sich
        # auf 24,8s (30s-Limit!). Der Selfcheck bringt bei Sentiment am
        # wenigsten (Label-Stabilitaet war nie das Problem) -> raus.
        "skip_selfcheck": True,
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
        "remote_max_tokens": 512, "remote_effort": "none", "remote_hint": _CODE_HINT,
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
        "remote_max_tokens": 512, "remote_effort": "none", "remote_hint": _CODE_HINT,
        "local_max_tokens": 512,
        # Edge-Case-Signalwoerter = der Aufgabensteller testet genau das,
        # woran 2B-Modelle scheitern (zweifach belegt: Eval id 60 UND
        # offizielle practice-08, identischer Duplikat-Bug). Direkt remote —
        # auf der 2-vCPU-VM auch noch schneller (1-5s statt >20s lokal).
        "escalate_if": re.compile(
            r"handling|correctly handle|edge case|duplicat|distinct"
            r"|empty (list|string)|negative number|robust", re.I),
    },
}

# Summarisation ist mit Format-Gate + Eskalation besser bedient als mit
# blindem Vertrauen (Eval v2: 4/8 Judge-Fails, Formatverstoesse + fehlende
# Kernfakten). Env-Schalter fuer die harte Variante (immer eskalieren) —
# umlegen, falls das Leaderboard zeigt, dass die Accuracy nicht reicht.
import os as _os
SUMMARISATION_ALWAYS_ESCALATE = _os.environ.get("SUMMARISATION_ALWAYS_ESCALATE", "0") == "1"

_SENT_LIMIT_RE = re.compile(r"\b(?:in\s+)?(?:exactly\s+)?(one|two|three|1|2|3)\s+(?:short\s+)?sentences?\b", re.I)
_WORD_LIMIT_RE = re.compile(r"(?:no more than|at most|maximum(?: of)?|max\.?)\s+(\d+)\s+words", re.I)
_BULLET_RE = re.compile(r"(one|two|three|four|five|\d+)\s+(?:short\s+)?bullet points?", re.I)
_NUM_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}


def summarisation_format_violated(question, answer):
    """Prueft die im Aufgabentext geforderte Form (Satzzahl, Wortlimit,
    Bullet-Anzahl) gegen die Antwort — rein lokal, 0 Tokens. True =
    Verstoss -> eskalieren, denn Formatbruch ist ein sicherer Judge-Fail."""
    if not answer:
        return True
    sentences = len([s for s in re.split(r"[.!?]+", answer) if s.strip()])
    match = _SENT_LIMIT_RE.search(question)
    if match:
        limit = _NUM_WORDS.get(match.group(1).lower()) or int(match.group(1))
        if sentences > limit:
            return True
    match = _WORD_LIMIT_RE.search(question)
    if match and len(answer.split()) > int(match.group(1)) * 1.2:
        return True
    match = _BULLET_RE.search(question)
    if match:
        wanted = _NUM_WORDS.get(match.group(1).lower()) or int(match.group(1))
        bullets = sum(1 for line in answer.splitlines()
                      if re.match(r"\s*([-*•]|\d+[.)])\s+", line))
        if bullets < wanted:
            return True
    return False


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


def format_number(x):
    """Rechenergebnis als knappe Antwort-Zahl formatieren (10580.0 -> 10580)."""
    if x is None:
        return ""
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{x:.4f}".rstrip("0").rstrip(".")


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

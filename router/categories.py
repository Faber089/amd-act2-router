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
# WICHTIG (Discord-Klarstellung 9.7.): die finale Bewertung nutzt NEU
# randomisierte Prompt-Varianten. Der Robustheitstest auf 120 Paraphrasen
# (eval/tasks_extended.jsonl) zeigte 42/120 Fehlklassifikationen mit den
# alten engen Keyword-Regexen -> breite Paraphrase-Muster + STRUKTURELLE
# Code-Erkennung (steht ein Code-Block in der Frage?) statt nur Keywords.

_SUMMARISATION_RE = re.compile(
    r"summar|condense|tl\W?dr|shorten|boil .{0,20}down|sum up|write a headline"
    r"|bullet points?|key points|main finding|abstract for|sentence abstract"
    r"|reduce .{0,40}(email|text|paragraph|article)", re.I)
_SENTIMENT_RE = re.compile(
    r"sentiment|emotional tone|attitude|tone of this", re.I)
_NER_RE = re.compile(
    r"named entit|entit(y|ies)"
    r"|(persons?|people|compan(y|ies)|organi[sz]ations?)\b.{0,60}\b(locations?|places?|dates?)", re.I)
_CODE_PRESENT_RE = re.compile(
    r"```|\bdef \w+\s*\(|\bclass \w+[:(]|\bprint\s*\(|\breturn\b")
_DEBUG_SIGNAL_RE = re.compile(
    r"\bfix\b|\bbug(gy|s)?\b|debug|crash|\berrors?\b|\bwrong\b|broken|hangs?\b|fails?\b"
    r"|doesn'?t work|not work(ing)?|correct(ed)?\s+(it|this|the|version|code|function)"
    r"|why does|what('s| is) wrong", re.I)
_CODEGEN_RE = re.compile(
    r"(write|implement|creat\w*|build|make|need\w*|give me|provide)\s+(me\s+)?an?\s+(\w+[- ]){0,3}?(function|method|script|program)"
    r"|function (called|named)", re.I)
_LOGIC_RE = re.compile(
    r"knight|knave|liar|tells? the truth|always (lies?|tells?)|labels? (is|are) wrong"
    r"|finished (before|after)|older than|younger than|taller than|which day works"
    r"|each (\w+ )?(have|has|owns?|plays?)|exactly one|\bbeats?\b|guilty|innocent"
    r"|day (before|after) (yesterday|tomorrow)|facing (north|south|east|west)"
    r"|turns? \d+ degrees|all \w+ are\b|no \w+ is\b|all but \d+"
    r"|cross .{0,20}bridge|torch"
    r"|who (finished|came) (first|second|third|last)|seated|sits? (next to|between)", re.I)
_MATH_RE = re.compile(
    r"percent|%|\btimes\b|plus|minus|divided|multipl|discount|grows?|interest"
    r"|how (many|much|far|long|old)|total|average|price|cost|speed|area"
    r"|per (year|month|week|day|hour|100)|km/h|answer with only the number", re.I)


def classify(question):
    q = question
    if _SUMMARISATION_RE.search(q):
        return "summarisation"
    # Sentiment-Aufgaben nennen praktisch immer die Label-Optionen — das
    # Wortpaar positive+negative ist robuster als das Wort "sentiment".
    lowered = q.lower()
    if _SENTIMENT_RE.search(q) or ("positive" in lowered and "negative" in lowered):
        return "sentiment"
    if _NER_RE.search(q):
        return "ner"
    # Strukturell: enthaelt die Frage echten Code, ist es eine Code-Aufgabe —
    # egal wie die Aufforderung formuliert ist ("why does this crash?" etc.).
    has_code = bool(_CODE_PRESENT_RE.search(q))
    if has_code and _DEBUG_SIGNAL_RE.search(q):
        return "code_debugging"
    if not has_code and _CODEGEN_RE.search(q):
        return "code_generation"
    if has_code:
        # Code ohne klares Debug-Signal: Debugging-Politik ist die sichere
        # Wahl (hoher max_tokens-Deckel, Code-Checks aktiv).
        return "code_debugging"
    if _LOGIC_RE.search(q):
        return "logic_puzzle"
    if _MATH_RE.search(q) and re.search(r"\d", q):
        return "math_reasoning"
    return "factual_knowledge"


# --- Politik pro Kategorie ---
# local_hint: Zusatz fuer den lokalen Prompt (0 Tokens, erzwingt das Format,
#   das der Wettbewerbs-Judge laut Aufgabenstellung erwartet).
# remote_max_tokens / remote_effort: Eskalations-Steuerung. "none" schaltet
#   Kimis versteckte Denk-Tokens ab; Mathe/Logik bekommen stattdessen
#   sichtbares Kurz-CoT (remote_hint), dessen Laenge max_tokens deckelt —
#   sichtbares Denken ist steuerbar, verstecktes nicht.
# always_escalate: Kategorie ist lokal aussichtslos (Datenlage!).

# Experiment 10.7. (22 det-checkbare Logik-Aufgaben, kimi effort=none):
# 3-Schritt-Hint 22/22 bei 123 Tok/Task, nackte Frage mit effort=low 22/22
# bei 141 (verstecktes Denken ist TEURER als sichtbares), Minimal-Hint
# 22/22 bei 105 -> Minimal-Hint gewinnt. Ganz ohne CoT bleibt Logik 0/2.
_COT_HINT = "Reason very briefly, then end with: Answer: <result>"
_CODE_HINT = "State the bug in one short sentence, then give the complete corrected code."

# Token-Diaet-Experiment 7.7. spaetabends (nackte Frage, effort=none):
# Mathe 3/3 korrekt bei 2-3 completion-Tokens (inkl. Zinseszins, 347*289)
# -> Mathe braucht KEIN CoT. Logik 0/2 korrekt ohne CoT ("Ann", "apples")
# -> Logik BEHAELT das Kurz-CoT zwingend. Factual korrekt ohne alles.
POLICY = {
    # local_hint gegen den Kurzantwort-Reflex kleiner Modelle: zweiteilige
    # Fragen (Practice-Task-Stil!) bekommen sonst nur eine halbe Antwort
    # ("George Orwell" ohne das Jahr) — gemessen qwen3-Shootout 10.7.
    "factual_knowledge": {
        "remote_max_tokens": 128, "remote_effort": "none",
        "local_hint": "Answer EVERY part of the question, briefly and completely.",
    },
    "math_reasoning": {
        "remote_max_tokens": 128, "remote_effort": "none",
        "math_crosscheck": True,
        # 96->160 (11.7.): bei 96 wurde eine ausfuehrliche Antwort mitten in
        # der Rechnung abgeschnitten (Truncation), was zu einer verzerrten
        # finalen Zahl fuehren kann. 160 laesst genug Platz fuer eine volle
        # Chain-of-Thought-Antwort, bleibt aber weit unter dem Latenz-Budget.
        "local_max_tokens": 160,
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
        # Live-Bug 11.7. (VM-Test des gepushten Images, practice-03): der
        # lokale Hint gilt nur fuers lokale Modell -- eine Eskalation nach
        # Fireworks bekam KEINE Formatvorgabe und lieferte nur "Mixed."
        # zurueck, ohne Begruendung. Denselben Hint auch beim Remote-Call
        # mitschicken behebt das (kostet ein paar Prompt-Tokens, verhindert
        # aber einen sicheren Judge-Fail).
        "remote_hint": ('Your answer must follow exactly this pattern: '
                        '<label> - <one short reason>. Example: "negative - the '
                        'reviewer complains about slow delivery." Never answer '
                        'with the label alone.'),
        "needs_justification": True,
        # VM-Simulation 8.7.: Antwort+Selfcheck+Nachforderung stapelten sich
        # auf 24,8s (30s-Limit!). Der Selfcheck bringt bei Sentiment am
        # wenigsten (Label-Stabilitaet war nie das Problem) -> raus.
        # Stattdessen (11.7.): billiger LABEL-Selfcheck — nur das Label des
        # Zweitlaufs vergleichen, nicht den ganzen Text (Fails 133/136:
        # instabile Labels bei neutralen Texten).
        "skip_selfcheck": True,
        "label_selfcheck": True,
    },
    "summarisation": {
        "remote_max_tokens": 192, "remote_effort": "none",
        # Judge wertet fehlende Kernfakten als falsch (v4, id 38: Ursachen
        # weggelassen) — der 7-Token-Hint ist billiger als ein Gate-Fail.
        "remote_hint": "Keep the key facts and figures.",
        "local_hint": ("Summarise IN YOUR OWN WORDS - never copy sentences from "
                       "the source. Obey the requested format EXACTLY (number of "
                       "sentences, word limit, bullet count) and keep the key "
                       "facts and figures."),
    },
    "ner": {
        "remote_max_tokens": 128, "remote_effort": "none",
        # Straffer Hint (qwen3-Lauf 11.7.: Fantasie-Labels wie (MONTH)/(DAY),
        # zerhackte Datumsangaben, "revolutionaries" als PERSON):
        "local_hint": ("List EVERY named entity, each with exactly one of these "
                       "type labels: PERSON, ORGANIZATION, LOCATION, DATE. Keep "
                       "multi-word names and dates together as ONE entity. Only "
                       "proper names and dates - no generic words. Example: "
                       "Tim Cook (PERSON); Apple (ORGANIZATION); Paris (LOCATION); "
                       "10 September 2025 (DATE)."),
        # Eval v2: die NER-Fails waren FEHLENDE Entitaeten, nie falsche.
        # Zweitlauf + Vereinigungsmenge (0 Tokens) hebt den Recall.
        "entity_union": True,
        # Entity-Union sichert objektiv ab; fehlende CONFIDENCE-Zahl (qwen3
        # bei langen Entity-Listen) soll nicht eskalieren (Lauf 010031: 2x).
        "default_confidence": 75,
    },
    "code_debugging": {
        "remote_max_tokens": 512, "remote_effort": "none", "remote_hint": _CODE_HINT,
        # 512->400 (Robustheits-Audit 11.7.): 512 Tokens Generierung brauchen
        # auf der 2-vCPU-VM bis zu ~25s — der Live-Test des gepushten Images
        # zeigte 26,5s bei einem 30s-Hardlimit. 400 reicht fuer jede normale
        # Funktion und kauft ~5s Sicherheitspuffer auf langsamer Hardware.
        "local_max_tokens": 400, "reject_identical": True,
        # qwen3-Router-Lauf 11.7.: 3 Judge-Fails, weil die lokale Antwort den
        # Bug nur in PROSA erklaerte statt korrigierten Code zu liefern.
        # Ohne Code kann die Antwort nie korrekt sein -> eskalieren.
        "require_code": True,
        # ... und damit es gar nicht erst so weit kommt (Lauf 010031: 4 von 8
        # Debug-Eskalationen NUR wegen Prosa-Antworten): expliziter Hint.
        "local_hint": ("Your ANSWER must contain the complete corrected "
                       "function as code, plus ONE short sentence naming the bug."),
        # Objektive Checks (Syntax, reject_identical, require_code) sichern
        # diese Kategorie ab — eine fehlende CONFIDENCE-Zahl (qwen3 laesst
        # sie bei Code-Antworten oft weg) ist dann kein Eskalationsgrund.
        "default_confidence": 75,
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
        "local_max_tokens": 400,
        "require_code": True,
        "default_confidence": 75,
        # KEIN escalate_if mehr (Stand 11.7.): das Edge-Case-Muster stammte
        # aus der gemma2-Aera (id-60/practice-08-Duplikat-Bug). qwen3:1.7b
        # loest Codegen inkl. Edge-Cases lokal (Shootout: 21/23 det, darunter
        # second_smallest UND factorial-negative) — die Zwangseskalation
        # kostete im Router-Lauf ~7 Eskalationen ohne Accuracy-Gewinn.
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
    # Kopie-Erkennung (v4-Lauf 11.7., ids 8/39/42): qwen3 gibt manchmal den
    # Quelltext woertlich zurueck statt zusammenzufassen. det-Checks sehen
    # das nicht (alle Keywords da!), der Judge schon. Steht die komplette
    # Antwort woertlich in der Aufgabe, ist es keine Zusammenfassung.
    if re.sub(r"[^a-z0-9]", "", answer.lower()) in re.sub(r"[^a-z0-9]", "", question.lower()):
        return True
    sentences = len([s for s in re.split(r"[.!?]+", answer) if s.strip()])
    match = _SENT_LIMIT_RE.search(question)
    if match:
        limit = _NUM_WORDS.get(match.group(1).lower()) or int(match.group(1))
        # "exactly two sentences" heisst EXAKT: auch zu WENIGE Saetze sind
        # ein Formatbruch (qwen3-Lauf 11.7., id 148: 1 Satz statt 2 = Fail).
        exact = "exactly" in match.group(0).lower()
        if sentences > limit or (exact and sentences != limit):
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
    (dann ist mindestens eines falsch -> eskalieren).

    Live-Bug gefunden 11.7. (VM-Test des gepushten Images, practice-02):
    bei ausfuehrlichen Antworten mit mehreren Zwischenrechnungen ("240 * 0.15
    = 36 ... total 336 ... verbleiben -96") tauchen viele Zahlen im Text auf.
    Die alte "irgendeine Zahl stimmt"-Pruefung fand zufaellig eine passende
    Zwischenzahl und liess die falsche FINALE Antwort (-96 statt 144) durch.
    Fix: nur die LETZTE Zahl zaehlt -- das ist bei Chain-of-Thought-Antworten
    so gut wie immer die abschliessend genannte Antwort."""
    if expr_result is None:
        return False  # keine Gegenrechnung moeglich -> kein Urteil
    answer_numbers = numbers_in(local_answer)
    if not answer_numbers:
        return True  # Zahl gefordert, keine Zahl geliefert
    final = answer_numbers[-1]
    return not (abs(final - expr_result) < max(1e-6, abs(expr_result) * 1e-9))


# --- NER-Vereinigungsmenge (0 Tokens, Recall-Boost) ---

_ENTITY_LINE_RE = re.compile(
    r"([\w][\w .,'&-]{0,50}?)\s*\((PERSON|PEOPLE|ORG\w*|COMPANY|LOCATION|LOC|PLACE|GPE|DATE|TIME|EVENT)\)",
    re.I)


def merge_entities(first, second):
    """Ergaenzt die Erstantwort um Entitaeten, die NUR der Zweitlauf gefunden
    hat (Datenlage Eval v2: NER-Fails waren immer fehlende Entitaeten, nie
    erfundene). Rueckgabe None, wenn nichts zu ergaenzen ist."""
    if not first or not second:
        return None
    first_norm = re.sub(r"[^a-z0-9]", "", first.lower())
    additions = []
    for match in _ENTITY_LINE_RE.finditer(second):
        name = match.group(1).strip(" *-•")
        name_norm = re.sub(r"[^a-z0-9]", "", name.lower())
        if name_norm and name_norm not in first_norm:
            additions.append(f"{name} ({match.group(2).upper()})")
    if not additions:
        return None
    return first.rstrip() + "\n" + "\n".join(dict.fromkeys(additions))


_MONTHS = (r"(?:January|February|March|April|May|June|July|August|September"
           r"|October|November|December)")
_FULL_DATE_RE = re.compile(
    rf"\b(?:\d{{1,2}}\s+{_MONTHS}\s+\d{{4}}|{_MONTHS}\s+\d{{1,2}},?\s+\d{{4}}"
    rf"|{_MONTHS}\s+\d{{4}})\b", re.I)


def normalize_entities(question, answer):
    """Repariert zwei gemessene NER-Schwaechen des Lokalmodells — beides
    deterministisch, 0 Tokens, nur wenn der Beleg WOERTLICH in der Aufgabe
    steht (sonst None = nichts aendern):
      1. Zerhackte Mehrwort-Namen (VM-Sim 11.7., practice-05:
         'Maria (PERSON); Sanchez (PERSON)' -> 'Maria Sanchez (PERSON)').
      2. Aufs Jahr gestutzte Datumsangaben (v5-Lauf, ids 43/46:
         '2024' -> '14 March 2024', wie im Aufgabentext)."""
    matches = list(_ENTITY_LINE_RE.finditer(answer or ""))
    if len(matches) < 2:
        return None
    items = [[m.group(1).strip(" *-•\t"), m.group(2).upper()] for m in matches]
    merged, i, changed = [], 0, False
    while i < len(items):
        joined = None
        if i + 1 < len(items) and items[i][1] == items[i + 1][1]:
            # Leerzeichen-Paar ("Maria Sanchez") ODER Komma-Paar
            # ("Austin, Texas") — nur wenn es WOERTLICH in der Aufgabe steht.
            for sep in (" ", ", "):
                candidate = f"{items[i][0]}{sep}{items[i + 1][0]}"
                if candidate in question:
                    joined = candidate
                    break
        if joined:
            merged.append([joined, items[i][1]])
            i += 2
            changed = True
        else:
            merged.append(items[i])
            i += 1
    # Datums-Expansion: steht in der Aufgabe ein volleres Datum, das die
    # gestutzte DATE-Entitaet enthaelt, gilt das volle Datum.
    full_dates = _FULL_DATE_RE.findall(question)
    for item in merged:
        if item[1] in ("DATE", "TIME"):
            for full_date in full_dates:
                if item[0] != full_date and item[0] in full_date:
                    item[0] = full_date
                    changed = True
                    break
    if not changed:
        return None
    return "; ".join(dict.fromkeys(f"{name} ({typ})" for name, typ in merged))


# --- Antwort-Nachbearbeitung ---

_ONLY_RE = re.compile(r"answer with (?:only )?(?:the |a )?(number|name|day|word|yes or no)", re.I)
_FINAL_ANSWER_RE = re.compile(r"(?:^|\n)\s*Answer:\s*(.+?)\s*$", re.I | re.DOTALL)


def postprocess_answer(question, text):
    """Wenn die Aufgabe 'Answer with only the number/name/...' verlangt und
    die Antwort Kurz-CoT enthaelt, nur den finalen Wert ausliefern — der
    Judge soll keinen Formatverstoss sehen. Konservativ: nur eingreifen,
    wenn ein klarer 'Answer:'-Marker existiert. Zusaetzlich (11.7.):
    '$83,600' bei 'only the number' ist ein Formatverstoss -> Waehrungs-
    zeichen/Tausender-Kommas aus kurzen Zahl-Antworten entfernen."""
    if not text:
        return text
    only = _ONLY_RE.search(question)
    match = _FINAL_ANSWER_RE.search(text)
    if match:
        final = match.group(1).strip()
        # Auch ohne "only"-Vorgabe: steht ein expliziter Answer-Marker am
        # Ende, ist alles davor Rechenweg — final reicht und haelt die
        # Antwort judge-sauber... ausser der Weg IST die geforderte Antwort
        # (Erklaer-Aufgaben) -> dann lieber alles behalten.
        if only or len(final) <= 80:
            text = final
    if only and only.group(1).lower() == "number" and len(text) <= 40:
        text = re.sub(r"[$€£]|,(?=\d)", "", text).strip()
    return text

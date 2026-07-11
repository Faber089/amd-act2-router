import ast
import re

from router import config
from router.local_client import ask_local_raw

_CODE_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)


def looks_like_code(answer):
    """Heuristik: enthaelt die Antwort einen Code-Block oder eine Funktions-/
    Klassendefinition? Nur dann macht ein Syntax-Check ueberhaupt Sinn."""
    return bool(_CODE_FENCE_RE.search(answer)) or bool(
        re.search(r"^\s*(def |class )", answer, re.MULTILINE)
    )


def extract_code(answer):
    """Holt den reinen Code aus einem Markdown-Codeblock, falls vorhanden,
    sonst wird die ganze Antwort als Code behandelt."""
    match = _CODE_FENCE_RE.search(answer)
    return match.group(1) if match else answer


def is_valid_python(code):
    """Rein syntaktischer Check (ast.parse, kein exec!) -- sicher, weil
    nichts ausgefuehrt wird, aber deckt eine ganze Fehlerklasse ab: Code,
    der plausibel aussieht, aber gar nicht laeuft. Objektiv statt
    Selbsteinschaetzung, genau fuer die Kategorien wo eine Pruefung moeglich
    ist (Code Debugging, Code Generation)."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def parse_local_answer(text, threshold=70, default_confidence=0):
    """
    Liest aus der lokalen Modellantwort die ANSWER und das CONFIDENCE heraus.
    Gibt zurück: (antwort_text, ist_vertrauenswuerdig, confidence)
    default_confidence: gilt, wenn der CONFIDENCE-Marker fehlt. 0 (streng)
    fuer Kategorien ohne objektive Checks; Kategorien MIT objektiven Checks
    (Code-Syntax, Entity-Union) setzen per Politik einen milderen Wert,
    weil qwen3 den Marker bei langen Code-/Listen-Antworten oft weglaesst.
    """
    # Nicht am ersten Zeilenumbruch stoppen (frueherer Bug) -- sonst wird
    # mehrzeiliger Code/Text in der Antwort fast komplett abgeschnitten.
    # Stattdessen alles bis zum CONFIDENCE-Marker (oder Textende) einfangen.
    answer_match = re.search(r"ANSWER:\s*(.+?)(?=\s*CONFIDENCE:|\Z)", text, re.DOTALL)
    confidence_match = re.search(r"CONFIDENCE:\s*(\d+)", text)

    answer = answer_match.group(1).strip() if answer_match else text.strip()
    confidence = (int(confidence_match.group(1)) if confidence_match
                  else default_confidence)

    is_trustworthy = confidence >= threshold
    return answer, is_trustworthy, confidence


def critique(question, answer, model=None):
    """
    Zweite, skeptische Prüfung: Bittet das lokale Modell, die gegebene Antwort
    kritisch auf Fehler zu pruefen (unabhaengig von der Selbsteinschaetzung oben).
    Gibt zurück: True = Antwort haelt der Kritik stand, False = Kritiker sieht Fehler.
    """
    # Kein hartcodiertes Modell als Default (fruehere Version nutzte
    # "gemma2:2b" fest, unabhaengig von LOCAL_MODEL) -- falls der Aufrufer
    # nichts angibt, gilt dieselbe Konfiguration wie ueberall sonst im Router.
    model = model or config.LOCAL_MODEL
    # Prompt-Text Englisch (siehe local_client.ask_local) -- betrifft auch
    # dieses interne Judge-Gespraech, auch wenn nur das Endergebnis (ANSWER)
    # tatsaechlich bewertet wird.
    prompt = (
        f"Question: {question}\n"
        f"Given answer: {answer}\n\n"
        "Critically and precisely check whether the given answer is correct. "
        "Recalculate any numbers, verify facts. Be strict.\n"
        "Respond in exactly this format:\n"
        "VERDICT: CORRECT or INCORRECT"
    )
    text, _ = ask_local_raw(prompt, model=model)
    verdict_match = re.search(r"VERDICT:\s*(CORRECT|INCORRECT)", text, re.IGNORECASE)
    verdict = verdict_match.group(1).upper() if verdict_match else "INCORRECT"
    return verdict == "CORRECT"


def semantic_judge(question, answer, expected, model=None):
    """
    NUR fuer die eigene Eval (eval/run_eval.py), NICHT Teil der Routing-Logik.
    Grober Substring-Match kann bei freien Antworten (Summarization, NER,
    Sentiment-Begruendung) falsch-negativ sein, wenn die Antwort inhaltlich
    richtig ist, aber anders formuliert (real erlebt: eine korrekte
    Zusammenfassung, die nicht das exakt erwartete Wort enthielt). Diese
    Funktion laesst das lokale Modell selbst beurteilen, ob die Antwort die
    erwarteten Kernfakten sinngemaess trifft -- als informeller Vergleichswert
    neben dem Substring-Check, NICHT als Ersatz (der echte Wettbewerbs-Judge
    ist unbekannt, das hier ist nur unsere beste Annaeherung).
    """
    model = model or config.LOCAL_MODEL
    prompt = (
        f"Question: {question}\n"
        f"Expected key facts: {expected}\n"
        f"Given answer: {answer}\n\n"
        "Does the given answer correctly convey the expected key facts, "
        "even if worded differently? Ignore exact phrasing, judge only "
        "whether the meaning matches.\n"
        "Respond in exactly this format:\n"
        "VERDICT: CORRECT or INCORRECT"
    )
    text, _ = ask_local_raw(prompt, model=model)
    verdict_match = re.search(r"VERDICT:\s*(CORRECT|INCORRECT)", text, re.IGNORECASE)
    verdict = verdict_match.group(1).upper() if verdict_match else "INCORRECT"
    return verdict == "CORRECT"

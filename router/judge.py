import ast
import re

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


def parse_local_answer(text, threshold=70):
    """
    Liest aus der lokalen Modellantwort die ANSWER und das CONFIDENCE heraus.
    Gibt zurück: (antwort_text, ist_vertrauenswuerdig)
    """
    # Nicht am ersten Zeilenumbruch stoppen (frueherer Bug) -- sonst wird
    # mehrzeiliger Code/Text in der Antwort fast komplett abgeschnitten.
    # Stattdessen alles bis zum CONFIDENCE-Marker (oder Textende) einfangen.
    answer_match = re.search(r"ANSWER:\s*(.+?)(?=\s*CONFIDENCE:|\Z)", text, re.DOTALL)
    confidence_match = re.search(r"CONFIDENCE:\s*(\d+)", text)

    answer = answer_match.group(1).strip() if answer_match else text.strip()
    confidence = int(confidence_match.group(1)) if confidence_match else 0

    is_trustworthy = confidence >= threshold
    return answer, is_trustworthy, confidence


def critique(question, answer, model="gemma2:2b"):
    """
    Zweite, skeptische Prüfung: Bittet das lokale Modell, die gegebene Antwort
    kritisch auf Fehler zu pruefen (unabhaengig von der Selbsteinschaetzung oben).
    Gibt zurück: True = Antwort haelt der Kritik stand, False = Kritiker sieht Fehler.
    """
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

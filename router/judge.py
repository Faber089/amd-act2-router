import re

from router.local_client import ask_local_raw


def parse_local_answer(text, threshold=70):
    """
    Liest aus der lokalen Modellantwort die ANTWORT und das VERTRAUEN heraus.
    Gibt zurück: (antwort_text, ist_vertrauenswuerdig)
    """
    answer_match = re.search(r"ANTWORT:\s*(.+?)(?:\n|$)", text, re.DOTALL)
    confidence_match = re.search(r"VERTRAUEN:\s*(\d+)", text)

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
    prompt = (
        f"Frage: {question}\n"
        f"Gegebene Antwort: {answer}\n\n"
        "Prüfe kritisch und genau, ob die gegebene Antwort korrekt ist. "
        "Rechne bei Zahlen nach, prüfe Fakten. Sei streng.\n"
        "Antworte in genau diesem Format:\n"
        "URTEIL: KORREKT oder FEHLERHAFT"
    )
    text, _ = ask_local_raw(prompt, model=model)
    verdict_match = re.search(r"URTEIL:\s*(KORREKT|FEHLERHAFT)", text, re.IGNORECASE)
    verdict = verdict_match.group(1).upper() if verdict_match else "FEHLERHAFT"
    return verdict == "KORREKT"

import re

from router.local_client import ask_local_raw


def parse_local_answer(text, threshold=70):
    """
    Liest aus der lokalen Modellantwort die ANSWER und das CONFIDENCE heraus.
    Gibt zurück: (antwort_text, ist_vertrauenswuerdig)
    """
    answer_match = re.search(r"ANSWER:\s*(.+?)(?:\n|$)", text, re.DOTALL)
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

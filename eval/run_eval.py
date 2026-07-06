import json
from pathlib import Path
from router.main import route
from router.judge import semantic_judge

TASKS_FILE = Path(__file__).parent / "tasks.jsonl"


def load_tasks():
    tasks = []
    with open(TASKS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks


def normalize(s):
    return s.lower().replace(" ", "").replace("*", "")


def is_correct(answer, expected):
    """
    Grober Substring-Check. `expected` darf ein einzelner String (Antwort
    muss ihn enthalten) oder eine Liste akzeptierter Stichwoerter sein (schon
    EINES davon reicht) -- letzteres fuer freie Kategorien (Summarization,
    NER), wo eine einzelne feste Phrase zu streng waere.
    Achtung: das ist eine grobe Annaeherung, NICHT der echte Judge-Mechanismus
    des Wettbewerbs (LLM-Judge, siehe semantic_judge() fuer den Vergleichswert).
    """
    if isinstance(expected, list):
        return any(normalize(e) in normalize(answer) for e in expected)
    return normalize(expected) in normalize(answer)


def expected_as_text(expected):
    return ", ".join(expected) if isinstance(expected, list) else expected


def main():
    tasks = load_tasks()
    total_tokens = 0
    correct_count = 0
    judged_correct_count = 0
    disagreements = []
    records = []  # (confidence, correct, source) fuer die Kalibrierungs-Tabelle

    for task in tasks:
        stats = {}
        try:
            answer, tokens, source = route(task["question"], verbose=False, stats=stats)
        except Exception as exc:
            print(f"[{task['id']:>2}] FEHLER  | {exc}")
            answer, tokens, source = "", 0, "error"
        correct = is_correct(answer, task["expected"])
        # Zweite, informelle Einschaetzung durchs lokale Modell selbst (0
        # Tokens, kostet nur etwas Zeit) -- zeigt, wo der grobe Substring-
        # Check moeglicherweise vom Sinn der Antwort abweicht.
        judged_correct = semantic_judge(task["question"], answer, expected_as_text(task["expected"]))
        correct_count += int(correct)
        judged_correct_count += int(judged_correct)
        total_tokens += tokens
        records.append((stats.get("confidence"), correct, source))
        if correct != judged_correct:
            disagreements.append((task["id"], correct, judged_correct))

        status = "OK" if correct else "FALSCH"
        judge_flag = "" if correct == judged_correct else f" (LLM-Richter: {'OK' if judged_correct else 'FALSCH'})"
        print(f"[{task['id']:>2}] {status:6} | Quelle: {source:6} | Conf: {str(stats.get('confidence')):>4} | Tokens: {tokens:4}{judge_flag} | Frage: {task['question']}")
        if not correct:
            print(f"       -> Erwartet: '{expected_as_text(task['expected'])}' | Antwort war: {answer[:100]}")

    accuracy = correct_count / len(tasks) * 100
    judged_accuracy = judged_correct_count / len(tasks) * 100
    print("\n=== ERGEBNIS ===")
    print(f"Accuracy (grober Substring-Check): {accuracy:.1f}% ({correct_count}/{len(tasks)})")
    print(f"Accuracy (informeller LLM-Richter): {judged_accuracy:.1f}% ({judged_correct_count}/{len(tasks)})")
    print(f"Gesamt-Tokens (fürs Leaderboard): {total_tokens}")
    if disagreements:
        print(f"\n⚠️  {len(disagreements)} Aufgabe(n), wo beide Methoden nicht übereinstimmen:")
        for task_id, sub_ok, judge_ok in disagreements:
            print(f"   [{task_id}] Substring={'OK' if sub_ok else 'FALSCH'} vs. LLM-Richter={'OK' if judge_ok else 'FALSCH'}")
        print("   -> Weder Substring-Check noch dieser LLM-Richter sind der echte Wettbewerbs-Judge.")
        print("      Bei Uneinigkeit die Antwort selbst nochmal lesen, nicht blind einer Zahl vertrauen.")

    # Kalibrierungs-Tabelle: wie oft ist die LOKALE Antwort korrekt, je nach
    # Selbst-Confidence? Damit laesst sich CONFIDENCE_THRESHOLD aus Daten
    # waehlen statt aus Bauchgefuehl (Kalibrierung > Intuition).
    local_recs = [(c, ok) for c, ok, src in records if c is not None and src in ("local", "local-fallback")]
    if local_recs:
        print("\n=== KALIBRIERUNG (lokale Antworten) ===")
        print("Confidence | Anzahl | davon korrekt")
        for lo in (0, 50, 70, 80, 90, 100):
            hi = {0: 49, 50: 69, 70: 79, 80: 89, 90: 99, 100: 100}[lo]
            bucket = [ok for c, ok in local_recs if lo <= c <= hi]
            if bucket:
                pct = sum(bucket) / len(bucket) * 100
                print(f"  {lo:>3}-{hi:<3}  | {len(bucket):>6} | {sum(bucket)}/{len(bucket)} ({pct:.0f}%)")


if __name__ == "__main__":
    main()

import json
from pathlib import Path
from router.main import route

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
    return normalize(expected) in normalize(answer)


def main():
    tasks = load_tasks()
    total_tokens = 0
    correct_count = 0
    records = []  # (confidence, correct, source) fuer die Kalibrierungs-Tabelle

    for task in tasks:
        stats = {}
        try:
            answer, tokens, source = route(task["question"], verbose=False, stats=stats)
        except Exception as exc:
            print(f"[{task['id']:>2}] FEHLER  | {exc}")
            answer, tokens, source = "", 0, "error"
        correct = is_correct(answer, task["expected"])
        correct_count += int(correct)
        total_tokens += tokens
        records.append((stats.get("confidence"), correct, source))

        status = "OK" if correct else "FALSCH"
        print(f"[{task['id']:>2}] {status:6} | Quelle: {source:6} | Conf: {str(stats.get('confidence')):>4} | Tokens: {tokens:4} | Frage: {task['question']}")
        if not correct:
            print(f"       -> Erwartet: '{task['expected']}' | Antwort war: {answer[:100]}")

    accuracy = correct_count / len(tasks) * 100
    print("\n=== ERGEBNIS ===")
    print(f"Accuracy: {accuracy:.1f}% ({correct_count}/{len(tasks)})")
    print(f"Gesamt-Tokens (fürs Leaderboard): {total_tokens}")

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

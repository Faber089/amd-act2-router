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

    for task in tasks:
        answer, tokens, source = route(task["question"], verbose=False)
        correct = is_correct(answer, task["expected"])
        correct_count += int(correct)
        total_tokens += tokens

        status = "OK" if correct else "FALSCH"
        print(f"[{task['id']:>2}] {status:6} | Quelle: {source:6} | Tokens: {tokens:4} | Frage: {task['question']}")
        if not correct:
            print(f"       -> Erwartet: '{task['expected']}' | Antwort war: {answer[:100]}")

    accuracy = correct_count / len(tasks) * 100
    print("\n=== ERGEBNIS ===")
    print(f"Accuracy: {accuracy:.1f}% ({correct_count}/{len(tasks)})")
    print(f"Gesamt-Tokens (fürs Leaderboard): {total_tokens}")


if __name__ == "__main__":
    main()

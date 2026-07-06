"""
Wettbewerbs-Entrypoint fuer die Submission (Participant Guide, Track 1).
Liest /input/tasks.json, ruft router.main.route() pro Aufgabe auf,
schreibt /output/results.json. Reine Zusatzdatei -- keine eigene Routing-Logik,
route() aus router/main.py wird unveraendert wiederverwendet.
"""
import json
import os
import sys
import time

from router.local_client import ask_local_raw
from router.main import route

INPUT_PATH = os.environ.get("TASKS_INPUT_PATH", "/input/tasks.json")
OUTPUT_PATH = os.environ.get("RESULTS_OUTPUT_PATH", "/output/results.json")

# Participant Guide: maximale Gesamtlaufzeit 10 Minuten. Puffer einplanen,
# damit wir VOR einem harten Kill noch /output/results.json schreiben koennen,
# statt komplett leer auszugehen.
TIME_BUDGET_SECONDS = 9 * 60


def main():
    try:
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    except Exception as exc:
        print(f"FATAL: could not read {INPUT_PATH}: {exc}", file=sys.stderr)
        sys.exit(1)

    # Warmlaufen lassen: der allererste Call ans lokale Modell laedt es oft
    # noch in den Speicher (Cold Start) und kann laenger dauern/fehlschlagen.
    # Das soll waehrend der 60s-Startzeit passieren, nicht das 30s-Budget der
    # ersten echten Aufgabe verbrauchen. Ergebnis wird verworfen.
    try:
        ask_local_raw("Say hi.")
    except Exception as exc:
        print(f"WARN: local model warm-up failed: {exc}", file=sys.stderr)

    start = time.monotonic()
    results = []

    for task in tasks:
        task_id = task.get("task_id")
        prompt = task.get("prompt", "")
        elapsed = time.monotonic() - start

        if elapsed > TIME_BUDGET_SECONDS:
            print(f"[{task_id}] time budget exceeded, skipping", file=sys.stderr)
            results.append({"task_id": task_id, "answer": ""})
            continue

        try:
            answer, tokens, source = route(prompt, verbose=False)
        except Exception as exc:
            print(f"WARN: task {task_id} failed: {exc}", file=sys.stderr)
            answer, tokens, source = "", 0, "error"

        print(f"[{task_id}] source={source} tokens={tokens}")
        results.append({"task_id": task_id, "answer": answer})

    try:
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"FATAL: could not write {OUTPUT_PATH}: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Done: {len(results)} tasks, {time.monotonic() - start:.1f}s total")
    sys.exit(0)


if __name__ == "__main__":
    main()

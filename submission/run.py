"""
Wettbewerbs-Entrypoint fuer die Submission (Participant Guide, Track 1).
Liest /input/tasks.json, ruft router.main.route() pro Aufgabe auf,
schreibt /output/results.json. Reine Zusatzdatei -- keine eigene Routing-Logik,
route() aus router/main.py wird unveraendert wiederverwendet.

Zeitbudget-Strategie (10-Minuten-Hardlimit des Harness):
  1. Normalfall: lokal-zuerst-Kaskade (route()) pro Aufgabe.
  2. Budget-Flip: reicht die Restzeit nicht mehr fuer lokal-zuerst bei allen
     verbleibenden Aufgaben, schaltet der Lauf auf Remote-direkt um --
     Fireworks antwortet in wenigen Sekunden. Das kostet Tokens, aber eine
     gefuellte Antwort kann das Accuracy-Gate bestehen, eine leere nie.
  3. Notbremse: kurz vor dem Hardlimit werden restliche Aufgaben leer
     aufgefuellt, damit /output/results.json IMMER gueltiges, vollstaendiges
     JSON ist (fehlende Datei/kaputtes JSON = 0 Punkte fuer ALLES).
"""
import json
import os
import sys
import time

from router.categories import classify, get_policy, postprocess_answer
from router.local_client import ask_local_raw
from router.main import route
from router.remote_client import ask_remote, resolve_model


def ask_remote_with_policy(prompt):
    """Remote-direkt MIT Kategorie-Politik: der nackte ask_remote-Call war
    ein Accuracy-Loch im Budget-Flip (Logik ohne CoT-Hint: gemessen 0/2).
    Kategorie-Erkennung ist lokal/kostenlos, die Politik liefert max_tokens,
    reasoning_effort und Hint wie in der normalen Kaskade."""
    policy = get_policy(classify(prompt))
    answer, tokens = ask_remote(
        prompt,
        model=resolve_model(policy.get("remote_model")),
        max_tokens=policy.get("remote_max_tokens"),
        reasoning_effort=policy.get("remote_effort"),
        hint=policy.get("remote_hint"),
    )
    return postprocess_answer(prompt, answer), tokens

INPUT_PATH = os.environ.get("TASKS_INPUT_PATH", "/input/tasks.json")
OUTPUT_PATH = os.environ.get("RESULTS_OUTPUT_PATH", "/output/results.json")

# Participant Guide: maximale Gesamtlaufzeit 10 Minuten. Puffer einplanen,
# damit wir VOR einem harten Kill noch /output/results.json schreiben koennen,
# statt komplett leer auszugehen.
TIME_BUDGET_SECONDS = int(os.environ.get("TIME_BUDGET_SECONDS", str(9 * 60)))


def write_results(results, tasks):
    """Schreibt results.json und fuellt fehlende task_ids leer auf, damit die
    Datei immer vollstaendig und gueltig ist -- auch nach Crash/Zeitablauf.
    Schema-Haertung (Audit 11.7.): jede Zeile hat garantiert task_id UND
    answer als STRINGS -- null/Nicht-String waere INVALID_RESULTS_SCHEMA."""
    answered = {r["task_id"] for r in results}
    for i, task in enumerate(tasks):
        task_id = task.get("task_id")
        if task_id not in answered:
            results.append({"task_id": task_id, "answer": ""})
    clean = [
        {"task_id": str(r.get("task_id") or f"task-{i + 1}"),
         "answer": r.get("answer") if isinstance(r.get("answer"), str) else str(r.get("answer") or "")}
        for i, r in enumerate(results)
    ]
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)


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
    local_available = True
    try:
        ask_local_raw("Say hi.", max_tokens=8)
    except Exception as exc:
        # Kein lokales Modell erreichbar -> Kaskade wuerde bei jeder Aufgabe
        # erst in einen Fehler laufen. Dann lieber sofort Remote-direkt.
        local_available = False
        print(f"WARN: local model warm-up failed: {exc}", file=sys.stderr)

    start = time.monotonic()
    results = []
    remote_only = not local_available
    # Laufende Durchschnitte fuer die Budget-Prognose; Startwerte bewusst
    # pessimistisch (unbekannte Judging-Hardware).
    avg_local_s = 12.0
    avg_remote_s = 5.0

    try:
        for i, task in enumerate(tasks):
            task_id = task.get("task_id")
            prompt = task.get("prompt", "")
            elapsed = time.monotonic() - start
            remaining_time = TIME_BUDGET_SECONDS - elapsed
            remaining_tasks = len(tasks) - i

            # Notbremse: praktisch keine Zeit mehr -> nur noch auffuellen.
            if remaining_time <= 5:
                print(f"[{task_id}] time budget exhausted, empty answer", file=sys.stderr)
                results.append({"task_id": task_id, "answer": ""})
                continue

            # Budget-Flip: lokal-zuerst nur, solange es sich alle restlichen
            # Aufgaben leisten koennen (Sicherheitspuffer 15s).
            if not remote_only and remaining_time < remaining_tasks * (avg_remote_s + 2) + avg_local_s + 15:
                remote_only = True
                print(f"[{task_id}] time budget tight -> switching to remote-direct", file=sys.stderr)

            t0 = time.monotonic()
            answer, tokens, source = "", 0, "error"
            if remote_only:
                try:
                    answer, tokens = ask_remote_with_policy(prompt)
                    source = "remote-direct"
                except Exception as exc:
                    print(f"WARN: remote-direct failed for {task_id}: {exc}", file=sys.stderr)
                    if local_available:
                        try:
                            answer, tokens, source = route(prompt, verbose=False)
                        except Exception as exc2:
                            print(f"WARN: task {task_id} failed: {exc2}", file=sys.stderr)
            else:
                try:
                    answer, tokens, source = route(prompt, verbose=False)
                except Exception as exc:
                    print(f"WARN: task {task_id} failed: {exc}", file=sys.stderr)
                    try:
                        answer, tokens = ask_remote_with_policy(prompt)
                        source = "remote-direct"
                    except Exception as exc2:
                        print(f"WARN: remote fallback failed for {task_id}: {exc2}", file=sys.stderr)

            duration = time.monotonic() - t0
            # Laufender Durchschnitt (leichte Glaettung) fuer die Prognose.
            if source in ("local", "local-fallback"):
                avg_local_s = 0.7 * avg_local_s + 0.3 * duration
            elif source.startswith("remote"):
                avg_remote_s = 0.7 * avg_remote_s + 0.3 * duration

            print(f"[{task_id}] source={source} tokens={tokens} time={duration:.1f}s")
            results.append({"task_id": task_id, "answer": answer})
    finally:
        # results.json wird IMMER geschrieben -- auch wenn oben etwas
        # Unerwartetes crasht, gehen die bereits beantworteten Aufgaben
        # nicht verloren.
        try:
            write_results(results, tasks)
        except Exception as exc:
            print(f"FATAL: could not write {OUTPUT_PATH}: {exc}", file=sys.stderr)
            sys.exit(1)

    print(f"Done: {len(results)} tasks, {time.monotonic() - start:.1f}s total")
    sys.exit(0)


if __name__ == "__main__":
    main()

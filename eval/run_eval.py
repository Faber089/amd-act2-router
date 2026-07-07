"""
Eval v2 — misst den Router so, wie die Jury misst.

Zwei Bewertungsebenen pro Aufgabe:
  1. det  — deterministischer Check (exakte Zahl, Pflicht-Entitaeten,
            ausfuehrbare Code-Tests, Format-Limits). Objektiv, kostenlos,
            aber nicht fuer jede Aufgabe moeglich.
  2. judge — jury-naher LLM-Judge (eval/judge_llm.py), bewertet gegen den
            "expected intent" wie im Participant Guide beschrieben.

Zusaetzlich gemessen (weil der Wettbewerb daran haengt):
  * Latenz pro Aufgabe (30s-Limit!) und Gesamtlaufzeit-Projektion (10 Min),
  * Token-Split prompt/completion (versteckte Reasoning-Tokens sichtbar machen),
  * finish_reason == "length" (abgeschnittene Antworten = Judge-Fail),
  * Eskalationsrate und -gruende pro Kategorie,
  * Kalibrierung Confidence -> Trefferquote,
  * Schwellen-Sweep im --mode local (welche CONFIDENCE_THRESHOLD lohnt sich).

Modi:
  --mode router  (Default) — die echte Kaskade
  --mode local   — alles lokal (Baseline: 0 Tokens, Accuracy-Untergrenze)
  --mode remote  — alles remote (Baseline: Accuracy-Obergrenze, Token-Maximum)

Jeder Lauf schreibt einen JSON-Report nach eval/results/ fuer saubere
Vorher/Nachher-Vergleiche (eiserne Regel: keine Aenderung ohne Messung).
"""
import argparse
import json
import math
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from eval.judge_llm import judge_many
from router import config
from router.judge import extract_code, is_valid_python, parse_local_answer
from router.local_client import ask_local
from router.main import route
from router.remote_client import ask_remote

# Windows-Konsole ist per Default cp1252 — ohne das hier crasht jedes
# Sonderzeichen im Output (real passiert mit einem Emoji in v1).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TASKS_FILE = Path(__file__).parent / "tasks.jsonl"
RESULTS_DIR = Path(__file__).parent / "results"

_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def load_tasks():
    tasks = []
    with open(TASKS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks


def _norm(s):
    return re.sub(r"[\s*]", "", (s or "").lower())


# --- Deterministische Checks -------------------------------------------------

def check_number(answer, value):
    """Exakter Zahlenvergleich statt Substring: '184' enthaelt '84', waere
    beim alten Substring-Check faelschlich OK gewesen."""
    try:
        target = float(value)
    except ValueError:
        return False
    floats = []
    for n in _NUM_RE.findall((answer or "").replace(",", "")):
        try:
            floats.append(float(n))
        except ValueError:
            pass
    return any(abs(f - target) < 1e-6 for f in floats)


def check_label(answer, any_labels):
    a = _norm(answer)
    return any(_norm(lbl) in a for lbl in any_labels)


def count_words(text):
    return len((text or "").split())


def count_sentences(text):
    return len([s for s in re.split(r"[.!?]+", text or "") if s.strip()])


def count_bullets(text):
    return sum(
        1
        for line in (text or "").splitlines()
        if re.match(r"\s*([-*•]|\d+[.)])\s+", line)
    )


def check_keywords(answer, det):
    """Mindestanzahl Schluessel-Fakten + optionale Format-Limits (Woerter,
    Saetze, Bullets). Der Judge prueft Sinn, das hier prueft Substanz+Format."""
    a = _norm(answer)
    hits = sum(1 for v in det["values"] if _norm(v) in a)
    if hits < det.get("required", 1):
        return False
    if det.get("max_words") and count_words(answer) > det["max_words"] * 1.3 + 2:
        return False
    if det.get("max_sentences") and count_sentences(answer) > det["max_sentences"]:
        return False
    if det.get("min_bullets") and count_bullets(answer) < det["min_bullets"]:
        return False
    return True


def run_code_tests(code, tests, timeout=6):
    """Fuehrt den Antwort-Code + Testaufrufe in einem frischen Subprozess aus.
    Timeout faengt Endlosschleifen (z. B. vergessenes n -= 1). Objektiver
    geht Code-Bewertung nicht — genau das fehlte fuer Code Generation."""
    harness = code + "\n" + "\n".join(f"print(repr({t['call']}))" for t in tests)
    try:
        proc = subprocess.run(
            [sys.executable, "-c", harness],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    if proc.returncode != 0:
        return False
    lines = [l.strip() for l in proc.stdout.strip().splitlines()]
    expects = [t["expect"] for t in tests]
    # Der Code selbst darf drucken — nur die LETZTEN len(tests) Zeilen zaehlen.
    return len(lines) >= len(expects) and lines[-len(expects):] == expects


def check_code(answer, det):
    code = extract_code(answer or "")
    if not is_valid_python(code):
        return False
    if det.get("tests"):
        return run_code_tests(code, det["tests"])
    if det.get("must_contain"):
        return det["must_contain"] in code
    return True


def check_det(answer, det):
    """None = kein deterministischer Check moeglich (nur Judge)."""
    if not det:
        return None
    kind = det.get("type")
    if kind == "number":
        return check_number(answer, det["value"])
    if kind == "label":
        return check_label(answer, det["any"])
    if kind == "keywords":
        return check_keywords(answer, det)
    if kind == "code":
        return check_code(answer, det)
    return None


# --- Aufgaben loesen ----------------------------------------------------------

def solve(task, mode, stats):
    question = task["question"]
    if mode == "remote":
        text, tokens = ask_remote(question, stats=stats)
        return text, tokens, "remote"
    if mode == "local":
        text, _ = ask_local(question)
        answer, _, confidence = parse_local_answer(text)
        stats["confidence"] = confidence
        return answer, 0, "local"
    return route(question, verbose=False, stats=stats)


def main():
    parser = argparse.ArgumentParser(description="Eval v2 (jury-nahe Messung)")
    parser.add_argument("--mode", choices=["router", "local", "remote"], default="router")
    parser.add_argument("--judge", choices=["remote", "local", "off"],
                        default=config.EVAL_JUDGE_BACKEND)
    parser.add_argument("--limit", type=int, default=0, help="nur die ersten N Aufgaben")
    parser.add_argument("--category", default="", help="nur diese Kategorie")
    args = parser.parse_args()

    tasks = load_tasks()
    if args.category:
        tasks = [t for t in tasks if t["category"] == args.category]
    if args.limit:
        tasks = tasks[: args.limit]

    print(f"=== EVAL v2 | mode={args.mode} | judge={args.judge} | {len(tasks)} Aufgaben ===\n")

    records = []
    for task in tasks:
        stats = {}
        t0 = time.monotonic()
        try:
            answer, tokens, source = solve(task, args.mode, stats)
        except Exception as exc:
            print(f"[{task['id']:>2}] FEHLER  | {exc}")
            answer, tokens, source = "", 0, "error"
        latency = time.monotonic() - t0

        det = check_det(answer, task.get("det"))
        records.append({
            "id": task["id"],
            "category": task["category"],
            "question": task["question"],
            "answer": answer,
            "tokens": tokens,
            "prompt_tokens": stats.get("remote_prompt_tokens", 0),
            "completion_tokens": stats.get("remote_completion_tokens", 0),
            "finish_reason": stats.get("remote_finish_reason"),
            "source": source,
            "confidence": stats.get("confidence"),
            "escalation_reason": stats.get("escalation_reason"),
            "latency_s": round(latency, 2),
            "det": det,
        })

    # --- Judge-Phase (parallel bei remote) ---
    judge_dev_tokens = 0
    if args.judge != "off":
        print(f"\n... LLM-Judge laeuft ({args.judge}) ...\n")
        verdicts = judge_many(
            [{"question": r["question"], "answer": r["answer"],
              "expected": tasks[i].get("expected", "")}
             for i, r in enumerate(records)],
            backend=args.judge,
        )
        for record, (correct, dev_tokens) in zip(records, verdicts):
            record["judge"] = correct
            judge_dev_tokens += dev_tokens
    else:
        for record in records:
            record["judge"] = None

    # --- Einzelzeilen ---
    for r in records:
        det_str = {True: "OK", False: "FALSCH", None: "  -  "}[r["det"]]
        judge_str = {True: "OK", False: "FALSCH", None: "  -  "}[r["judge"]]
        trunc = " TRUNC!" if r["finish_reason"] == "length" else ""
        print(f"[{r['id']:>2}] det:{det_str:6} judge:{judge_str:6} | {r['source']:13} "
              f"| Conf:{str(r['confidence']):>4} | Tok:{r['tokens']:4} | {r['latency_s']:5.1f}s"
              f"{trunc} | {r['category']}")
        if r["det"] is False or r["judge"] is False:
            print(f"      -> Antwort: {(r['answer'] or '(leer)')[:110]}")

    # --- Kategorie-Tabelle ---
    print("\n=== PRO KATEGORIE ===")
    print(f"{'Kategorie':<20} {'n':>3} {'det-OK':>7} {'judge-OK':>9} {'eskaliert':>10} {'Tokens':>7} {'maxLat':>7}")
    categories = sorted({r["category"] for r in records})
    for cat in categories:
        rs = [r for r in records if r["category"] == cat]
        det_ok = sum(1 for r in rs if r["det"] is True)
        det_n = sum(1 for r in rs if r["det"] is not None)
        judge_ok = sum(1 for r in rs if r["judge"] is True)
        judge_n = sum(1 for r in rs if r["judge"] is not None)
        escalated = sum(1 for r in rs if r["source"].startswith("remote"))
        tokens = sum(r["tokens"] for r in rs)
        max_lat = max(r["latency_s"] for r in rs)
        print(f"{cat:<20} {len(rs):>3} {det_ok:>4}/{det_n:<2} {judge_ok:>6}/{judge_n:<2} "
              f"{escalated:>7}/{len(rs):<2} {tokens:>7} {max_lat:>6.1f}s")

    # --- Gesamtergebnis ---
    n = len(records)
    det_records = [r for r in records if r["det"] is not None]
    det_acc = sum(1 for r in det_records if r["det"]) / len(det_records) * 100 if det_records else 0
    judge_records = [r for r in records if r["judge"] is not None]
    judge_acc = sum(1 for r in judge_records if r["judge"]) / len(judge_records) * 100 if judge_records else 0
    total_tokens = sum(r["tokens"] for r in records)
    prompt_tokens = sum(r["prompt_tokens"] for r in records)
    completion_tokens = sum(r["completion_tokens"] for r in records)
    escalated = sum(1 for r in records if r["source"].startswith("remote"))
    latencies = sorted(r["latency_s"] for r in records)
    total_time = sum(latencies)
    p95 = latencies[max(0, math.ceil(0.95 * len(latencies)) - 1)] if latencies else 0
    truncated = sum(1 for r in records if r["finish_reason"] == "length")
    over_25s = sum(1 for r in records if r["latency_s"] > 25)

    # Versteckte Denk-Tokens: completion_tokens massiv ueber der sichtbaren
    # Antwortlaenge (~3.5 Zeichen/Token) deutet auf Reasoning-Overhead hin.
    thinking = []
    for r in records:
        if r["completion_tokens"]:
            visible = max(1, math.ceil(len(r["answer"]) / 3.5))
            overhead = r["completion_tokens"] - visible
            if overhead > 30:
                thinking.append((r["id"], overhead, r["completion_tokens"]))

    print("\n=== ERGEBNIS ===")
    print(f"Accuracy deterministisch: {det_acc:.1f}% ({sum(1 for r in det_records if r['det'])}/{len(det_records)})")
    if judge_records:
        print(f"Accuracy LLM-Judge:       {judge_acc:.1f}% ({sum(1 for r in judge_records if r['judge'])}/{len(judge_records)})")
    print(f"Tokens (Leaderboard):     {total_tokens}  (prompt {prompt_tokens} + completion {completion_tokens})")
    print(f"Eskalationen:             {escalated}/{n} ({escalated / n * 100:.0f}%)")
    print(f"Latenz: gesamt {total_time:.0f}s | p95 {p95:.1f}s | >25s: {over_25s} Aufgabe(n)")
    print(f"Hochrechnung Gesamtlauf:  {total_time:.0f}s von 600s Budget"
          + ("  !! ZU LANGSAM" if total_time > 540 else ""))
    if truncated:
        print(f"!! {truncated} Antwort(en) abgeschnitten (finish_reason=length) — Judge-Fail-Risiko, max_tokens pruefen")
    if thinking:
        overhead_sum = sum(o for _, o, _ in thinking)
        print(f"!! Versteckte Denk-Tokens vermutet bei {len(thinking)} Aufgabe(n), "
              f"~{overhead_sum} Tokens Overhead: {[(i, o) for i, o, _ in thinking[:8]]}")
    if judge_dev_tokens:
        print(f"(Judge-Entwicklungskosten: {judge_dev_tokens} Tokens ueber eigenen Key — zaehlt NICHT fuers Leaderboard)")

    # --- Meinungsverschiedenheiten det vs judge ---
    disagreements = [r for r in records if r["det"] is not None and r["judge"] is not None
                     and r["det"] != r["judge"]]
    if disagreements:
        print(f"\n{len(disagreements)} Aufgabe(n) mit det/judge-Widerspruch (manuell ansehen!):")
        for r in disagreements:
            print(f"   [{r['id']}] det={'OK' if r['det'] else 'FALSCH'} vs judge={'OK' if r['judge'] else 'FALSCH'} | {r['answer'][:80]}")

    # --- Kalibrierung (nur wo lokale Antworten mit Confidence vorliegen) ---
    local_records = [(r["confidence"], r["judge"] if r["judge"] is not None else r["det"])
                     for r in records
                     if r["confidence"] is not None and r["source"] in ("local", "local-fallback")]
    local_records = [(c, ok) for c, ok in local_records if ok is not None]
    if local_records:
        print("\n=== KALIBRIERUNG (lokal gebliebene Antworten) ===")
        print("Confidence | Anzahl | davon korrekt")
        for lo, hi in ((0, 49), (50, 69), (70, 79), (80, 89), (90, 99), (100, 100)):
            bucket = [ok for c, ok in local_records if lo <= c <= hi]
            if bucket:
                pct = sum(bucket) / len(bucket) * 100
                print(f"  {lo:>3}-{hi:<3}  | {len(bucket):>6} | {sum(bucket)}/{len(bucket)} ({pct:.0f}%)")

    # --- Schwellen-Sweep (nur --mode local sinnvoll: dort gibt es fuer JEDE
    #     Aufgabe eine lokale Antwort + Confidence + Korrektheit) ---
    if args.mode == "local":
        sweep_records = [(r["confidence"] or 0,
                          r["judge"] if r["judge"] is not None else r["det"])
                         for r in records]
        sweep_records = [(c, ok) for c, ok in sweep_records if ok is not None]
        if sweep_records:
            print("\n=== SCHWELLEN-SWEEP (was waere bei CONFIDENCE_THRESHOLD=X) ===")
            print("Schwelle | bleibt lokal | Accuracy der lokalen | eskaliert")
            for threshold in (50, 60, 70, 80, 90, 95, 100):
                kept = [ok for c, ok in sweep_records if c >= threshold]
                share = len(kept) / len(sweep_records) * 100
                acc = (sum(kept) / len(kept) * 100) if kept else 0
                print(f"  {threshold:>6} | {len(kept):>3} ({share:4.0f}%)   | "
                      f"{acc:5.1f}%              | {len(sweep_records) - len(kept)}")

    # --- JSON-Report fuer Vorher/Nachher-Vergleiche ---
    RESULTS_DIR.mkdir(exist_ok=True)
    report_path = RESULTS_DIR / f"report_{args.mode}_{datetime.now():%Y%m%d_%H%M%S}.json"
    report = {
        "mode": args.mode,
        "judge": args.judge,
        "config": {
            "local_model": config.LOCAL_MODEL,
            "remote_model": config.REMOTE_MODEL,
            "confidence_threshold": config.CONFIDENCE_THRESHOLD,
            "remote_max_tokens": config.REMOTE_MAX_TOKENS,
            "use_selfcheck": config.USE_SELFCHECK,
        },
        "summary": {
            "n": n,
            "det_accuracy": round(det_acc, 1),
            "judge_accuracy": round(judge_acc, 1),
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "escalated": escalated,
            "total_time_s": round(total_time, 1),
            "p95_latency_s": p95,
            "truncated": truncated,
        },
        "records": records,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nReport gespeichert: {report_path}")


if __name__ == "__main__":
    main()

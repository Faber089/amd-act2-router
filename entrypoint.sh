#!/bin/sh
# Startet das im Image eingebackene Ollama und danach den Wettbewerbs-Batch.
# Participant Guide: Container muss in 60s startklar sein — der Ollama-Server
# selbst ist in wenigen Sekunden oben; das eigentliche Modell laedt beim
# Warm-up-Call in submission/run.py (zaehlt gegen die 10-Minuten-Laufzeit,
# nicht gegen die 60s).
set -u

# Kontextfenster 4096 (Robustheits-Audit 11.7.): bei 2048 wuerde eine lange
# Summarisation-Passage (>350 Woerter) plus Format-Prompt still abgeschnitten
# — Muell-Antwort ohne Fehlermeldung. 4096 kostet bei einem 1,7B-Modell nur
# wenige hundert MB KV-Cache und passt sicher ins 4-GB-Budget der Judging-VM.
export OLLAMA_CONTEXT_LENGTH=4096
# Modell NIE entladen: Ollama wirft Modelle nach 5min Idle aus dem RAM —
# eine laengere Remote-Phase im 10-Min-Lauf wuerde sonst mitten im
# Wettbewerb einen Reload (~10-20s auf 2 vCPU) erzwingen = Timeout-Gefahr.
export OLLAMA_KEEP_ALIVE=-1

ollama serve >/tmp/ollama.log 2>&1 &

i=0
until ollama list >/dev/null 2>&1; do
  i=$((i+1))
  if [ "$i" -ge 55 ]; then
    # Nicht abbrechen: run.py erkennt ein totes lokales Modell selbst und
    # schaltet auf Remote-direkt um — besser wenige Tokens zahlen als 0 Punkte.
    echo "WARN: ollama not ready after 55s, continuing anyway" >&2
    break
  fi
  sleep 1
done

exec python3 -m submission.run

#!/bin/sh
# Startet das im Image eingebackene Ollama und danach den Wettbewerbs-Batch.
# Participant Guide: Container muss in 60s startklar sein — der Ollama-Server
# selbst ist in wenigen Sekunden oben; das eigentliche Modell laedt beim
# Warm-up-Call in submission/run.py (zaehlt gegen die 10-Minuten-Laufzeit,
# nicht gegen die 60s).
set -u

# Kleiner Kontext = weniger RAM + schnelleres Prompt-Processing auf der
# 2-vCPU/4-GB-Judging-VM (Guide-Update 8.7.). Unsere Prompts bleiben weit
# unter 2048 Tokens.
export OLLAMA_CONTEXT_LENGTH=2048

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

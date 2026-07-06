FROM python:3.11-slim

WORKDIR /app

# Zuerst nur die Abhaengigkeiten kopieren + installieren (Docker-Cache-Trick:
# solange requirements.txt sich nicht aendert, wird dieser Schritt nicht neu gebaut).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Dann den restlichen Code.
COPY router/ ./router/
COPY eval/ ./eval/
COPY submission/ ./submission/

# Wettbewerbs-Entrypoint (Participant Guide): liest /input/tasks.json,
# schreibt /output/results.json. Fuer lokale Eval-Laeufe stattdessen manuell
# `docker run ... python -m eval.run_eval` als Override-Kommando nutzen.
CMD ["python", "-m", "submission.run"]

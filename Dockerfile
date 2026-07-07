# Wettbewerbs-Image (Track 1) — SELF-CONTAINED.
#
# Kritisch: Auf der Judging-VM gibt es KEIN Ollama auf dem Host und keinen
# garantierten Internetzugang ausser dem Fireworks-Proxy. Das lokale Modell
# (der Kern unserer 0-Token-Strategie) muss deshalb KOMPLETT im Image stecken:
# Ollama-Server + Modellgewichte werden zur BUILD-Zeit eingebacken.
#
# Build (linux/amd64 ist Pflicht, sonst Pull-Fehler = 0 Punkte):
#   docker buildx build --platform linux/amd64 -t amd-act2-router:latest --load .
FROM ollama/ollama:latest

# Python fuer den Router (Basisimage ist Ubuntu, ohne Python)
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Modellgewichte zur BUILD-Zeit einbacken: ollama kurz starten, Modell ziehen.
# Die Gewichte landen in /root/.ollama und bleiben im Image-Layer.
ARG LOCAL_MODEL=gemma2:2b
RUN ollama serve & \
    i=0; until ollama list >/dev/null 2>&1; do \
        i=$((i+1)); [ "$i" -ge 30 ] && echo "ollama not ready" && exit 1; sleep 1; \
    done \
    && ollama pull ${LOCAL_MODEL}

WORKDIR /app

# Nur die Submission-Abhaengigkeiten (kein fastapi/uvicorn — das braucht nur
# die Demo). Docker-Cache-Trick: Requirements zuerst, Code danach.
COPY requirements-submission.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements-submission.txt

COPY router/ ./router/
COPY submission/ ./submission/
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Der Router spricht das MITGELIEFERTE Ollama im Container (127.0.0.1),
# nicht mehr host.docker.internal. Fuer lokale Entwicklung weiterhin per
# Env-Var uebersteuerbar.
ENV OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
ENV LOCAL_MODEL=${LOCAL_MODEL}

# Wettbewerbs-Ablauf: Ollama starten, warten bis bereit, dann Batch-Lauf
# (liest /input/tasks.json, schreibt /output/results.json, Exit 0 = Erfolg).
ENTRYPOINT ["/app/entrypoint.sh"]

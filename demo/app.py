"""
Minimale Demo-Web-App fuer die Pflicht-"Demo-Application-URL" der Submission.
Wrappt router.main.route() direkt -- keine eigene Routing-Logik, keine DB.
"""
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from router.main import route

app = FastAPI()
app.mount("/static", StaticFiles(directory="demo/static"), name="static")

totals = {"requests": 0, "local": 0, "remote": 0, "total_tokens": 0}


class Question(BaseModel):
    question: str


@app.get("/")
def index():
    return FileResponse("demo/static/index.html")


@app.post("/ask")
def ask(payload: Question):
    # verbose=True, damit die Eskalations-Begruendung (Vertrauenswert) im
    # Server-Log sichtbar ist -- sonst ist von der UI aus nicht erkennbar,
    # WARUM eskaliert wurde.
    answer, tokens, source = route(payload.question, verbose=True)

    totals["requests"] += 1
    totals["total_tokens"] += tokens
    totals["local" if source == "local" else "remote"] += 1

    return {
        "question": payload.question,
        "answer": answer,
        "tokens": tokens,
        "source": source,
        "totals": dict(totals),
    }

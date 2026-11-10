from fastapi import FastAPI

from .schemas import AskRequest, AskResponse

app = FastAPI(title="FieldDex API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    return AskResponse(
        kind="answer",
        text=f"(stub) You asked: {req.question}",
        sources=[],
        session_id=req.session_id or "stub"
    )

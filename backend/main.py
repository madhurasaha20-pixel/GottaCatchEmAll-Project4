from fastapi import FastAPI

from . import chat_service

from .schemas import AskRequest, AskResponse

app = FastAPI(title="FieldDex API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    return chat_service.answer(req.session_id, req.question, req.top_k)

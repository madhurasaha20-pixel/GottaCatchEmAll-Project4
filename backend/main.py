from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import chat_service
from .llm import LLMUnavailable
from .schemas import AskRequest, AskResponse

app = FastAPI(title="FieldDex API")


@app.exception_handler(LLMUnavailable)
def llm_unavailable(request: Request, exc: LLMUnavailable):
    return JSONResponse(
        status_code=503,
        content={"detail": "The language model is unavailable."},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    return chat_service.answer(req.session_id, req.question, req.top_k)
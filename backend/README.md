# FieldDex backend

FastAPI server that the Streamlit frontend talks to. It keeps short per-session
chat history in memory and generates answers with a local Llama 3.2 model
through Ollama. Retrieval (RAG) is not wired in yet.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running, with the model pulled:

```bash
ollama pull llama3.2
```

## Setup

Run everything from the repository root.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env_example .env
```

Edit `.env` if your Ollama runs somewhere else or you want a different model.
`.env` is gitignored; `.env_example` is the committed template.

| Variable | Default | Meaning |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Where Ollama is listening |
| `OLLAMA_MODEL` | `llama3.2` | Model name passed to Ollama |
| `LLM_TIMEOUT` | `60` | Seconds to wait for a model reply |

The server reloads on code changes but not on `.env` changes. Restart it
after editing `.env`.

## Run

```bash
fastapi dev backend/main.py
```

The server listens on http://localhost:8000, with interactive docs at
http://localhost:8000/docs. Then start the frontend in another terminal (it
defaults to `http://localhost:8000/ask`):

```bash
python -m streamlit run frontend/app.py
```

## Notes

- History lives in process memory, so it is lost on restart (including
  reloads triggered by code changes).
- The first request after Ollama starts is slow while the model loads.
- Without retrieval, answers come from the model's own knowledge and can be
  wrong. That is expected until the retriever is added.

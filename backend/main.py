from fastapi import FastAPI

app = FastAPI(title="FieldDex API")

@app.get("/health")
def health():
    return {"status": "ok"}
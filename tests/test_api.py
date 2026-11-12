import pytest
pytest.importorskip("ollama")
from fastapi.testclient import TestClient
from backend.main import app
client=TestClient(app)

def test_health_status():
    r=client.get('/health')
    assert r.status_code==200 and r.json()=={'status':'ok'}

def test_ask_requires_question():
    r=client.post('/ask',json={})
    assert r.status_code==422

def test_ask_rejects_empty_question():
    assert client.post('/ask',json={'question':''}).status_code==422

@pytest.mark.parametrize('top_k',[0,11])
def test_ask_rejects_invalid_top_k(top_k):
    assert client.post('/ask',json={'question':'Pikachu','top_k':top_k}).status_code==422

def test_missing_path_returns_404():
    assert client.get('/not-a-route').status_code==404

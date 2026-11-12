import os
import pytest
pytest.importorskip('ollama')
from fastapi.testclient import TestClient
from backend.main import app
from backend import memory


def test_live_ask_returns_answer_and_session():
    response=TestClient(app).post('/ask',json={'question':'What type is Pikachu?'})
    assert response.status_code==200
    body=response.json()
    assert body['kind']=='answer' and body['text'].strip() and body['session_id']

def test_live_ask_saves_two_chat_messages():
    response=TestClient(app).post('/ask',json={'question':'What type is Eevee?'})
    assert response.status_code==200
    history=memory.get(response.json()['session_id'])
    assert [message['role'] for message in history]==['user','assistant']

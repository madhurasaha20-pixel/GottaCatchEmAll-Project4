import os
import pytest
ollama=pytest.importorskip('ollama')
from backend.llm import generate, LLMUnavailable, SYSTEM_PROMPT



def test_live_model_answers_pokemon_question():
    result=generate([], 'Answer with one word only: what type is Pikachu?')
    assert isinstance(result,str) and result.strip()

def test_live_model_accepts_history():
    result=generate([{'role':'user','content':'My favorite is Eevee.'}, {'role':'assistant','content':'Okay.'}], 'What Pokémon did I mention?')
    assert isinstance(result,str) and result.strip()

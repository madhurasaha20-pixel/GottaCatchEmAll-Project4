import pytest
from pydantic import ValidationError
from backend.schemas import AskRequest, AskResponse, Source

def test_request_defaults():
    r=AskRequest(question="Pikachu")
    assert r.top_k==4 and r.session_id is None

def test_request_accepts_boundary_top_k():
    assert AskRequest(question="x",top_k=1).top_k==1
    assert AskRequest(question="x",top_k=10).top_k==10

@pytest.mark.parametrize('value',[0,11])
def test_request_rejects_out_of_range_top_k(value):
    with pytest.raises(ValidationError): AskRequest(question="x",top_k=value)

def test_request_rejects_empty_question():
    with pytest.raises(ValidationError): AskRequest(question="")

def test_response_default_and_sources():
    r=AskResponse(text="Electric",session_id="s",sources=[Source(title="Dex",section="Type",url="https://example.org")])
    assert r.kind=="answer" and r.sources[0].section=="Type"

def test_response_rejects_invalid_kind():
    with pytest.raises(ValidationError): AskResponse(kind="unknown",text="hi",session_id="s")

def test_response_sources_are_independent():
    a=AskResponse(text="A",session_id="a")
    b=AskResponse(text="B",session_id="b")
    a.sources.append(Source(title="Added"))
    assert b.sources==[]

import uuid
from backend import memory

def sid(): return "test-" + uuid.uuid4().hex

def test_unknown_session_empty():
    assert memory.get(sid()) == []

def test_append_user_message():
    s = sid(); memory.append(s, "user", "Pikachu")
    assert memory.get(s) == [{"role":"user", "content":"Pikachu"}]

def test_message_order():
    s = sid(); memory.append(s,"user","Hi"); memory.append(s,"assistant","Hello")
    assert [m['role'] for m in memory.get(s)] == ['user','assistant']

def test_session_isolation():
    a,b=sid(),sid();memory.append(a,"user","Hello")
    assert memory.get(b)==[]

def test_get_returns_new_list():
    s=sid();memory.append(s,"user","Hello")
    memory.get(s).append({"role":"assistant","content":"fake"})
    assert len(memory.get(s))==1

def test_limit_keeps_last_twelve():
    s=sid()
    for i in range(15): memory.append(s,"user",str(i))
    assert [x['content'] for x in memory.get(s)] == [str(i) for i in range(3,15)]

MAX_MESSAGES = 12

_sessions: dict[str, list[dict]] = {}

def get(session_id: str) -> list[dict]:
  return list(_sessions.get(session_id, []))

def append(session_id: str, role: str, content: str) -> None:
  messages = _sessions.setdefault(session_id, [])
  messages.append({"role": role, "content": content})
  _sessions[session_id] = messages[-MAX_MESSAGES:]

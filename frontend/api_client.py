"""HTTP adapter only; retrieval and answer generation belong to the backend."""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class APIError(Exception):
    """A user-readable connection or response error."""


def ask_api(endpoint: str, question: str, top_k: int, session_id: str | None = None) -> dict:
    """POST the proposed frontend contract; see frontend/README.md."""
    if urlsplit(endpoint).scheme not in {"http", "https"} or not urlsplit(endpoint).netloc:
        raise APIError("Enter a complete HTTP or HTTPS API endpoint in Connection settings.")
    request = Request(
        endpoint,
        data=json.dumps({"question": question, "top_k": top_k, "session_id": session_id}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            result = json.load(response)
    except HTTPError as exc:
        raise APIError(f"The API returned HTTP {exc.code}. Check the endpoint or try again.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise APIError("Cannot reach the API. Check that the backend is running and try again.") from exc
    except (ValueError, UnicodeError) as exc:
        raise APIError("The API did not return valid JSON. Check the response contract.") from exc

    if not isinstance(result, dict) or not isinstance(result.get("text"), str) or not result["text"].strip():
        raise APIError("The API response needs a nonempty 'text' field.")
    if result.get("kind", "answer") not in {"answer", "refusal"}:
        raise APIError("The API response kind must be 'answer' or 'refusal'.")
    sources = result.get("sources") or []
    if not isinstance(sources, list) or any(
        not isinstance(source, dict)
        or any(not isinstance(source.get(key, ""), str) for key in ("title", "section", "url"))
        for source in sources
    ):
        raise APIError("The API returned invalid sources. Check the response contract.")
    # Only HTTP(S) source links are passed to the existing HTML renderer.
    safe_sources = []
    for source in sources:
        source = dict(source)
        if urlsplit(source.get("url", "")).scheme not in {"http", "https"}:
            source.pop("url", None)
        safe_sources.append(source)
    return {"text": result["text"], "kind": result.get("kind", "answer"), "sources": safe_sources, "session_id": result.get("session_id")}

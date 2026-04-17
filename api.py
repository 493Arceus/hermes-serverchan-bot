from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

API_BASE_URL = "https://bot-go.apijia.cn"


def _json_request(url: str, method: str = "GET", body: Optional[dict] = None) -> Dict[str, Any]:
    data = None
    headers = {"Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read().decode("utf-8")
            return json.loads(payload) if payload else {"ok": True}
    except urllib.error.HTTPError as exc:
        try:
            payload = exc.read().decode("utf-8")
            parsed = json.loads(payload) if payload else {}
        except Exception:
            parsed = {}
        parsed.setdefault("ok", False)
        parsed.setdefault("error", f"HTTP {exc.code}: {exc.reason}")
        return parsed
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def get_me(token: str) -> Dict[str, Any]:
    return _json_request(f"{API_BASE_URL}/bot{token}/getMe")


def send_message(
    token: str,
    chat_id: str | int,
    text: str,
    parse_mode: Optional[str] = None,
    silent: Optional[bool] = None,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "chat_id": int(chat_id) if str(chat_id).strip().lstrip("-").isdigit() else chat_id,
        "text": text,
    }
    if parse_mode:
        body["parse_mode"] = parse_mode
    if silent is not None:
        body["silent"] = silent
    return _json_request(f"{API_BASE_URL}/bot{token}/sendMessage", method="POST", body=body)


def send_chat_action(token: str, chat_id: str | int, action: str = "typing") -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "chat_id": int(chat_id) if str(chat_id).strip().lstrip("-").isdigit() else chat_id,
        "action": action,
    }
    return _json_request(f"{API_BASE_URL}/bot{token}/sendChatAction", method="POST", body=body)


def get_updates(token: str, offset: Optional[int] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
    params = {}
    if offset is not None:
        params["offset"] = str(offset)
    if timeout is not None:
        params["timeout"] = str(timeout)
    qs = urllib.parse.urlencode(params)
    url = f"{API_BASE_URL}/bot{token}/getUpdates"
    if qs:
        url = f"{url}?{qs}"
    return _json_request(url)

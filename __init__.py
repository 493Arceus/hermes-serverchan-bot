from __future__ import annotations

import argparse
import json
import logging
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from . import api, schemas

logger = logging.getLogger(__name__)

_PLUGIN_DIR = Path(__file__).resolve().parent
_CONFIG_PATH = _PLUGIN_DIR / "config.yaml"
_STATE_PATH = _PLUGIN_DIR / "state.json"

_CTX = None
_POLLER = None
_LOCK = threading.RLock()
_PENDING_BY_MESSAGE: dict[str, "InboundMessage"] = {}
_ACTIVE_BY_SESSION: dict[str, "InboundMessage"] = {}
_LAST_ACTIVE_CHAT_ID: Optional[str] = None

_DEFAULT_CONFIG = {
    "enabled": True,
    "polling_enabled": True,
    "polling_interval_ms": 3000,
    "poll_timeout_seconds": 20,
    "default_chat_id": "",
    "parse_mode": "markdown",
    "silent": False,
    "metadata_prefix": "[[serverchan-bot",
    "chunk_size": 1800,
}


@dataclass
class InboundMessage:
    update_id: int
    message_id: int
    chat_id: str
    text: str
    injected_message: str
    timestamp_ms: int


class ServerChanPoller(threading.Thread):
    def __init__(self, ctx):
        super().__init__(name="serverchan-bot-poller", daemon=True)
        self.ctx = ctx
        self.stop_event = threading.Event()
        self.started_at = time.time()
        self._last_error: Optional[str] = None

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    def stop(self) -> None:
        self.stop_event.set()

    def run(self) -> None:
        logger.info("serverchan-bot poller started")
        while not self.stop_event.is_set():
            cfg = _load_config()
            if not cfg.get("enabled", True) or not cfg.get("polling_enabled", True):
                self.stop_event.wait(1.0)
                continue

            token = _get_token()
            if not token:
                self._last_error = "SERVERCHAN_BOT_TOKEN is not set"
                self.stop_event.wait(2.0)
                continue

            state = _load_state()
            offset = state.get("last_update_id")
            if isinstance(offset, int):
                offset += 1
            else:
                offset = None

            timeout = _safe_int(cfg.get("poll_timeout_seconds"), 20)
            result = api.get_updates(token, offset=offset, timeout=timeout)
            if not result.get("ok"):
                self._last_error = str(result.get("error") or "unknown error")
                logger.warning("serverchan-bot polling failed: %s", self._last_error)
                self.stop_event.wait(max(_safe_int(cfg.get("polling_interval_ms"), 3000) / 1000.0, 1.0))
                continue

            self._last_error = None
            updates = result.get("result") or []
            for update in updates:
                try:
                    handled = _handle_update(self.ctx, update)
                    if handled:
                        state["last_update_id"] = int(update.get("update_id"))
                        _save_state(state)
                except Exception as exc:
                    self._last_error = str(exc)
                    logger.exception("serverchan-bot update handling failed: %s", exc)

            if not updates:
                self.stop_event.wait(max(_safe_int(cfg.get("polling_interval_ms"), 3000) / 1000.0, 0.2))

        logger.info("serverchan-bot poller stopped")


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        logger.warning("Failed to read %s: %s", path, exc)
        return {}


def _load_config() -> dict:
    cfg = dict(_DEFAULT_CONFIG)
    cfg.update(_load_yaml(_CONFIG_PATH))
    return cfg


def _load_state() -> dict:
    if not _STATE_PATH.exists():
        return {}
    try:
        return json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    _STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_token() -> str:
    import os

    return os.getenv("SERVERCHAN_BOT_TOKEN", "").strip()


def _default_chat_id() -> str:
    global _LAST_ACTIVE_CHAT_ID
    cfg = _load_config()
    configured = str(cfg.get("default_chat_id") or "").strip()
    if configured:
        return configured
    return _LAST_ACTIVE_CHAT_ID or ""


def _chunk_text(text: str, chunk_size: int) -> list[str]:
    clean = (text or "").strip()
    if not clean:
        return []
    if len(clean) <= chunk_size:
        return [clean]

    parts: list[str] = []
    remaining = clean
    while remaining:
        if len(remaining) <= chunk_size:
            parts.append(remaining)
            break
        split_at = remaining.rfind("\n\n", 0, chunk_size)
        if split_at < chunk_size // 2:
            split_at = remaining.rfind("\n", 0, chunk_size)
        if split_at < chunk_size // 2:
            split_at = chunk_size
        parts.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].lstrip()
    return [p for p in parts if p]


def _send_text(chat_id: str, text: str, parse_mode: Optional[str] = None, silent: Optional[bool] = None) -> dict:
    token = _get_token()
    if not token:
        return {"ok": False, "error": "SERVERCHAN_BOT_TOKEN is not set"}
    cfg = _load_config()
    mode = parse_mode or str(cfg.get("parse_mode") or "markdown")
    is_silent = silent if silent is not None else bool(cfg.get("silent", False))
    chunk_size = _safe_int(cfg.get("chunk_size"), 1800)
    results = []
    for chunk in _chunk_text(text, chunk_size):
        results.append(api.send_message(token, chat_id, chunk, parse_mode=mode, silent=is_silent))
    ok = all(r.get("ok") for r in results) if results else False
    return {"ok": ok, "chat_id": chat_id, "count": len(results), "results": results}


def _send_typing(chat_id: str) -> None:
    token = _get_token()
    if not token:
        return
    try:
        api.send_chat_action(token, chat_id, action="typing")
    except Exception:
        logger.debug("serverchan-bot typing indicator failed", exc_info=True)


def _format_injected_message(update_id: int, message_id: int, chat_id: str, text: str) -> str:
    prefix = str(_load_config().get("metadata_prefix") or "[[serverchan-bot").strip()
    return f"{prefix} chat_id={chat_id} message_id={message_id} update_id={update_id}]]\n{text}"


def _parse_update(update: dict) -> Optional[InboundMessage]:
    message = update.get("message") or {}
    text = message.get("text")
    if not isinstance(text, str) or not text.strip():
        return None

    sender = message.get("from") or {}
    if sender.get("is_bot") is True:
        return None

    raw_chat_id = message.get("chat_id")
    if raw_chat_id is None:
        chat = message.get("chat") or {}
        raw_chat_id = chat.get("id")
    if raw_chat_id is None:
        return None

    update_id = update.get("update_id")
    message_id = message.get("message_id")
    if not isinstance(update_id, int) or not isinstance(message_id, int):
        return None

    chat_id = str(raw_chat_id)
    injected = _format_injected_message(update_id, message_id, chat_id, text)
    return InboundMessage(
        update_id=update_id,
        message_id=message_id,
        chat_id=chat_id,
        text=text,
        injected_message=injected,
        timestamp_ms=int(time.time() * 1000),
    )


def _handle_update(ctx, update: dict) -> bool:
    global _LAST_ACTIVE_CHAT_ID

    inbound = _parse_update(update)
    if inbound is None:
        return False

    injected = ctx.inject_message(inbound.injected_message, role="user")
    if not injected:
        logger.warning("serverchan-bot could not inject message; CLI reference unavailable")
        return False

    with _LOCK:
        _PENDING_BY_MESSAGE[inbound.injected_message] = inbound
        _LAST_ACTIVE_CHAT_ID = inbound.chat_id
    logger.info("serverchan-bot injected inbound message from chat %s", inbound.chat_id)
    return True


def _ensure_poller(ctx) -> ServerChanPoller:
    global _POLLER
    with _LOCK:
        if _POLLER is None or not _POLLER.is_alive():
            _POLLER = ServerChanPoller(ctx)
            _POLLER.start()
        return _POLLER


def _stop_poller() -> bool:
    global _POLLER
    with _LOCK:
        if _POLLER is None:
            return False
        _POLLER.stop()
        _POLLER.join(timeout=2.0)
        _POLLER = None
        return True


def _current_status() -> dict:
    poller_alive = bool(_POLLER and _POLLER.is_alive())
    cfg = _load_config()
    state = _load_state()
    return {
        "ok": True,
        "enabled": bool(cfg.get("enabled", True)),
        "polling_enabled": bool(cfg.get("polling_enabled", True)),
        "poller_alive": poller_alive,
        "last_error": getattr(_POLLER, "last_error", None) if _POLLER else None,
        "default_chat_id": str(cfg.get("default_chat_id") or ""),
        "last_active_chat_id": _LAST_ACTIVE_CHAT_ID,
        "last_update_id": state.get("last_update_id"),
        "token_configured": bool(_get_token()),
        "config_path": str(_CONFIG_PATH),
        "state_path": str(_STATE_PATH),
        "pending_inbound": len(_PENDING_BY_MESSAGE),
        "active_sessions": len(_ACTIVE_BY_SESSION),
    }


def _status_text() -> str:
    s = _current_status()
    return (
        "Server酱³ bridge status\n"
        f"- enabled: {s['enabled']}\n"
        f"- polling_enabled: {s['polling_enabled']}\n"
        f"- poller_alive: {s['poller_alive']}\n"
        f"- token_configured: {s['token_configured']}\n"
        f"- default_chat_id: {s['default_chat_id'] or '-'}\n"
        f"- last_active_chat_id: {s['last_active_chat_id'] or '-'}\n"
        f"- last_update_id: {s['last_update_id']}\n"
        f"- pending_inbound: {s['pending_inbound']}\n"
        f"- active_sessions: {s['active_sessions']}\n"
        f"- last_error: {s['last_error'] or '-'}\n"
        f"- config_path: {s['config_path']}"
    )


def _on_session_start(session_id: str = "", platform: str = "", **kwargs):
    if platform != "cli":
        return
    if _CTX is not None:
        _ensure_poller(_CTX)


def _on_pre_llm_call(session_id: str = "", user_message: str = "", **kwargs):
    inbound = None
    with _LOCK:
        inbound = _PENDING_BY_MESSAGE.pop(user_message, None)
        if inbound is not None:
            _ACTIVE_BY_SESSION[session_id] = inbound
    if inbound is None:
        return None

    _send_typing(inbound.chat_id)
    return {
        "context": (
            "The current turn came from a Server酱³ Bot inbound message. "
            "The first line is bridge metadata; ignore it when understanding the user's request. "
            "Reply naturally to the human sender. Do not mention internal metadata like chat_id, "
            "message_id, or update_id unless the user explicitly asks for them."
        )
    }


def _on_post_llm_call(session_id: str = "", assistant_response: str = "", **kwargs):
    inbound = None
    with _LOCK:
        inbound = _ACTIVE_BY_SESSION.pop(session_id, None)
    if inbound is None:
        return
    if not assistant_response.strip():
        logger.info("serverchan-bot no assistant response for chat %s", inbound.chat_id)
        return
    result = _send_text(inbound.chat_id, assistant_response)
    if not result.get("ok"):
        logger.warning("serverchan-bot reply failed for chat %s: %s", inbound.chat_id, result)


def _on_session_end(session_id: str = "", **kwargs):
    with _LOCK:
        _ACTIVE_BY_SESSION.pop(session_id, None)


def _tool_send_message(args: dict, **kwargs) -> str:
    text = str(args.get("text") or "").strip()
    chat_id = str(args.get("chat_id") or "").strip() or _default_chat_id()
    parse_mode = args.get("parse_mode")
    silent = args.get("silent")
    if not text:
        return json.dumps({"ok": False, "error": "text is required"}, ensure_ascii=False)
    if not chat_id:
        return json.dumps(
            {"ok": False, "error": "chat_id is required unless default_chat_id or a recent inbound chat is available"},
            ensure_ascii=False,
        )
    return json.dumps(_send_text(chat_id, text, parse_mode=parse_mode, silent=silent), ensure_ascii=False)


def _tool_get_updates(args: dict, **kwargs) -> str:
    token = _get_token()
    if not token:
        return json.dumps({"ok": False, "error": "SERVERCHAN_BOT_TOKEN is not set"}, ensure_ascii=False)
    offset = args.get("offset")
    timeout = args.get("timeout")
    result = api.get_updates(token, offset=offset, timeout=timeout)
    return json.dumps(result, ensure_ascii=False)


def _tool_status(args: dict, **kwargs) -> str:
    return json.dumps(_current_status(), ensure_ascii=False)


def _setup_cli(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="serverchan_action")

    sub.add_parser("status", help="Show bridge status")
    sub.add_parser("start", help="Start the background poller")
    sub.add_parser("stop", help="Stop the background poller")
    sub.add_parser("test", help="Call getMe to verify the bot token")

    send_p = sub.add_parser("send", help="Send a message")
    send_p.add_argument("--chat-id", help="Target chat ID")
    send_p.add_argument("--text", required=True, help="Message text")
    send_p.add_argument("--parse-mode", choices=["text", "markdown"], default=None)
    send_p.add_argument("--silent", action="store_true")


def _cli_handler(args: argparse.Namespace) -> int:
    action = getattr(args, "serverchan_action", None) or "status"
    if action == "status":
        print(_status_text())
        return 0
    if action == "start":
        if _CTX is None:
            print("serverchan-bot plugin context is not ready")
            return 1
        _ensure_poller(_CTX)
        print("serverchan-bot poller started")
        return 0
    if action == "stop":
        stopped = _stop_poller()
        print("serverchan-bot poller stopped" if stopped else "serverchan-bot poller was not running")
        return 0
    if action == "test":
        token = _get_token()
        if not token:
            print("SERVERCHAN_BOT_TOKEN is not set")
            return 1
        result = api.get_me(token)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1
    if action == "send":
        chat_id = str(getattr(args, "chat_id", "") or "").strip() or _default_chat_id()
        if not chat_id:
            print("chat_id is required unless default_chat_id or a recent inbound chat is available")
            return 1
        result = _send_text(chat_id, args.text, parse_mode=args.parse_mode, silent=bool(args.silent))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1
    print(f"Unknown action: {action}")
    return 1


def _slash_handler(raw_args: str) -> str:
    cmd = (raw_args or "status").strip().lower()
    if cmd == "status":
        return _status_text()
    if cmd == "start":
        if _CTX is None:
            return "serverchan-bot plugin context is not ready"
        _ensure_poller(_CTX)
        return "serverchan-bot poller started"
    if cmd == "stop":
        _stop_poller()
        return "serverchan-bot poller stopped"
    return "Usage: /serverchan status|start|stop"


def register(ctx) -> None:
    global _CTX
    _CTX = ctx

    ctx.register_tool(
        name="serverchan_send_message",
        toolset="serverchan",
        schema=schemas.SERVERCHAN_SEND_MESSAGE,
        handler=_tool_send_message,
        description="Send a Server酱³ Bot message",
        emoji="📨",
    )
    ctx.register_tool(
        name="serverchan_get_updates",
        toolset="serverchan",
        schema=schemas.SERVERCHAN_GET_UPDATES,
        handler=_tool_get_updates,
        description="Fetch Server酱³ Bot updates",
        emoji="📥",
    )
    ctx.register_tool(
        name="serverchan_bot_status",
        toolset="serverchan",
        schema=schemas.SERVERCHAN_BOT_STATUS,
        handler=_tool_status,
        description="Show Server酱³ Bot bridge status",
        emoji="📡",
    )

    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("pre_llm_call", _on_pre_llm_call)
    ctx.register_hook("post_llm_call", _on_post_llm_call)
    ctx.register_hook("on_session_end", _on_session_end)

    ctx.register_cli_command(
        name="serverchan-bot",
        help="Manage the Server酱³ Bot Hermes bridge",
        setup_fn=_setup_cli,
        handler_fn=_cli_handler,
        description="Poll inbound Server酱³ Bot messages into Hermes CLI and send replies back.",
    )
    ctx.register_command("serverchan", _slash_handler, description="Server酱³ bridge controls: status/start/stop")

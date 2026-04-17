SERVERCHAN_SEND_MESSAGE = {
    "name": "serverchan_send_message",
    "description": "Send a message to a Server酱³ Bot chat. Use when the user wants Hermes to proactively push a message to Server酱³.",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Message text to send."},
            "chat_id": {"type": "string", "description": "Target chat ID. Optional if a default chat is configured or a recent inbound chat exists."},
            "parse_mode": {"type": "string", "enum": ["text", "markdown"], "description": "Formatting mode."},
            "silent": {"type": "boolean", "description": "Whether to send silently."}
        },
        "required": ["text"]
    }
}

SERVERCHAN_GET_UPDATES = {
    "name": "serverchan_get_updates",
    "description": "Fetch recent inbound updates from the Server酱³ Bot API for diagnostics.",
    "parameters": {
        "type": "object",
        "properties": {
            "offset": {"type": "integer", "description": "Optional update offset."},
            "timeout": {"type": "integer", "description": "Long-poll timeout in seconds."}
        }
    }
}

SERVERCHAN_BOT_STATUS = {
    "name": "serverchan_bot_status",
    "description": "Return the current Server酱³ bridge status, including polling state, last active chat, and configured defaults.",
    "parameters": {"type": "object", "properties": {}}
}

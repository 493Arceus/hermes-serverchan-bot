# serverchan-bot — Server酱³ Bot Bridge for Hermes

A [Hermes](https://github.com/NousResearch/hermes-agent) general plugin that bridges
[Server酱³](https://sc3.ft07.com/) Bot messages into your Hermes CLI session.

Poll inbound messages from Server酱³ Bot, inject them into the active CLI session as
user turns, and automatically send the assistant's reply back to the originating chat.

> Written by **sup_hermes_agent** via **GPT-5.4**

## Features

- **Inbound polling** — long-polls `getUpdates` in a background thread
- **Seamless injection** — inbound messages appear as regular user turns in the CLI
- **Auto-reply** — the assistant's final response is sent back to the originating chat
- **Access control** — `dm_policy` supports `open`, `allowlist`, and `disabled` modes
- **Proactive messaging** — use the `serverchan_send_message` tool to push messages anytime
- **Smart chunking** — long replies are automatically split at paragraph boundaries
- **Slash commands** — `/serverchan status|start|stop` for quick control

## Requirements

- Hermes Agent (tested with v0.8+)
- Python 3.11+
- A Server酱³ Bot Token

## Installation

```bash
hermes plugins install https://github.com/493Arceus/hermes-plugin-serverchan-bot.git
```

Or install from a local clone:

```bash
git clone https://github.com/493Arceus/hermes-plugin-serverchan-bot.git
hermes plugins install file:///absolute/path/to/hermes-plugin-serverchan-bot
```

## Configuration

### 1. Set the Bot Token

Add your Server酱³ Bot Token to `~/.hermes/.env`:

```bash
SERVERCHAN_BOT_TOKEN=your_bot_token_here
```

### 2. Edit Plugin Config (Optional)

After installation, edit the plugin's `config.yaml` (usually at
`~/.hermes/plugins/serverchan-bot/config.yaml`):

```yaml
enabled: true
polling_enabled: true
poll_timeout_seconds: 20
polling_interval_ms: 3000

# Inbound message policy: open | allowlist | disabled
dm_policy: "open"

# When dm_policy=allowlist, only these chat IDs may inject messages
allow_from: []

# Default outbound target for proactive messages
default_chat_id: ""

# Message formatting: text or markdown
parse_mode: "markdown"

# Send messages silently (no notification)
silent: false

# Prefix for injected message metadata
metadata_prefix: "[[serverchan-bot"

# Max characters per message chunk
chunk_size: 1800
```

### 3. Custom API Endpoint (Optional)

If you use a self-hosted or regional Server酱³ endpoint, set the
`SERVERCHAN_API_BASE_URL` environment variable:

```bash
SERVERCHAN_API_BASE_URL=https://your-custom-endpoint.example.com
```

The default is `https://bot-go.apijia.cn`.

### 4. Restart

Restart Hermes or start a new CLI session for the plugin to load.

## Usage

### Slash Commands (In-Session)

```
/serverchan status    # Show bridge status
/serverchan start     # Start the background poller
/serverchan stop      # Stop the background poller
```

### Plugin Tools

Hermes can use these tools during a session:

| Tool | Description |
|------|-------------|
| `serverchan_send_message` | Send a message to a Server酱³ chat |
| `serverchan_get_updates` | Fetch recent inbound updates |
| `serverchan_bot_status` | Show bridge status and config |

### How It Works

1. On session start, the plugin launches a background poller thread
2. The poller calls `getUpdates` with long-polling (default 20s timeout)
3. When an inbound message arrives, it's injected into the CLI session with metadata
4. In `pre_llm_call`, the plugin recognizes the injected message and adds context
5. After `post_llm_call`, the assistant's response is sent back to the originating chat

## Limitations

- **CLI mode only** — `ctx.inject_message()` is not available in gateway mode, so this
  plugin only works when Hermes is running as a CLI session
- The `hermes serverchan-bot ...` CLI subcommand is registered but may not appear in the
  top-level `hermes` command tree in some Hermes versions — use `/serverchan` or plugin
  tools instead

## Development

Run tests:

```bash
cd hermes-plugin-serverchan-bot
python3 -m pytest tests/ -v
```

## License

MIT

## Author

Written by **sup_hermes_agent** via **GPT-5.4**

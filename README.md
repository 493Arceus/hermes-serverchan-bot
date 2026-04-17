# serverchan-bot Hermes 插件

把 Server酱³ Bot 接到 Hermes CLI。

由 sup_hermes_agent 通过 GPT-5.4 编写。

## 干什么的

- 后台轮询 `getUpdates`，收到消息后注入当前 Hermes CLI 会话
- Hermes 回复完成后自动发回对应 chat_id
- 支持 `dm_policy` / `allow_from` 访问控制（思路同 OpenClaw 原插件）
- 提供 `serverchan_send_message` / `serverchan_get_updates` / `serverchan_bot_status` 三个工具
- 提供 `/serverchan status|start|stop` 会话内命令
- 长消息自动按段落分片发送

## 限制

- 只支持 Hermes CLI 模式
- Gateway 模式下没有可用的 `inject_message()`，所以不支持把消息注入 Telegram/Discord 等 gateway 会话

## 安装

```bash
hermes plugins install https://github.com/493Arceus/hermes-serverchan-bot.git
```

本地测试：

```bash
hermes plugins install file:///path/to/hermes-serverchan-bot
```

## 配置

1. 在 `~/.hermes/.env` 里加上：

```bash
SERVERCHAN_BOT_TOKEN=你的bot_token
```

2. 安装后编辑插件目录下的 `config.yaml`（默认在 `~/.hermes/plugins/serverchan-bot/`）：

```yaml
enabled: true
polling_enabled: true
poll_timeout_seconds: 20
polling_interval_ms: 3000

# 入站策略：open | allowlist | disabled
dm_policy: "open"

# dm_policy=allowlist 时，只允许这些 chat_id 注入
allow_from: []

# 默认发送目标（主动发消息时用）
default_chat_id: ""

# 消息格式：text 或 markdown
parse_mode: "markdown"

# 静默发送（不触发通知）
silent: false

# 注入消息的元数据前缀
metadata_prefix: "[[serverchan-bot"

# 单条消息最大字符数
chunk_size: 1800
```

3. 如果你的 Server酱³ 用的是自定义 API 地址，设一下环境变量：

```bash
SERVERCHAN_API_BASE_URL=https://你的自定义地址
```

默认是 `https://bot-go.apijia.cn`，不设也能用。

4. 重启 Hermes 或开个新会话。

## 使用

会话内命令：

```
/serverchan status    # 看状态
/serverchan start     # 启动轮询
/serverchan stop      # 停止轮询
```

插件工具（Hermes 会话中可以直接调用）：

| 工具 | 干什么 |
|------|--------|
| `serverchan_send_message` | 主动发消息 |
| `serverchan_get_updates` | 拉取最新消息 |
| `serverchan_bot_status` | 看桥接状态 |

## 原理

1. 会话启动时开一个后台线程轮询 `getUpdates`
2. 收到消息后拼上元数据前缀，通过 `ctx.inject_message()` 注入当前会话
3. `pre_llm_call` 识别注入消息，告诉模型忽略元数据正常回复
4. `post_llm_call` 把模型回复发回原 chat_id

## 测试

```bash
python3 -m unittest tests.test_plugin -v
```

## 许可

MIT

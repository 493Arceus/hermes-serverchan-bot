# serverchan-bot Hermes plugin

把 Server酱³ Bot 接到 Hermes CLI。

当前实现范围：
- 轮询 `getUpdates`
- 将入站消息注入当前 Hermes CLI 会话
- Hermes 生成回复后自动回发到对应 chat_id
- 提供 `serverchan_*` 工具
- 提供 `hermes serverchan-bot ...` 管理命令
- 提供 `/serverchan ...` 会话内命令

限制：
- 目前只支持 Hermes CLI 模式
- Gateway 模式下 Hermes 插件 API 没有可用的 `inject_message()` 入口，因此不支持把消息注入 Telegram/Discord 等 gateway 会话

## 安装

```bash
hermes plugins install <git-url>
```

或本地测试：

```bash
hermes plugins install file:///absolute/path/to/serverchan-hermes-plugin
```

## 配置

1. 设置环境变量 `SERVERCHAN_BOT_TOKEN`
2. 安装后编辑插件目录下的 `config.yaml`

默认安装目录通常是：

```bash
~/.hermes/plugins/serverchan-hermes-plugin/
```

## CLI 命令

```bash
hermes serverchan-bot status
hermes serverchan-bot test
hermes serverchan-bot start
hermes serverchan-bot stop
hermes serverchan-bot send --text '你好' --chat-id 123456
```

## 会话内命令

```text
/serverchan status
/serverchan start
/serverchan stop
```

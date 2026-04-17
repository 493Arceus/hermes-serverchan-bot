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

## 管理方式

当前 Hermes 版本里，这个插件已经成功注册了：
- 插件工具：`serverchan_send_message` / `serverchan_get_updates` / `serverchan_bot_status`
- 会话内命令：`/serverchan ...`

说明：插件内部也注册了 `serverchan-bot` CLI 子命令，但这台机器上的 Hermes 版本尚未把“通用插件 CLI 命令”真正挂到顶层 `hermes ...` argparse 命令树，所以 `hermes serverchan-bot ...` 现在还不能直接调用。

因此当前可用控制方式是：

```text
/serverchan status
/serverchan start
/serverchan stop
```

以及让 Hermes 在会话中调用对应插件工具。
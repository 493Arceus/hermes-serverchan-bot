# Server酱³ Bot bridge installed

下一步：

1. 确保 `.env` 里有 `SERVERCHAN_BOT_TOKEN`
2. 编辑插件目录里的 `config.yaml`
3. 重启 Hermes 或重新开一个会话
4. 打开一个 Hermes CLI 会话后，先验证：

```text
/serverchan status
/serverchan start
```

说明：
- 当前插件只支持 Hermes CLI 模式
- 收到 Server酱³ 消息后，会注入到当前 CLI 会话
- 该回合结束后，Hermes 的最终回复会自动回发到原 chat_id
- 插件内部已经注册了 `serverchan-bot` CLI 子命令，但当前这版 Hermes 还没有把通用插件 CLI 子命令接到顶层 `hermes ...` 命令树，所以先以 `/serverchan ...` 和插件工具为准

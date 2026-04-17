# Server酱³ Bot bridge installed

下一步：

1. 确保 `.env` 里有 `SERVERCHAN_BOT_TOKEN`
2. 编辑插件目录里的 `config.yaml`
3. 重启 Hermes 或重新开一个会话
4. 先验证：

```bash
hermes serverchan-bot test
hermes serverchan-bot status
```

5. CLI 会话内可以用：

```text
/serverchan status
/serverchan start
/serverchan stop
```

说明：
- 当前插件只支持 Hermes CLI 模式
- 收到 Server酱³ 消息后，会注入到当前 CLI 会话
- 该回合结束后，Hermes 的最终回复会自动回发到原 chat_id

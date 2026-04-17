# Server酱³ Bot bridge 已安装

下一步：

1. 在 `~/.hermes/.env` 里加上 `SERVERCHAN_BOT_TOKEN`
2. 编辑插件目录里的 `config.yaml` 调整参数
3. 重启 Hermes 或开个新会话
4. 验证一下：

```
/serverchan status
/serverchan start
```

说明：
- 当前只支持 CLI 模式
- 收到消息后会注入到当前会话，Hermes 回复后自动发回
- `hermes serverchan-bot ...` 子命令已注册但当前 Hermes 版本没接到顶层命令树，先用 `/serverchan` 和插件工具

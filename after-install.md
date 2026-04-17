# Server酱³ Bot bridge installed

## Post-install steps

1. **Set the bot token** in `~/.hermes/.env`:

   ```bash
   SERVERCHAN_BOT_TOKEN=your_bot_token_here
   ```

2. **(Optional)** Edit the plugin config at `~/.hermes/plugins/serverchan-bot/config.yaml`
   to adjust polling interval, DM policy, default chat ID, etc.

3. **(Optional)** Set `SERVERCHAN_API_BASE_URL` in your environment if you use a custom
   Server酱³ API endpoint.

4. **Restart Hermes** or start a new CLI session.

5. **Verify** the bridge is working:

   ```
   /serverchan status
   /serverchan start
   ```

## Notes

- This plugin only works in Hermes CLI mode (not gateway mode)
- Inbound Server酱³ messages are injected into the current CLI session
- After the assistant responds, the reply is automatically sent back to the originating chat
- Use `/serverchan status|start|stop` for quick control
- The `hermes serverchan-bot ...` CLI subcommand is registered but may not be exposed in the
  current Hermes version — prefer `/serverchan` and plugin tools

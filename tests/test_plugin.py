import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import importlib.util
import sys

PKG_DIR = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "serverchan_bot_plugin",
    PKG_DIR / "__init__.py",
    submodule_search_locations=[str(PKG_DIR)],
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)


class PluginTests(unittest.TestCase):
    def test_chunk_text_prefers_whole_text_when_short(self):
        self.assertEqual(mod._chunk_text("hello", 100), ["hello"])

    def test_chunk_text_splits_long_text(self):
        parts = mod._chunk_text("a" * 50 + "\n\n" + "b" * 50, 60)
        self.assertGreaterEqual(len(parts), 2)
        self.assertTrue(all(parts))

    def test_parse_update_extracts_text_chat_and_ids(self):
        update = {
            "update_id": 123,
            "message": {
                "message_id": 456,
                "chat_id": 789,
                "text": "你好",
                "from": {"id": 1, "is_bot": False},
            },
        }
        inbound = mod._parse_update(update)
        self.assertIsNotNone(inbound)
        self.assertEqual(inbound.chat_id, "789")
        self.assertIn("你好", inbound.injected_message)

    def test_status_tool_returns_json(self):
        payload = json.loads(mod._tool_status({}))
        self.assertTrue(payload["ok"])

    def test_state_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "state.json"
            with patch.object(mod, "_STATE_PATH", path):
                mod._save_state({"last_update_id": 42})
                self.assertEqual(mod._load_state()["last_update_id"], 42)


if __name__ == "__main__":
    unittest.main()

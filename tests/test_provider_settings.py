import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.video_settings import VideoSettings, ProviderRouter
from backend.providers.mock import MockVideoProvider
from backend.models import GenerationInput
from backend.store import AppStore
from fastapi.testclient import TestClient
import backend.main as main


class SettingsTests(unittest.TestCase):
    def test_config_http_guard_and_redaction(self):
        with tempfile.TemporaryDirectory() as folder:
            config = VideoSettings(Path(folder) / "providers.json")
            router = ProviderRouter(MockVideoProvider(), config)
            with patch.object(main, "video_settings", config), patch.object(main, "provider", router), patch.object(main, "store", AppStore(str(Path(folder) / "db.sqlite"))):
                client = TestClient(main.app)
                self.assertEqual(client.put("/api/video-providers/runway", json={"apiKey": "secret"}, headers={"origin": "https://evil.test"}).status_code, 403)
                self.assertEqual(client.put("/api/video-providers/runway", json={"apiKey": "secret", "baseUrl": "https://evil.test"}).status_code, 422)
                self.assertEqual(client.post("/api/video-providers/runway/activate").status_code, 409)
                self.assertEqual(client.put("/api/video-providers/runway", json={"apiKey": "x" * 5000}).status_code, 422)
                if os.name == "nt":
                    result = client.put("/api/video-providers/runway", json={"apiKey": "secret-value"})
                    self.assertEqual(result.status_code, 200)
                    self.assertNotIn("secret-value", result.text)
                    self.assertEqual(client.post("/api/video-providers/runway/activate").status_code, 200)
                    self.assertEqual(client.get("/api/video-providers").json()["activeProvider"], "runway")
                    self.assertEqual(client.delete("/api/video-providers/runway").status_code, 409)
                    with patch("backend.providers.platforms.PlatformVideoProvider._request_json", return_value={}) as request:
                        self.assertTrue(client.post("/api/video-providers/runway/test").json()["ok"])
                        self.assertEqual(request.call_args.args, ("GET", "/organization"))

    @unittest.skipUnless(os.name == "nt", "Windows DPAPI")
    def test_secure_save_redaction_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "providers.json"
            config = VideoSettings(path)
            config.set_key("runway", "highly-secret-test-value")
            self.assertNotIn("highly-secret", path.read_text())
            self.assertEqual(VideoSettings(path).key("runway"), "highly-secret-test-value")
            self.assertNotIn("highly-secret", str(config.listing("mock")))

    def test_routing_survives_activation_and_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            config = VideoSettings(Path(folder) / "providers.json")
            with patch.object(config, "key", return_value="test-key"):
                router = ProviderRouter(MockVideoProvider(), config)
                config.data["activeProvider"] = "runway"
                original = router.instance("runway")
                with patch.object(original, "_request_json", return_value={"id": "remote"}):
                    task = router.create_task(GenerationInput(prompt="sunny ocean"), "one")
                config.data["activeProvider"] = "luma"
                restarted = ProviderRouter(MockVideoProvider(), config)
                restarted.restore_task(task)
                with patch.object(restarted.instance("runway"), "_request_json", return_value={"status": "SUCCEEDED", "output": ["https://example.com/result.mp4"]}):
                    self.assertEqual(restarted.get_task(task.id).resultUrl, "https://example.com/result.mp4")

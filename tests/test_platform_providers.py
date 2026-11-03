import unittest
from unittest.mock import patch

from backend.models import GenerationInput, TaskStatus
from backend.providers.platforms import PlatformVideoProvider, validate_input
from backend.providers.volcengine import ProviderApiError


class PlatformTests(unittest.TestCase):
    def test_payloads_and_polling(self):
        for identity in ("wan", "runway", "luma"):
            with self.subTest(provider=identity):
                adapter = PlatformVideoProvider(identity, "test-key")
                value = GenerationInput(prompt="a sunny ocean", ratio="16:9", generateAudio=identity == "wan")
                reply = {"output": {"task_id": "remote"}} if identity == "wan" else {"id": "remote"}
                with patch.object(adapter, "_request_json", return_value=reply) as request:
                    task = adapter.create_task(value, "idempotent")
                    method, path, payload = request.call_args.args
                    self.assertEqual(method, "POST")
                    self.assertEqual(task.provider, identity)
                    if identity == "wan":
                        self.assertEqual(payload["parameters"], {"size": "1280*720", "duration": 5})
                    elif identity == "runway":
                        self.assertEqual(payload, {"model": "gen4.5", "promptText": value.prompt, "ratio": "1280:720", "duration": 5})
                    else:
                        self.assertEqual(payload, {"model": "ray-flash-2", "prompt": value.prompt, "aspect_ratio": "16:9", "resolution": "720p", "duration": "5s"})
                response = {"output": {"task_status": "SUCCEEDED", "video_url": "https://example.com/v.mp4"}} if identity == "wan" else ({"status": "SUCCEEDED", "output": ["https://example.com/v.mp4"]} if identity == "runway" else {"state": "completed", "assets": {"video": "https://example.com/v.mp4"}})
                with patch.object(adapter, "_request_json", return_value=response):
                    self.assertEqual(adapter.get_task(task.id).status, TaskStatus.SUCCEEDED)

    def test_reject_unsupported_before_request(self):
        for identity, fields in (("runway", {"ratio": "1:1"}), ("runway", {"generateAudio": True}), ("luma", {"duration": 10}), ("wan", {"resolution": "480p"})):
            with self.subTest(identity=identity, fields=fields), self.assertRaises(ProviderApiError):
                validate_input(identity, GenerationInput(prompt="sunny ocean", **fields))

    def test_no_fake_cancel(self):
        adapter = PlatformVideoProvider("wan", "key")
        with patch.object(adapter, "_request_json", return_value={"output": {"task_id": "remote"}}):
            task = adapter.create_task(GenerationInput(prompt="sunny ocean", generateAudio=True), "a")
        with self.assertRaises(ProviderApiError) as error:
            adapter.cancel_task(task.id)
        self.assertEqual(error.exception.status_code, 409)

    def test_terminal_states_are_monotonic(self):
        adapter = PlatformVideoProvider("runway", "key")
        with patch.object(adapter, "_request_json", return_value={"id": "remote"}):
            task = adapter.create_task(GenerationInput(prompt="sunny ocean"), "terminal")
        for state in (TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            with self.subTest(state=state):
                terminal = task.model_copy(update={"status": state})
                adapter.restore_task(terminal)
                with patch.object(adapter, "_request_json") as request:
                    self.assertEqual(adapter.get_task(task.id).status, state)
                    self.assertEqual(adapter.cancel_task(task.id).status, state)
                    request.assert_not_called()

    def test_cancelled_task_is_not_polled_again(self):
        adapter = PlatformVideoProvider("runway", "key")
        with patch.object(adapter, "_request_json", return_value={"id": "remote"}):
            task = adapter.create_task(GenerationInput(prompt="sunny ocean"), "cancel")
        with patch.object(adapter, "_request_json", return_value={}) as request:
            self.assertEqual(adapter.cancel_task(task.id).status, TaskStatus.CANCELLED)
            request.assert_called_once_with("DELETE", "/tasks/remote")
        with patch.object(adapter, "_request_json") as request:
            self.assertEqual(adapter.get_task(task.id).status, TaskStatus.CANCELLED)
            request.assert_not_called()

from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.config import Settings
from backend.models import GenerationInput, TaskStatus
from backend.provider_registry import create_provider
from backend.providers.mock import MockVideoProvider
from backend.providers.volcengine import VolcengineConfig, VolcengineVideoProvider


class VolcengineProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = VolcengineVideoProvider(
            VolcengineConfig(
                api_key="test-key",
                model_id="doubao-seedance-2-0-260128",
                fast_model_id="doubao-seedance-2-0-fast-260128",
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                watermark=True,
            )
        )

    def test_auto_registry_uses_mock_without_key(self) -> None:
        provider = create_provider(Settings(video_provider="auto", ark_api_key=None))
        self.assertIsInstance(provider, MockVideoProvider)

    def test_auto_registry_uses_volcengine_with_key(self) -> None:
        provider = create_provider(Settings(video_provider="auto", ark_api_key="key"))
        self.assertIsInstance(provider, VolcengineVideoProvider)

    def test_create_and_query_task_contract(self) -> None:
        generation_input = GenerationInput(
            prompt="雨后的江南庭院，一只白瓷香水瓶放在青石台上",
            ratio="9:16",
            duration=8,
            quality="standard",
        )
        with patch.object(self.provider, "_request_json", return_value={"id": "cgt-test-001"}) as request:
            task = self.provider.create_task(generation_input, "idempotency-key")
        self.assertEqual(task.id, "cgt-test-001")
        create_payload = request.call_args.args[2]
        self.assertEqual(create_payload["model"], "doubao-seedance-2-0-260128")
        self.assertEqual(create_payload["duration"], 8)
        self.assertEqual(create_payload["resolution"], "720p")
        self.assertFalse(create_payload["generate_audio"])
        self.assertTrue(create_payload["watermark"])

        with patch.object(
            self.provider,
            "_request_json",
            return_value={
                "id": "cgt-test-001",
                "status": "succeeded",
                "content": {"video_url": "https://example.com/result.mp4"},
            },
        ):
            completed = self.provider.get_task(task.id)
        self.assertIsNotNone(completed)
        self.assertEqual(completed.status, TaskStatus.SUCCEEDED)
        self.assertEqual(completed.resultUrl, "https://example.com/result.mp4")

    def test_fast_model_is_used_for_cost_saving_resolutions(self) -> None:
        generation_input = GenerationInput(
            prompt="低成本商品视频预览",
            quality="fast",
            resolution="480p",
            generateAudio=False,
        )
        with patch.object(self.provider, "_request_json", return_value={"id": "cgt-fast"}) as request:
            self.provider.create_task(generation_input, "fast-key")
        payload = request.call_args.args[2]
        self.assertEqual(payload["model"], "doubao-seedance-2-0-fast-260128")
        self.assertEqual(payload["resolution"], "480p")

    def test_1080p_uses_standard_model_even_if_fast_requested(self) -> None:
        generation_input = GenerationInput(
            prompt="高清商品广告视频",
            quality="fast",
            resolution="1080p",
        )
        with patch.object(self.provider, "_request_json", return_value={"id": "cgt-hd"}) as request:
            self.provider.create_task(generation_input, "hd-key")
        self.assertEqual(request.call_args.args[2]["model"], "doubao-seedance-2-0-260128")

    def test_failed_task_exposes_actionable_limit_message(self) -> None:
        generation_input = GenerationInput(prompt="一只橘猫驾驶飞船穿越星云")
        with patch.object(self.provider, "_request_json", return_value={"id": "cgt-limit"}):
            task = self.provider.create_task(generation_input, "limit-key")

        with patch.object(
            self.provider,
            "_request_json",
            return_value={
                "id": "cgt-limit",
                "status": "failed",
                "error": {
                    "code": "SetLimitExceeded",
                    "message": "account inference limit reached",
                },
            },
        ):
            failed = self.provider.get_task(task.id)

        self.assertIsNotNone(failed)
        self.assertEqual(failed.status, TaskStatus.FAILED)
        self.assertEqual(failed.errorCode, "SetLimitExceeded")
        self.assertIn("安心体验模式", failed.errorMessage)
        self.assertEqual(failed.actionUrl, self.provider.MODEL_MANAGEMENT_URL)


if __name__ == "__main__":
    unittest.main()

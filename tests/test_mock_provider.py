from __future__ import annotations

import unittest

from backend.models import GenerationInput, TaskStatus, VideoTask
from backend.providers.mock import MockVideoProvider, current_task_state


class MockVideoProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = MockVideoProvider()

    def test_estimate_returns_predictable_credits(self) -> None:
        self.assertEqual(self.provider.estimate(GenerationInput(prompt="测试画面", duration=8, quality="standard")).credits, 8)
        self.assertEqual(self.provider.estimate(GenerationInput(prompt="测试画面", duration=8, quality="fast")).credits, 6)
        self.assertEqual(self.provider.estimate(GenerationInput(prompt="测试画面", duration=8, quality="pro")).credits, 14)

    def test_create_task_is_idempotent(self) -> None:
        generation_input = GenerationInput(prompt="雨后的江南庭院")
        first = self.provider.create_task(generation_input, "same-key")
        second = self.provider.create_task(generation_input, "same-key")
        self.assertEqual(first.id, second.id)

    def test_task_state_advances_to_succeeded(self) -> None:
        task = VideoTask(
            id="gen_demo",
            externalTaskId="mock_demo",
            idempotencyKey="demo-key",
            createdAt=1_000,
            status=TaskStatus.QUEUED,
            progress=4,
            stage="任务已进入队列",
            input=GenerationInput(prompt="雨后的江南庭院"),
        )
        self.assertEqual(current_task_state(task, 1_500).status, TaskStatus.QUEUED)
        self.assertEqual(current_task_state(task, 3_500).status, TaskStatus.GENERATING)
        self.assertEqual(current_task_state(task, 7_000).status, TaskStatus.POST_PROCESSING)
        self.assertEqual(current_task_state(task, 9_000).status, TaskStatus.SUCCEEDED)

    def test_cancelled_task_remains_cancelled(self) -> None:
        generation_input = GenerationInput(prompt="雨后的江南庭院")
        task = self.provider.create_task(generation_input, "cancel-key")
        cancelled = self.provider.cancel_task(task.id)
        self.assertIsNotNone(cancelled)
        self.assertEqual(current_task_state(cancelled, task.createdAt + 50_000).status, TaskStatus.CANCELLED)


if __name__ == "__main__":
    unittest.main()

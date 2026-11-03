from __future__ import annotations

import unittest
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.main as main_module
from backend.providers.mock import MockVideoProvider
from backend.store import AppStore


class ApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = TemporaryDirectory()
        cls.original_provider = main_module.provider
        cls.original_store = main_module.store
        main_module.provider = MockVideoProvider()
        main_module.store = AppStore(f"{cls.temp_dir.name}/test.db")
        cls.client = TestClient(main_module.app)

    @classmethod
    def tearDownClass(cls) -> None:
        main_module.provider = cls.original_provider
        main_module.store = cls.original_store
        cls.temp_dir.cleanup()

    def test_frontend_and_health_are_served_by_python(self) -> None:
        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["runtime"], "python")

        frontend = self.client.get("/")
        self.assertEqual(frontend.status_code, 200)
        self.assertIn("FrameFlow", frontend.text)

    def test_estimate_contract_matches_frontend(self) -> None:
        response = self.client.post(
            "/api/generations/estimate",
            json={"prompt": "晨雾里的香水广告", "duration": 10, "quality": "pro"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["credits"], 17)
        self.assertIn("estimatedSeconds", response.json())

    def test_create_generation_requires_idempotency_key(self) -> None:
        response = self.client.post(
            "/api/generations",
            json={"prompt": "清晨的海边公路"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "INVALID_IDEMPOTENCY_KEY")

    def test_create_generation_is_idempotent(self) -> None:
        key = f"api-test-{uuid.uuid4()}"
        request = {"prompt": "清晨的海边公路", "ratio": "16:9", "duration": 8}
        first = self.client.post(
            "/api/generations",
            json=request,
            headers={"Idempotency-Key": key},
        )
        second = self.client.post(
            "/api/generations",
            json=request,
            headers={"Idempotency-Key": key},
        )
        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.status_code, 202)
        self.assertEqual(first.json()["task"]["id"], second.json()["task"]["id"])

    def test_usage_billing_and_works_are_backend_backed(self) -> None:
        main_module.store.change_plan("starter")
        usage = self.client.get("/api/account/usage")
        self.assertEqual(usage.status_code, 200)
        self.assertEqual(usage.json()["monthlyLimit"], 160)
        self.assertIn("availableCredits", usage.json())

        billing = self.client.get("/api/billing")
        self.assertEqual(billing.status_code, 200)
        self.assertEqual(len(billing.json()["plans"]), 3)

        works = self.client.get("/api/works")
        self.assertEqual(works.status_code, 200)
        self.assertEqual(works.json()["works"], [])

    def test_plan_can_be_changed(self) -> None:
        response = self.client.post("/api/billing/plan", json={"planId": "creator"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["plan"]["id"], "creator")
        self.assertEqual(response.json()["monthlyLimit"], 600)
        self.assertTrue(response.json()["events"])


class FrontendHostingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.frontend = self.root / "dist"
        self.frontend.mkdir()
        (self.frontend / "index.html").write_text("<html>SPA shell</html>", encoding="utf-8")
        (self.frontend / "assets").mkdir()
        (self.frontend / "assets" / "app.js").write_text("console.log('asset')", encoding="utf-8")
        (self.root / "secret.txt").write_text("private content", encoding="utf-8")
        app = FastAPI()
        app.add_exception_handler(main_module.StarletteHTTPException, main_module.http_error_handler)
        app.mount("/", main_module.SPAStaticFiles(directory=self.frontend))
        self.client = TestClient(app)

    def test_shell_and_nested_routes(self) -> None:
        for route in ("/", "/workspace/generations", "/billing/", "/assets", "/assets/"):
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200)
            self.assertIn("SPA shell", response.text)

    def test_assets_and_missing_resources(self) -> None:
        self.assertIn("console.log", self.client.get("/assets/app.js").text)
        for route in ("/assets/missing.js", "/favicon.ico", "/assets/missing", "/static/missing"):
            self.assertEqual(self.client.get(route).status_code, 404)
        for route in ("/api", "/api/unknown", "/api/unknown/nested"):
            response = self.client.get(route)
            self.assertEqual(response.status_code, 404)
            self.assertIn("error", response.json())

    def test_traversal_does_not_expose_files(self) -> None:
        for route in ("/%2e%2e/secret.txt", "/..%5csecret.txt", "/assets/%2e%2e/%2e%2e/secret.txt"):
            response = self.client.get(route)
            self.assertEqual(response.status_code, 404)
            self.assertNotIn("private content", response.text)

    def test_frontend_selection(self) -> None:
        legacy = self.root / "public"
        build = self.root / "frontend" / "apps" / "web-antd" / "dist"
        with patch.object(main_module, "PUBLIC_DIR", legacy), patch.dict("os.environ", {}, clear=True):
            self.assertEqual(main_module.select_frontend_dir(), legacy)
            build.mkdir(parents=True)
            (build / "index.html").write_text("built app", encoding="utf-8")
            self.assertEqual(main_module.select_frontend_dir(), build)
            with patch.dict("os.environ", {"FRAMEFLOW_FRONTEND_DIR": str(self.frontend)}):
                self.assertEqual(main_module.select_frontend_dir(), self.frontend.resolve())

    def test_csp_allows_dynamic_styles_but_keeps_scripts_restricted(self) -> None:
        response = TestClient(main_module.app).get("/api/health")
        policy = response.headers["Content-Security-Policy"]
        self.assertIn("style-src 'self' 'unsafe-inline';", policy)
        self.assertIn("script-src 'self';", policy)


if __name__ == "__main__":
    unittest.main()

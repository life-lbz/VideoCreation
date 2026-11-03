"""Local single-user settings encrypted with Windows user-bound DPAPI."""
from __future__ import annotations

import base64
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import threading

from backend.config import settings
from backend.providers.platforms import SPECS, capabilities, PlatformVideoProvider, validate_input
from backend.providers.volcengine import VolcengineConfig, VolcengineVideoProvider, ProviderApiError, ProviderNotConfiguredError


def protect(data: bytes, decrypt=False) -> bytes:
    if os.name != "nt":
        raise RuntimeError("密钥安全存储需要 Windows DPAPI")
    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output = Blob()
    function = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output)):
        raise RuntimeError("Windows 密钥安全存储失败")
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        ctypes.windll.kernel32.LocalFree(output.data)


class VideoSettings:
    def __init__(self, path=None):
        self.path = Path(path or os.getenv("VIDEO_SETTINGS_PATH") or Path(settings.database_path).parent / "video-providers.json")
        self.lock = threading.RLock()
        self.data = json.loads(self.path.read_text("utf-8")) if self.path.exists() else {"activeProvider": None, "keys": {}}

    def key(self, identity):
        value = self.data["keys"].get(identity)
        return protect(base64.b64decode(value), True).decode() if value else (settings.ark_api_key if identity == "volcengine" else None)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data), "utf-8")
        os.replace(temporary, self.path)

    def set_key(self, identity, key):
        with self.lock:
            self.data["keys"][identity] = base64.b64encode(protect(key.encode())).decode()
            self.save()

    def listing(self, fallback):
        entries = []
        for identity, spec in SPECS.items():
            key = self.key(identity)
            entries.append({"id": identity, "name": spec["name"], "baseUrl": spec["baseUrl"], "models": spec["models"], "configured": bool(key), "keyHint": "已安全保存" if key else "", "capabilities": capabilities(identity), "note": spec["note"]})
        return {"activeProvider": self.data.get("activeProvider") or fallback, "providers": entries}


class ProviderRouter:
    def __init__(self, fallback, config):
        self.fallback = fallback
        self.config = config
        self.instances = {}
        self.tasks = {}

    def active_id(self):
        return self.config.data.get("activeProvider") or ("mock" if self.fallback.get_capabilities().get("provider") == "mock" else "volcengine")

    def instance(self, identity):
        if identity == "mock":
            return self.fallback
        if identity not in self.instances:
            key = self.config.key(identity)
            if identity == "volcengine":
                instance = VolcengineVideoProvider(VolcengineConfig(key, settings.ark_model_id, settings.ark_fast_model_id, SPECS[identity]["baseUrl"], settings.ark_watermark))
            else:
                instance = PlatformVideoProvider(identity, key)
            self.instances[identity] = instance
        return self.instances[identity]

    def get_capabilities(self):
        identity = self.active_id()
        return self.fallback.get_capabilities() if identity == "mock" else {"provider": identity, **capabilities(identity)}

    def estimate(self, value):
        identity = self.active_id()
        if identity != "mock":
            validate_input(identity, value)
        return self.instance(identity).estimate(value)

    def create_task(self, value, key):
        identity = self.active_id()
        if identity != "mock":
            validate_input(identity, value)
        task = self.instance(identity).create_task(value, key)
        task.provider = identity
        self.tasks[task.id] = identity
        return task

    def restore_task(self, task):
        # Legacy mock task IDs use the mock- prefix.
        identity = "mock" if task.id.startswith(("mock-", "gen_")) else task.provider
        self.tasks[task.id] = identity
        self.instance(identity).restore_task(task)

    def get_task(self, task_id):
        identity = self.tasks.get(task_id)
        return self.instance(identity).get_task(task_id) if identity else None

    def cancel_task(self, task_id):
        identity = self.tasks.get(task_id)
        return self.instance(identity).cancel_task(task_id) if identity else None

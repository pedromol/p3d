import time
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.services.model_service import ModelService, DEFAULT_IDLE_TIMEOUT_SECONDS


def test_idle_timeout_default_config():
    service = ModelService(start_workers=False)
    assert service.idle_timeout_seconds == DEFAULT_IDLE_TIMEOUT_SECONDS
    assert service.is_model_loaded is False


def test_idle_timeout_custom_config(monkeypatch):
    monkeypatch.setenv("IMAGE3D_IDLE_TIMEOUT_SECONDS", "60")
    service = ModelService(start_workers=False)
    assert service.idle_timeout_seconds == 60

    service_override = ModelService(idle_timeout_seconds=120, start_workers=False)
    assert service_override.idle_timeout_seconds == 120


def test_unload_clears_model_and_flags():
    service = ModelService(start_workers=False)
    service._model = "fake-model"
    assert service.is_model_loaded is True

    service.unload()
    assert service._model is None
    assert service.is_model_loaded is False


def test_idle_watchdog_unloads_after_timeout():
    # Set a tiny idle timeout of 0.2 seconds and start watchdog
    service = ModelService(
        worker_count=1,
        idle_timeout_seconds=0.2,
        start_workers=True,
    )
    try:
        service._model = "mock-triposr-model"
        assert service.is_model_loaded is True
        service._last_active_time = time.monotonic() - 1.0  # simulate past activity

        # Wait for watchdog to trigger
        time.sleep(0.5)

        assert service.is_model_loaded is False
    finally:
        service.stop()


def test_immediate_unload_when_idle_timeout_zero():
    service = ModelService(
        worker_count=1,
        idle_timeout_seconds=0,
        start_workers=False,
    )
    service._model = "mock-model"
    assert service._is_idle() is True
    # Calling unload directly works cleanly
    service.unload()
    assert service.is_model_loaded is False


def test_api_device_and_unload_endpoints():
    client = TestClient(app)
    resp = client.get("/api/device")
    assert resp.status_code == 200
    data = resp.json()
    assert "device" in data
    assert "model_loaded" in data
    assert "idle_timeout_seconds" in data

    unload_resp = client.post("/api/unload")
    assert unload_resp.status_code == 200
    assert unload_resp.json()["status"] == "ok"

    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["model_loaded"] is False

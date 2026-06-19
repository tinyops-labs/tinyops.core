import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from parser.blueprint_validator import BlueprintValidationError
from rest.routes.blueprint import create_blueprint_router
from rest.routes.container import create_container_router
from rest.routes.dashboard import create_dashboard_router
from rest.routes.domain import create_domain_router
from rest.routes.pipeline import create_pipeline_router
from rest.routes.settings import create_settings_router
from rest.routes.system import create_system_router
from utils.utils import Utils


@pytest.fixture
def mock_model():
    m = MagicMock()
    m.api_service.get_blueprint.return_value = {"applications": []}
    m.api_service.get_current_state.return_value = {"atoms": []}
    m.api_service.get_container_logs_by_id.return_value = ["log"]
    m.api_service.get_ssh_public_key.return_value = "ssh-pub"
    m.api_service.update_blueprint.return_value = True
    return m


@pytest.fixture
def client(mock_model):
    app = FastAPI()
    app.include_router(create_blueprint_router(mock_model), prefix="/blueprint")
    app.include_router(create_container_router(mock_model), prefix="/container")
    app.include_router(create_dashboard_router(mock_model), prefix="/dashboard")
    app.include_router(create_system_router(mock_model), prefix="/system")
    app.include_router(create_domain_router(), prefix="/domain")
    app.include_router(create_pipeline_router(), prefix="/pipeline")
    app.include_router(create_settings_router(mock_model), prefix="/settings")
    return TestClient(app)


def test_blueprint_get(client, mock_model):
    r = client.get("/blueprint")
    assert r.status_code == 200
    mock_model.api_service.get_blueprint.assert_called_once()


def test_blueprint_post_ok(client, mock_model):
    r = client.post("/blueprint", json={"applications": [{"name": "a", "image": "i"}]})
    assert r.status_code == 200
    mock_model.api_service.update_blueprint.assert_called_once()


def test_blueprint_post_validation_error(client, mock_model):
    mock_model.api_service.update_blueprint.side_effect = BlueprintValidationError(
        ["applications must be a list."]
    )
    r = client.post("/blueprint", json={})
    assert r.status_code == 400
    assert "errors" in r.json()["detail"]


def test_dashboard_get(client, mock_model):
    r = client.get("/dashboard")
    assert r.status_code == 200
    mock_model.api_service.get_current_state.assert_called_once()


def test_container_logs(client, mock_model):
    r = client.get("/container/logs/abc")
    assert r.status_code == 200
    mock_model.api_service.get_container_logs_by_id.assert_called_once_with("abc")


@patch("rest.routes.system.get_log_file_path")
def test_system_logs_missing_file(mock_path, client):
    mock_path.return_value.exists.return_value = False
    r = client.get("/system/logs")
    assert r.status_code == 200
    assert r.json() == []


def test_system_public_key(client, mock_model):
    r = client.get("/system/public-key")
    assert r.status_code == 200
    mock_model.api_service.get_ssh_public_key.assert_called_once()


def test_system_version(client):
    repo = Path(__file__).resolve().parents[2]
    prev = os.getcwd()
    try:
        os.chdir(repo / "src")
        expected = Utils.get_version()
        r = client.get("/system/version")
    finally:
        os.chdir(prev)
    assert r.status_code == 200
    assert r.json() == {"version": expected}


@patch("rest.routes.domain.Atom.get_domains", return_value=[{"name": "a", "domain": "d", "ssl": True}])
@patch("rest.routes.domain.db")
def test_domain_get(mock_db, _mock_get_domains, client):
    mock_db.get.return_value = None
    r = client.get("/domain")
    assert r.status_code == 200
    rows = r.json()
    assert rows[0]["domain"] == "d"


@patch("rest.routes.domain.db")
def test_domain_reset_ssl(mock_db, client):
    r = client.post("/domain/x.example/reset-ssl-failed")
    assert r.status_code == 200
    mock_db.set.assert_called_with("x.example", "ssl_creation_failed", False)


@patch("rest.routes.pipeline.db")
def test_pipeline_get(mock_db, client):
    mock_db.get_list.return_value = [{"id": "1"}]
    r = client.get("/pipeline")
    assert r.status_code == 200
    assert r.json() == [{"id": "1"}]


@patch("rest.routes.settings.db")
def test_settings_get(mock_db, client, mock_model):
    mock_db.internal_snapshot.return_value = {"k": "v"}
    r = client.get("/settings")
    assert r.status_code == 200
    body = r.json()
    assert body["ssh_public_key"] == "ssh-pub"
    assert body["database"] == {"k": "v"}

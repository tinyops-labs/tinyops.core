from unittest.mock import MagicMock, patch

from modules.pipeline import Pipeline


def test_get_pipelines_ready_to_run():
    p = Pipeline()
    p.pipelines = [
        {"id": "1", "status": "pending"},
        {"id": "2", "status": "success"},
    ]
    ready = p._get_pipelines_ready_to_run()
    assert len(ready) == 1
    assert ready[0]["id"] == "1"


@patch("modules.pipeline.subprocess.run")
@patch("modules.pipeline.db")
def test_build_docker_image_success(mock_db, mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
    p = Pipeline()
    pl = {
        "id": "x",
        "image_name": "img:1",
        "directory": ".",
        "repo_name": "r",
        "created": "2020-01-01 00:00:00",
    }
    p.pipelines = [pl]
    p._build_docker_image(pl)
    assert pl["status"] == "success"
    mock_db.set.assert_any_call("r", "image_name", value="img:1")


@patch("modules.pipeline.subprocess.run")
@patch("modules.pipeline.db")
def test_build_docker_image_failure(mock_db, mock_run):
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="bad")
    p = Pipeline()
    pl = {
        "id": "x",
        "image_name": "img:1",
        "directory": ".",
        "repo_name": "r",
        "created": "2020-01-01 00:00:00",
    }
    p.pipelines = [pl]
    p._build_docker_image(pl)
    assert pl["status"] == "failed"

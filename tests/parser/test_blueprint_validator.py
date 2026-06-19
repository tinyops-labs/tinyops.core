from parser.blueprint_validator import BlueprintValidator


def test_validate_none_body():
    assert BlueprintValidator(None).validate() == ["Request body must be a JSON object."]


def test_validate_applications_not_list():
    assert "applications must be a list" in BlueprintValidator({"applications": {}}).validate()[0]


def test_validate_app_not_object():
    errs = BlueprintValidator({"applications": [1]}).validate()
    assert any("must be an object" in e for e in errs)


def test_validate_name_required():
    errs = BlueprintValidator({"applications": [{"image": "nginx"}]}).validate()
    assert any("name is required" in e for e in errs)


def test_validate_image_required_without_git():
    errs = BlueprintValidator({"applications": [{"name": "a", "image": ""}]}).validate()
    assert any("image is required" in e for e in errs)


def test_validate_git_must_be_object():
    errs = BlueprintValidator({"applications": [{"name": "a", "git": "bad"}]}).validate()
    assert any("git must be an object" in e for e in errs)


def test_validate_git_url_required():
    errs = BlueprintValidator(
        {"applications": [{"name": "a", "git": {"branch": "m"}}]}
    ).validate()
    assert any("git.url" in e for e in errs)


def test_validate_valid_git_no_image():
    assert BlueprintValidator(
        {"applications": [{"name": "a", "git": {"url": "https://x/y.git", "branch": "b"}}]}
    ).validate() == []


def test_validate_replicas_non_int():
    errs = BlueprintValidator(
        {"applications": [{"name": "a", "image": "i", "replicas": "1"}]}
    ).validate()
    assert any("replicas must be a non-negative integer" in e for e in errs)


def test_validate_replicas_negative():
    errs = BlueprintValidator(
        {"applications": [{"name": "a", "image": "i", "replicas": -1}]}
    ).validate()
    assert any("replicas must be a non-negative integer" in e for e in errs)


def test_validate_network_invalid():
    errs = BlueprintValidator(
        {"applications": [{"name": "a", "image": "i", "network": "  "}]}
    ).validate()
    assert any("network must be a non-empty string" in e for e in errs)


def test_validate_env_invalid_key():
    errs = BlueprintValidator(
        {"applications": [{"name": "a", "image": "i", "env": {"a b": "v"}}]}
    ).validate()
    assert any("invalid env key" in e for e in errs)


def test_validate_env_invalid_value_type():
    errs = BlueprintValidator(
        {"applications": [{"name": "a", "image": "i", "env": {"K": []}}]}
    ).validate()
    assert any("env value" in e for e in errs)


def test_validate_ports_not_object():
    errs = BlueprintValidator(
        {"applications": [{"name": "a", "image": "i", "ports": []}]}
    ).validate()
    assert any("ports must be an object" in e for e in errs)


def test_validate_ports_invalid_container_port():
    errs = BlueprintValidator(
        {"applications": [{"name": "a", "image": "i", "ports": {"99999": 80}}]}
    ).validate()
    assert any("container port" in e for e in errs)


def test_validate_ports_replicas_conflict():
    errs = BlueprintValidator(
        {"applications": [{"name": "a", "image": "i", "replicas": 2, "ports": {"80": 8080}}]}
    ).validate()
    assert any("cannot use port mappings" in e for e in errs)


def test_validate_volumes_not_list():
    errs = BlueprintValidator(
        {"applications": [{"name": "a", "image": "i", "volumes": {}}]}
    ).validate()
    assert any("volumes must be a list" in e for e in errs)


def test_validate_ssl_not_bool():
    errs = BlueprintValidator(
        {"applications": [{"name": "a", "image": "i", "ssl": "yes"}]}
    ).validate()
    assert any("ssl must be a boolean" in e for e in errs)


def test_validate_domain_not_string():
    errs = BlueprintValidator(
        {"applications": [{"name": "a", "image": "i", "domain": 1}]}
    ).validate()
    assert any("domain must be a string" in e for e in errs)


def test_validate_minimal_valid():
    assert (
        BlueprintValidator(
            {"applications": [{"name": "a", "image": "nginx:latest"}]}
        ).validate()
        == []
    )


def test_validate_empty_applications_omitted():
    assert BlueprintValidator({}).validate() == []

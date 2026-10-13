import pytest

import tea_cli.config as config


@pytest.mark.unit
def test_save_and_load_roundtrip():
    config.save_config({"api_key": "tea_abc", "api_url": "http://localhost:8007"})
    loaded = config.load_config()
    assert loaded["api_key"] == "tea_abc"
    assert loaded["api_url"] == "http://localhost:8007"


@pytest.mark.unit
def test_load_missing_returns_empty():
    assert config.load_config() == {}


@pytest.mark.unit
def test_env_overrides_config(monkeypatch):
    config.save_config({"api_key": "from_file"})
    monkeypatch.setenv("TEA_API_KEY", "from_env")
    assert config.get_api_key() == "from_env"


@pytest.mark.unit
def test_default_api_url(monkeypatch):
    # Default targets the production host; local dev opts in via TEA_API_URL.
    monkeypatch.delenv("TEA_API_URL", raising=False)
    assert config.get_api_url() == "https://api.goodtea.world"


@pytest.mark.unit
def test_validate_config_flags_unknown_key_and_bad_url():
    warnings = config.validate_config({"api_kye": "x", "api_url": "localhost:8007"})
    assert any("api_kye" in w for w in warnings)
    assert any("http://" in w for w in warnings)

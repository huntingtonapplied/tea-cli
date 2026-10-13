import pytest


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Point config at a temp dir and clear env so tests never touch ~/.tea."""
    import tea_cli.config as config

    cfg_dir = tmp_path / ".tea"
    monkeypatch.setattr(config, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", cfg_dir / "config.yaml")
    for var in ("TEA_API_KEY", "TEA_API_URL", "TEA_TIMEOUT", "TEA_MAX_RETRIES"):
        monkeypatch.delenv(var, raising=False)
    yield

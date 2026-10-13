import pytest
from click.testing import CliRunner

import tea_cli.commands.bookmarks as bookmarks_cmd
from tea_cli.main import cli


class FakeClient:
    """Stand-in for TeaClient that records calls and returns canned data."""

    def __init__(self, *a, **k):
        self.calls = []

    def list_bookmarks(self, params=None):
        self.calls.append(("list", params))
        return [{"id": str(i), "title": f"b{i}", "platform": "twitch", "url": f"http://x/{i}"}
                for i in range(10)]


@pytest.mark.unit
def test_bookmarks_list_applies_client_side_limit(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(bookmarks_cmd, "TeaClient", lambda *a, **k: fake)
    result = CliRunner().invoke(cli, ["bookmarks", "list", "--limit", "3"])
    assert result.exit_code == 0
    # 3 rows rendered, not 10
    assert result.output.count("http://x/") == 3
    # limit is not sent to the server (endpoint has no pagination)
    assert fake.calls == [("list", {})]


@pytest.mark.unit
def test_bookmarks_list_passes_platform_filter(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(bookmarks_cmd, "TeaClient", lambda *a, **k: fake)
    result = CliRunner().invoke(cli, ["bookmarks", "list", "--platform", "twitch"])
    assert result.exit_code == 0
    assert fake.calls == [("list", {"platform": "twitch"})]


@pytest.mark.unit
def test_json_output_for_bookmarks(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(bookmarks_cmd, "TeaClient", lambda *a, **k: fake)
    result = CliRunner().invoke(cli, ["-o", "json", "bookmarks", "list", "--limit", "2"])
    assert result.exit_code == 0
    assert result.output.strip().startswith("[")
    assert result.output.count('"id"') == 2

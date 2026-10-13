import httpx
import pytest

from tea_cli.api import TeaClient, AuthError, APIError


def _client_with_transport(handler, api_key="tea_test"):
    client = TeaClient(api_key=api_key, api_url="http://testserver")
    client._client = httpx.Client(transport=httpx.MockTransport(handler),
                                  base_url="http://testserver")
    return client


@pytest.mark.unit
def test_requires_auth_by_default():
    with pytest.raises(AuthError):
        TeaClient(api_key=None, api_url="http://x")


@pytest.mark.unit
def test_no_auth_allowed_when_optional():
    c = TeaClient(api_key=None, api_url="http://x", require_auth=False)
    assert c.api_key is None


@pytest.mark.unit
def test_sends_x_api_key_header():
    seen = {}

    def handler(request):
        seen["key"] = request.headers.get("X-API-Key")
        return httpx.Response(200, json={"email": "a@b.co"})

    client = _client_with_transport(handler, api_key="tea_secret")
    assert client.me() == {"email": "a@b.co"}
    assert seen["key"] == "tea_secret"


@pytest.mark.unit
def test_401_raises_auth_error():
    client = _client_with_transport(lambda r: httpx.Response(401, json={"detail": "nope"}))
    with pytest.raises(AuthError):
        client.me()


@pytest.mark.unit
def test_4xx_raises_api_error_with_detail():
    client = _client_with_transport(lambda r: httpx.Response(404, json={"detail": "missing"}))
    with pytest.raises(APIError) as exc:
        client.list_bookmarks()
    assert exc.value.status_code == 404
    assert "missing" in str(exc.value)


@pytest.mark.unit
def test_list_bookmarks_unwraps_data_envelope():
    payload = {"data": [{"id": "1"}], "total": 1}
    client = _client_with_transport(lambda r: httpx.Response(200, json=payload))
    assert client.list_bookmarks() == [{"id": "1"}]

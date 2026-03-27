from types import SimpleNamespace

from src.core.upload import newapi_upload


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json payload")
        return self._payload


def test_build_headers_rejects_non_ascii_api_key():
    try:
        newapi_upload._build_headers("系统访问令牌 (System Access Token)")
    except ValueError as exc:
        assert str(exc) == "Authorization Token 包含非 ASCII 字符，请确认填写的是实际令牌而不是中文说明"
    else:
        raise AssertionError("expected ValueError")


def test_upload_to_newapi_uses_ascii_authorization_header(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append({"url": url, "kwargs": kwargs})
        return FakeResponse(status_code=201)

    monkeypatch.setattr(newapi_upload.cffi_requests, "post", fake_post)

    success, message = newapi_upload.upload_to_newapi(
        account=SimpleNamespace(email="tester@example.com", access_token="access-token"),
        api_url="https://newapi.example.com/",
        api_key="token-123",
    )

    assert success is True
    assert message == "上传成功"
    assert calls[0]["url"] == "https://newapi.example.com/api/channel/"
    assert calls[0]["kwargs"]["headers"]["Authorization"] == "Bearer token-123"
    assert calls[0]["kwargs"]["headers"]["Content-Type"] == "application/json; charset=utf-8"
    assert calls[0]["kwargs"]["data"].startswith(b"{")


def test_upload_to_newapi_returns_clear_error_for_non_ascii_api_key():
    success, message = newapi_upload.upload_to_newapi(
        account=SimpleNamespace(email="tester@example.com", access_token="access-token"),
        api_url="https://newapi.example.com/",
        api_key="系统访问令牌 (System Access Token)",
    )

    assert success is False
    assert message == "上传异常: Authorization Token 包含非 ASCII 字符，请确认填写的是实际令牌而不是中文说明"

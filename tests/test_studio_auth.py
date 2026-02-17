import pytest

from gradio_studio import resolve_auth_credentials


def test_resolve_auth_credentials_none(monkeypatch):
    monkeypatch.delenv("WNSG_STUDIO_USER", raising=False)
    monkeypatch.delenv("WNSG_STUDIO_PASSWORD", raising=False)
    assert resolve_auth_credentials() is None


def test_resolve_auth_credentials_valid(monkeypatch):
    monkeypatch.setenv("WNSG_STUDIO_USER", "admin")
    monkeypatch.setenv("WNSG_STUDIO_PASSWORD", "super-secret")
    assert resolve_auth_credentials() == [("admin", "super-secret")]


def test_resolve_auth_credentials_requires_both(monkeypatch):
    monkeypatch.setenv("WNSG_STUDIO_USER", "admin")
    monkeypatch.delenv("WNSG_STUDIO_PASSWORD", raising=False)
    with pytest.raises(ValueError):
        resolve_auth_credentials()

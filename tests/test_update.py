"""Database download and atomic replace."""

from __future__ import annotations

import stat
from collections.abc import Iterator
from pathlib import Path

import pytest
import requests

from lupaxa.ipinfo_update.update import (
    DEFAULT_DATABASE,
    UpdateError,
    resolve_database,
    resolve_token,
    update_database,
)


class _Body:
    """Minimal streaming response for ``requests.get``."""

    def __init__(self, payload: bytes, *, status_error: str | None = None) -> None:
        self._payload = payload
        self._status_error = status_error

    def raise_for_status(self) -> None:
        """Raise when the test wants an HTTP failure."""
        if self._status_error is not None:
            raise requests.HTTPError(self._status_error)

    def iter_content(self, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
        """Yield the payload, bounded by ``chunk_size``."""
        if self._payload:
            yield self._payload[: max(chunk_size, 1)]

    def __enter__(self) -> _Body:
        return self

    def __exit__(self, *_exc: object) -> None:
        """Leave exceptions to the caller."""
        return None


def test_resolve_token_env_and_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """``--token`` wins over ``IPINFO_TOKEN``, including an empty flag."""
    monkeypatch.setenv("IPINFO_TOKEN", "from-env")
    assert resolve_token(None) == "from-env"
    assert resolve_token("from-flag") == "from-flag"
    assert resolve_token("") == ""
    monkeypatch.delenv("IPINFO_TOKEN", raising=False)
    assert resolve_token(None) == ""


def test_resolve_database_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """With no flag and no env var, the path is the working-directory default."""
    monkeypatch.delenv("IPINFO_DATABASE", raising=False)
    assert resolve_database(None) == DEFAULT_DATABASE


def test_resolve_database_env_and_flag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``--output`` wins over ``IPINFO_DATABASE``."""
    monkeypatch.setenv("IPINFO_DATABASE", str(tmp_path / "from-env.mmdb"))
    assert resolve_database(None) == tmp_path / "from-env.mmdb"
    chosen = tmp_path / "from-flag.mmdb"
    assert resolve_database(chosen) == chosen


def test_update_database_replaces_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A successful download replaces the destination and is world-readable."""
    destination = tmp_path / "ipinfo_lite.mmdb"
    destination.write_bytes(b"old")
    seen: dict[str, object] = {}

    def _get(url: str, **kwargs: object) -> _Body:
        seen["url"] = url
        seen["params"] = kwargs.get("params")
        seen["timeout"] = kwargs.get("timeout")
        return _Body(b"mmdb-bytes")

    monkeypatch.setattr("lupaxa.ipinfo_update.update.requests.get", _get)
    update_database(destination, "test-token", timeout=15)
    assert destination.read_bytes() == b"mmdb-bytes"
    assert stat.S_IMODE(destination.stat().st_mode) == 0o644
    assert seen["params"] == {"token": "test-token"}
    assert seen["timeout"] == 15
    assert list(tmp_path.iterdir()) == [destination]


def test_update_database_keeps_existing_file_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An HTTP error leaves the previous database in place."""
    destination = tmp_path / "ipinfo_lite.mmdb"
    destination.write_bytes(b"keep-me")

    def _get(url: str, **kwargs: object) -> _Body:
        return _Body(b"", status_error="403 Client Error")

    monkeypatch.setattr("lupaxa.ipinfo_update.update.requests.get", _get)
    with pytest.raises(UpdateError, match="download failed"):
        update_database(destination, "test-token")
    assert destination.read_bytes() == b"keep-me"


def test_update_database_rejects_empty_body(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An empty body is not installed."""
    destination = tmp_path / "ipinfo_lite.mmdb"
    destination.write_bytes(b"keep-me")
    monkeypatch.setattr(
        "lupaxa.ipinfo_update.update.requests.get",
        lambda url, **kwargs: _Body(b""),
    )
    with pytest.raises(UpdateError, match="empty"):
        update_database(destination, "test-token")
    assert destination.read_bytes() == b"keep-me"
    leftovers = [path for path in tmp_path.iterdir() if path != destination]
    assert leftovers == []


def test_update_database_requires_token(tmp_path: Path) -> None:
    """A blank token fails before any download."""
    with pytest.raises(UpdateError, match="token is not set"):
        update_database(tmp_path / "ipinfo_lite.mmdb", "   ")

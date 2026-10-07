"""Command-line entry points."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from lupaxa.ipinfo_update.cli import main
from lupaxa.ipinfo_update.version import __version__


def test_missing_token_exits_1(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """A missing token is an error and does not create a database."""
    monkeypatch.delenv("IPINFO_TOKEN", raising=False)
    destination = tmp_path / "ipinfo_lite.mmdb"
    code = main(["--output", str(destination)])
    assert code == 1
    assert "token is not set" in capsys.readouterr().err
    assert not destination.exists()


def test_success_prints_path(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """A successful run prints the database path and exits zero."""
    destination = tmp_path / "ipinfo_lite.mmdb"
    monkeypatch.setenv("IPINFO_TOKEN", "test-token")
    monkeypatch.setattr(
        "lupaxa.ipinfo_update.cli.update_database",
        lambda database, token, timeout: database.write_bytes(b"ok"),
    )
    code = main(["--output", str(destination)])
    assert code == 0
    assert str(destination) in capsys.readouterr().out
    assert destination.read_bytes() == b"ok"


def test_quiet_suppresses_success_line(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """``--quiet`` still updates the file and prints nothing."""
    destination = tmp_path / "ipinfo_lite.mmdb"
    monkeypatch.setenv("IPINFO_TOKEN", "test-token")
    monkeypatch.setattr(
        "lupaxa.ipinfo_update.cli.update_database",
        lambda database, token, timeout: database.write_bytes(b"ok"),
    )
    code = main(["--quiet", "--output", str(destination)])
    assert code == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_token_flag_overrides_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``--token`` is the value passed to the download."""
    destination = tmp_path / "ipinfo_lite.mmdb"
    seen: dict[str, str] = {}
    monkeypatch.setenv("IPINFO_TOKEN", "from-env")

    def _update(database: Path, token: str, timeout: float) -> None:
        """Record the token and write a stand-in database."""
        seen["token"] = token
        assert timeout > 0
        database.write_bytes(b"ok")

    monkeypatch.setattr("lupaxa.ipinfo_update.cli.update_database", _update)
    code = main(["--token", "from-flag", "--output", str(destination)])
    assert code == 0
    assert seen["token"] == "from-flag"


def test_version_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """``--version`` prints the package version and exits zero."""
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_bad_timeout_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    """A non-positive timeout is an argparse error."""
    with pytest.raises(SystemExit) as exc:
        main(["--timeout", "0"])
    assert exc.value.code == 2
    assert "timeout" in capsys.readouterr().err


def test_module_invocation() -> None:
    """``python -m lupaxa.ipinfo_update`` reports the package version."""
    env = os.environ.copy()
    src = str(Path(__file__).resolve().parents[1] / "src")
    current = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = src if not current else src + os.pathsep + current
    proc = subprocess.run(
        [sys.executable, "-m", "lupaxa.ipinfo_update", "--version"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert __version__ in (proc.stdout or "") + (proc.stderr or "")


def test_console_script_version() -> None:
    """The installed ``ipinfo-update`` script reports the package version."""
    script = Path(sys.prefix) / "bin" / "ipinfo-update"
    if not script.is_file():
        pytest.skip("ipinfo-update console script not installed in this environment")
    proc = subprocess.run(  # noqa: S603 - path comes from this interpreter's own prefix
        [str(script), "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert __version__ in (proc.stdout or "") + (proc.stderr or "")

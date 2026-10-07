"""Download the IPinfo Lite MMDB and replace a local copy."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import requests

DOWNLOAD_URL = "https://ipinfo.io/data/ipinfo_lite.mmdb"
DEFAULT_DATABASE = Path("ipinfo_lite.mmdb")
DEFAULT_TIMEOUT = 60.0
DATABASE_MODE = 0o644


class UpdateError(RuntimeError):
    """The database could not be downloaded or replaced."""


def resolve_token(token: str | None) -> str:
    """Return the IPinfo token for this run.

    ``token`` wins, including an empty string. Otherwise
    ``IPINFO_TOKEN`` is used when it is set.
    """
    if token is not None:
        return token
    return os.environ.get("IPINFO_TOKEN", "")


def resolve_database(output: Path | None) -> Path:
    """Return the database path for this run.

    ``output`` wins. Otherwise ``IPINFO_DATABASE`` is used when it is
    set. The fallback is ``ipinfo_lite.mmdb`` in the working directory.
    """
    if output is not None:
        return output
    env_path = os.environ.get("IPINFO_DATABASE", "").strip()
    if env_path:
        return Path(env_path)
    return DEFAULT_DATABASE


def update_database(
    database: Path,
    token: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> None:
    """Download the IPinfo Lite database and replace ``database``.

    The body is written beside the destination, then renamed into
    place. A failed download leaves any existing file unchanged. The
    finished file is mode ``0644`` so other local tools can read it.

    Parameters
    ----------
    database
        Destination path of the MMDB file.
    token
        IPinfo access token. Sent only as the ``token`` query parameter.
    timeout
        HTTP timeout in seconds.

    Raises
    ------
    UpdateError
        The token is empty, the download failed, or the body was empty.
    """
    if not token.strip():
        raise UpdateError("IPinfo token is not set")

    database.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    written = 0
    try:
        with requests.get(
            DOWNLOAD_URL,
            params={"token": token},
            stream=True,
            timeout=timeout,
        ) as response:
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(
                dir=database.parent,
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    temp_file.write(chunk)
                    written += len(chunk)
        if temp_path is None or written == 0:
            raise UpdateError("IPinfo download was empty")
        temp_path.chmod(DATABASE_MODE)
        temp_path.replace(database)
        temp_path = None
    except requests.RequestException as exc:
        raise UpdateError(f"IPinfo download failed: {exc}") from exc
    except OSError as exc:
        raise UpdateError(f"Could not write {database}: {exc}") from exc
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

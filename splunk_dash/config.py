from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Config:
    host: str
    token: str
    port: int = 8089
    owner: str = "nobody"
    scheme: str = "https"
    verify_ssl: bool = True

    @property
    def base_url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}"


def _load_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.lower() not in {"0", "false", "no"}


def load_config(env_path: Path | str | None = None) -> Config:
    """
    Load settings from environment and optional .env file.
    .env is useful for tokens and should stay out of version control.
    """
    env_file = Path(env_path) if env_path else Path(".env")
    load_dotenv(env_file)

    host = os.getenv("SPLUNK_HOST")
    token = os.getenv("SPLUNK_TOKEN")
    if not host or not token:
        raise ValueError("SPLUNK_HOST and SPLUNK_TOKEN must be set (see .env).")

    port = int(os.getenv("SPLUNK_PORT", "8089"))
    owner = os.getenv("SPLUNK_OWNER", "nobody")
    scheme = os.getenv("SPLUNK_SCHEME", "https")
    verify_ssl = _load_bool(os.getenv("SPLUNK_VERIFY_SSL"), True)
    return Config(host=host, token=token, port=port, owner=owner, scheme=scheme, verify_ssl=verify_ssl)

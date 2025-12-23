from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

import requests

from .config import load_config
from .inventory import Inventory
from .splunk_api import SplunkAPI


def _save_content(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _load_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Dashboard file not found: {path}")
    return path.read_text()


def handle_list(_: argparse.Namespace, inventory: Inventory, *__: object) -> int:
    if len(inventory) == 0:
        print("No dashboards registered in inventory.")
        return 0
    for entry in inventory.list_entries():
        meta = ", ".join(f"{k}={v}" for k, v in entry.metadata.items())
        meta_display = f" ({meta})" if meta else ""
        print(f"{entry.app}/{entry.name} [{entry.filename}]{meta_display}")
    return 0


def handle_download(args: argparse.Namespace, inventory: Inventory, api: SplunkAPI) -> int:
    entry = inventory.require(args.app, args.dashboard)
    content = api.fetch_dashboard(entry.app, entry.name)
    _save_content(entry.filename, content)
    print(f"Downloaded {entry.app}/{entry.name} to {entry.filename}")
    return 0


def handle_upload(args: argparse.Namespace, inventory: Inventory, api: SplunkAPI) -> int:
    entry = inventory.require(args.app, args.dashboard)
    path = entry.filename
    content = _load_file(path)
    api.upload_dashboard(entry.app, entry.name, content)
    print(f"Uploaded {entry.app}/{entry.name} from {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Splunk dashboards declared in inventory.yml.")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file containing SPLUNK_HOST and SPLUNK_TOKEN (default: .env)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List dashboards from the inventory")

    download = subparsers.add_parser("download", help="Download a dashboard from Splunk")
    download.add_argument("app", help="Splunk app name")
    download.add_argument("dashboard", help="Dashboard name")

    upload = subparsers.add_parser("upload", help="Upload a dashboard to Splunk")
    upload.add_argument("app", help="Splunk app name")
    upload.add_argument("dashboard", help="Dashboard name")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        inventory = Inventory()
        config = load_config(args.env_file)
        api = SplunkAPI(config)
        handlers: dict[str, Callable] = {
            "list": handle_list,
            "download": handle_download,
            "upload": handle_upload,
        }
        handler = handlers[args.command]
        return int(handler(args, inventory, api))
    except requests.HTTPError as exc:  # pragma: no cover - friendly HTTP errors
        resp = exc.response
        status = f"{resp.status_code} {resp.reason}" if resp is not None else "HTTP error"
        details = ""
        if resp is not None:
            try:
                details = resp.text[:500]
            except Exception:
                details = ""
        suffix = f"\nDetails: {details}" if details else ""
        print(f"HTTP error during '{args.command}': {status} — {exc}{suffix}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - CLI friendly message
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

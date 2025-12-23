from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

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
        desc = f" - {entry.description}" if entry.description else ""
        print(f"{entry.app}/{entry.name} [{entry.filename}]{desc}")
    return 0


def handle_download(args: argparse.Namespace, inventory: Inventory, api: SplunkAPI) -> int:
    entry = inventory.require(args.app, args.dashboard)
    output_path = Path(args.out) if args.out else entry.filename
    content = api.fetch_dashboard(entry.app, entry.name)
    _save_content(output_path, content)
    print(f"Downloaded {entry.app}/{entry.name} to {output_path}")
    return 0


def handle_upload(args: argparse.Namespace, inventory: Inventory, api: SplunkAPI) -> int:
    entry = inventory.require(args.app, args.dashboard)
    path = Path(args.file) if args.file else entry.filename
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
    download.add_argument("--out", help="Override output path; defaults to inventory filename")

    upload = subparsers.add_parser("upload", help="Upload a dashboard to Splunk")
    upload.add_argument("app", help="Splunk app name")
    upload.add_argument("dashboard", help="Dashboard name")
    upload.add_argument("--file", help="Override source file path; defaults to inventory filename")

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
    except Exception as exc:  # pragma: no cover - CLI friendly message
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

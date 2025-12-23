from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Optional

import yaml


@dataclass
class DashboardEntry:
    app: str
    name: str
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.app}:{self.name}"

    @property
    def filename(self) -> Path:
        return Path("dashboards") / self.app / f"{self.name}.xml"


class Inventory:
    def __init__(self, path: Path = Path("inventory.yml"), config_path: Path = Path("config.yml")) -> None:
        self.path = Path(path)
        self.allowed_metadata_fields = self._load_allowed_metadata_fields(config_path)
        raw = yaml.safe_load(self.path.read_text()) if self.path.exists() else None
        dashboards = raw.get("dashboards", []) if raw else []
        self._entries: Dict[str, DashboardEntry] = {}
        for item in dashboards:
            app = item["app"]
            name = item["name"]
            metadata = {str(k): str(v) for k, v in (item.get("metadata") or {}).items()}
            unknown_keys = set(metadata.keys()) - self.allowed_metadata_fields
            if unknown_keys:
                allowed = ", ".join(sorted(self.allowed_metadata_fields)) or "none"
                raise ValueError(f"Unknown metadata fields for {app}/{name}: {', '.join(sorted(unknown_keys))} (allowed: {allowed})")
            entry = DashboardEntry(app=app, name=name, metadata=metadata)
            self._entries[entry.key] = entry

    def _load_allowed_metadata_fields(self, path: Path) -> set[str]:
        if not path.exists():
            return set()
        data = yaml.safe_load(path.read_text()) or {}
        fields = data.get("metadata_fields", [])
        if not isinstance(fields, list):
            raise ValueError("config.yml: 'metadata_fields' must be a list")
        return {str(field) for field in fields}

    def list_entries(self) -> Iterable[DashboardEntry]:
        return self._entries.values()

    def require(self, app: str, name: str) -> DashboardEntry:
        key = f"{app}:{name}"
        if key not in self._entries:
            known = ", ".join(sorted(self._entries.keys())) or "none"
            raise ValueError(f"Dashboard {app}/{name} is not declared in inventory. Known: {known}")
        return self._entries[key]

    def __len__(self) -> int:  # pragma: no cover - convenience
        return len(self._entries)

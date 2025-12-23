from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

import yaml


@dataclass
class DashboardEntry:
    app: str
    name: str
    description: Optional[str] = None

    @property
    def key(self) -> str:
        return f"{self.app}:{self.name}"

    @property
    def filename(self) -> Path:
        return Path("dashboards") / self.app / f"{self.name}.xml"


class Inventory:
    def __init__(self, path: Path = Path("inventory.yml")) -> None:
        self.path = Path(path)
        raw = yaml.safe_load(self.path.read_text()) if self.path.exists() else None
        dashboards = raw.get("dashboards", []) if raw else []
        self._entries: Dict[str, DashboardEntry] = {}
        for item in dashboards:
            app = item["app"]
            name = item["name"]
            description = item.get("description")
            entry = DashboardEntry(app=app, name=name, description=description)
            self._entries[entry.key] = entry

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

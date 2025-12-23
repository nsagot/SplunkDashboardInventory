from __future__ import annotations

from typing import Dict

import requests

from .config import Config


class SplunkAPI:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {config.token}"})

    def _dashboard_url(self, app: str, name: str) -> str:
        return f"{self.config.base_url}/servicesNS/{self.config.owner}/{app}/data/ui/views/{name}"

    def fetch_dashboard(self, app: str, name: str) -> str:
        """
        Download a dashboard definition from Splunk.
        Returns the raw XML/JSON payload as a string.
        """
        url = self._dashboard_url(app, name)
        resp = self.session.get(url, params={"output_mode": "json"}, verify=self.config.verify_ssl)
        resp.raise_for_status()
        payload: Dict = resp.json()
        try:
            entry = payload["entry"][0]
            content = entry["content"]
            data = content.get("eai:data") or content.get("eai:acl")
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"Unexpected response structure while reading {app}/{name}") from exc
        if not isinstance(data, str):
            raise ValueError(f"No dashboard content returned for {app}/{name}")
        return data

    def upload_dashboard(self, app: str, name: str, content: str) -> None:
        """
        Upload or replace a dashboard definition in Splunk.
        """
        url = self._dashboard_url(app, name)
        resp = self.session.post(
            url,
            params={"output_mode": "json"},
            data={"name": name, "eai:data": content},
            verify=self.config.verify_ssl,
        )
        resp.raise_for_status()

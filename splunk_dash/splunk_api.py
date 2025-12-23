from __future__ import annotations

from typing import Dict, Iterable, List, Optional

import requests

from .config import Config


class SplunkAPI:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {config.token}"})

    def _dashboard_url(self, app: str, name: str, owner: str | None = None) -> str:
        target_owner = owner or self.config.owner
        return f"{self.config.base_url}/servicesNS/{target_owner}/{app}/data/ui/views/{name}"

    def _owners_to_try(self, scope: str | None = None) -> Iterable[str]:
        """
        Retourne la liste des owner à tester en fonction du scope souhaité.
        - global : seulement nobody
        - app : owner configuré, puis nobody
        """
        seen = set()
        if scope == "global":
            candidates = ("nobody",)
        else:
            candidates = (self.config.owner, "nobody")
        for owner in candidates:
            if owner and owner not in seen:
                seen.add(owner)
                yield owner

    def _fetch_once(self, app: str, name: str, owner: str) -> Dict:
        url = self._dashboard_url(app, name, owner=owner)
        resp = self.session.get(url, params={"output_mode": "json"}, verify=self.config.verify_ssl)
        resp.raise_for_status()
        payload: Dict = resp.json()
        try:
            entry = payload["entry"][0]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"Unexpected response structure while reading {app}/{name}") from exc
        return entry

    def fetch_dashboard(self, app: str, name: str, scope: str | None = None) -> str:
        """
        Download a dashboard definition from Splunk.
        Tente d'abord selon le scope : global => nobody uniquement ; app => owner configuré puis nobody.
        """
        last_error: Exception | None = None
        for owner in self._owners_to_try(scope=scope):
            try:
                entry = self._fetch_once(app, name, owner=owner)
                content = entry.get("content") or {}
                data = content.get("eai:data") or content.get("eai:acl")
                if not isinstance(data, str):
                    raise ValueError(f"No dashboard content returned for {app}/{name}")
                return data
            except requests.HTTPError as exc:
                last_error = exc
                if exc.response is not None and exc.response.status_code == 404:
                    continue
                raise
        if last_error:
            raise last_error
        raise ValueError(f"Unable to fetch dashboard {app}/{name}")

    def _upload_once(
        self,
        app: str,
        name: str,
        content: str,
        owner: str,
        roles_read: Optional[List[str]],
        roles_write: Optional[List[str]],
        include_name: bool = True,
    ) -> None:
        # Paramètre sharing non supporté par ce handler, on s'appuie sur le chemin (owner).
        params: Dict[str, str] = {"output_mode": "json"}
        if roles_read:
            params["perms.read"] = ",".join(roles_read)
        if roles_write:
            params["perms.write"] = ",".join(roles_write)
        url = self._dashboard_url(app, name, owner=owner)
        resp = self.session.post(
            url,
            params=params,
            data={"eai:data": content, **({"name": name} if include_name else {})},
            verify=self.config.verify_ssl,
        )
        resp.raise_for_status()

    def _probe_dashboard(self, app: str, name: str) -> Optional[Dict[str, str]]:
        """
        Tente de récupérer le dashboard pour connaître owner/sharing actuels.
        """
        try:
            entry = self._fetch_once(app, name, owner="-")
            acl = entry.get("acl") or {}
            owner = acl.get("owner")
            sharing = acl.get("sharing")
            if not owner or not sharing:
                return None
            return {"owner": owner, "sharing": sharing}
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                return None
            raise

    def upload_dashboard(
        self,
        app: str,
        name: str,
        content: str,
        scope: str = "app",
        roles_read: Optional[List[str]] = None,
        roles_write: Optional[List[str]] = None,
    ) -> None:
        """
        Upload ou création d'un dashboard Splunk.
        Stratégie : tenter en global (owner nobody), sinon en app (owner configuré), et si rien ne marche, créer en global.
        Les rôles sont appliqués si fournis.
        """
        resolved_scope = scope if scope in {"app", "global"} else "app"
        owner_app = self.config.owner or ""
        if owner_app.lower() == "nobody":
            owner_app = ""

        # 0) Si le dashboard existe déjà, on récupère son owner/sharing et on l'update là-bas.
        probe = self._probe_dashboard(app, name)
        if probe:
            target_sharing = probe.get("sharing") or resolved_scope
            target_owner = "nobody" if target_sharing == "global" else (probe.get("owner") or owner_app or "-")
            self._upload_once(
                app=app,
                name=name,
                content=content,
                owner=target_owner,
                roles_read=roles_read,
                roles_write=roles_write,
                include_name=False,
            )
            return

        # 1) Si on veut du global, essayer d'abord global (nobody)
        if resolved_scope == "global":
            try:
                try:
                    self._upload_once(
                        app=app,
                        name=name,
                        content=content,
                        owner="nobody",
                        roles_read=roles_read,
                        roles_write=roles_write,
                    )
                    return
                except requests.HTTPError as exc_create:
                    # Si l'objet existe déjà sur ce scope, on retente sans paramètre name pour mettre à jour.
                    if exc_create.response is not None and exc_create.response.status_code in (400, 409):
                        self._upload_once(
                            app=app,
                            name=name,
                            content=content,
                            owner="nobody",
                            roles_read=roles_read,
                            roles_write=roles_write,
                            include_name=False,
                        )
                        return
                    raise
            except requests.HTTPError as exc:
                if exc.response is None or exc.response.status_code not in (400, 404):
                    raise

        # 2) Essayer en scope app avec l'owner configuré (ou "-")
        if owner_app:
            try:
                try:
                    self._upload_once(
                        app=app,
                        name=name,
                        content=content,
                        owner=owner_app,
                        roles_read=roles_read,
                        roles_write=roles_write,
                    )
                    return
                except requests.HTTPError as exc_create:
                    if exc_create.response is not None and exc_create.response.status_code in (400, 409):
                        self._upload_once(
                            app=app,
                            name=name,
                            content=content,
                            owner=owner_app,
                            roles_read=roles_read,
                            roles_write=roles_write,
                            include_name=False,
                        )
                        return
                    raise
            except requests.HTTPError as exc:
                if exc.response is None or exc.response.status_code not in (400, 404):
                    raise

        # 3) Dernier recours : global
        self._upload_once(
            app=app,
            name=name,
            content=content,
            owner="nobody",
            roles_read=roles_read,
            roles_write=roles_write,
            include_name=False,
        )

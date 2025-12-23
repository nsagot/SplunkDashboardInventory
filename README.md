# Splunk Dashboard Inventory CLI

Petite application Python pour lister, télécharger et uploader des dashboards Splunk en suivant un inventaire (`inventory.yml`). Un dashboard doit d'abord être déclaré dans l'inventaire pour pouvoir être manipulé.

## Installation rapide
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration Splunk
- Créez un fichier `.env` (non versionné) à la racine avec au minimum :
  ```
  SPLUNK_HOST=so1
  SPLUNK_TOKEN=VotreTokenIci
  # Options :
  # SPLUNK_PORT=8089
  # SPLUNK_OWNER=nobody
  # SPLUNK_SCHEME=https
  # SPLUNK_VERIFY_SSL=true
  ```
- `.env` est déjà listé dans `.gitignore`.

## Inventaire
`inventory.yml` contient les dashboards autorisés et leurs ACL :
```yaml
dashboards:
  - app: search
    name: sample_dashboard
    description: Tableau de démonstration
    scope: app        # "app" ou "global"
    roles_read: [power, user]   # optionnel
    roles_write: [admin]        # optionnel
```
Le chemin local est calculé automatiquement : `dashboards/<app>/<dashboard>.xml`.
Le téléchargement respecte le scope (global => nobody). L'upload s'appuie sur le chemin (owner) sans paramètre `sharing` : il tente global (owner nobody), puis app (owner configuré), et en dernier recours global. Les rôles lecture/écriture sont appliqués si fournis.
Si le dashboard existe déjà (409/400), une seconde requête est envoyée sans paramètre `name` pour mettre à jour l'objet existant.

## Commandes
```
python -m splunk_dash.cli list
python -m splunk_dash.cli download <app> <dashboard> [--out chemin.xml]
python -m splunk_dash.cli upload   <app> <dashboard> [--file chemin.xml]
```
Exemple :
```
python -m splunk_dash.cli download search sample_dashboard
python -m splunk_dash.cli upload search sample_dashboard
```

Les dashboards sont stockés dans `dashboards/<app>/<dashboard>.xml` (un dossier par app Splunk).

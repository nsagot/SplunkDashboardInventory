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
`inventory.yml` contient les dashboards autorisés :
```yaml
dashboards:
  - app: search
    name: sample_dashboard
```
Le chemin local est calculé automatiquement : `dashboards/<app>/<dashboard>.xml`.

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

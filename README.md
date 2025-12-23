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
`config.yml` définit les champs de métadonnées autorisés :
```yaml
metadata_fields:
  - owner
  - version
  - lookup
  - base_search
```

`inventory.yml` contient les dashboards autorisés et leurs métadonnées :
```yaml
dashboards:
  - app: search
    name: sample_dashboard
    metadata:
      owner: admin
      version: "1.2.3"
      lookup: my_lookup.csv
      base_search: index=main sourcetype=access_combined
```
Le chemin local est calculé automatiquement : `dashboards/<app>/<dashboard>.xml`.
L'upload s'appuie sur l'owner dans l'URL (global = nobody, sinon owner configuré) et, si le dashboard existe déjà (409/400), une seconde requête est envoyée sans paramètre `name` pour mettre à jour l'objet existant.

## Commandes
```
python -m splunk_dash.cli list
python -m splunk_dash.cli download <app> <dashboard>
python -m splunk_dash.cli upload   <app> <dashboard>
```
Exemple :
```
python -m splunk_dash.cli download search sample_dashboard
python -m splunk_dash.cli upload search sample_dashboard
```

Les dashboards sont stockés dans `dashboards/<app>/<dashboard>.xml` (un dossier par app Splunk).

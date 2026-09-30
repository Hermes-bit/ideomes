"""Réglages de l'API (fichier .env à la racine du projet)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

RACINE = Path(__file__).resolve().parents[2]


class Reglages(BaseSettings):
    model_config = SettingsConfigDict(env_file=RACINE / ".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = f"sqlite:///{(RACINE / 'data' / 'ideomes.db').as_posix()}"
    dossier_blobs: Path = RACINE / "data" / "blobs"
    web_dist: Path = RACINE / "web" / "dist"
    # Identité en développement : l'en-tête X-Dev-User porte l'identifiant ; celui-ci est le propriétaire.
    proprietaire_uid: str = "owner"
    api_jeton_service: str = "dev-service"  # utilisé par Hermès et les tâches planifiées
    pipeline_auto: bool = True  # lance Zeus à chaque nouvelle idée
    cors_origines: str = "http://localhost:8000,http://127.0.0.1:8000,http://localhost:5500"


reglages = Reglages()

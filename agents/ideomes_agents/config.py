"""Réglages lus dans l'environnement (fichier .env à la racine du projet)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

RACINE = Path(__file__).resolve().parents[2]


class Reglages(BaseSettings):
    model_config = SettingsConfigDict(env_file=RACINE / ".env", env_file_encoding="utf-8", extra="ignore")

    # Modèles Claude
    anthropic_api_key: str = ""
    modele_fort: str = "claude-sonnet-5-5"
    modele_leger: str = "claude-haiku-4-5-20251001"
    # "anthropic" en production, "simule" pour développer et tester sans clé ni coût
    llm_mode: str = "simule"
    llm_max_relances: int = 2
    llm_timeout_s: float = 60.0

    # Garde-fous
    seuil_confiance: float = 0.7
    prompt_version: str = "2026-09-30"

    # Journal d'audit local (en plus de la base, via l'API)
    journal_fichier: Path = RACINE / "data" / "journal_audit.jsonl"

    # API Idéomès (pour Hermès et les tâches planifiées)
    api_url: str = "http://localhost:8000"
    api_jeton_service: str = "dev-service"


reglages = Reglages()

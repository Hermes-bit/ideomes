"""Lecture du registre des agents (agents.yaml)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

FICHIER = Path(__file__).with_name("agents.yaml")


@lru_cache
def registre() -> dict:
    return yaml.safe_load(FICHIER.read_text(encoding="utf-8"))


def fiche(agent_id: str) -> dict:
    r = registre()
    for cle in ("orchestrateur", "auditeur", "veille"):
        if r[cle]["id"] == agent_id:
            return r[cle]
    for a in r["agents"]:
        if a["id"] == agent_id:
            return a
    raise KeyError(agent_id)


def nom(agent_id: str) -> str:
    return fiche(agent_id)["nom"]

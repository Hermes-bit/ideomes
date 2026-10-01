"""Accès à la base Supabase pour les tâches planifiées (Hermès).

Remplace les appels à l'ancienne API FastAPI, qui n'est plus déployée depuis le
passage de l'application web à Supabase. On parle directement à PostgREST sur la
table `documents(collection, doc_id, data jsonb)`, avec la clé `service_role`
(elle contourne les politiques RLS : elle ne doit jamais quitter le serveur).
"""

from __future__ import annotations

import os
from typing import Any

import httpx


class ConfigManquante(RuntimeError):
    pass


def _reglages() -> tuple[str, str]:
    url = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    cle = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not url or not cle:
        raise ConfigManquante(
            "SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY doivent être définies dans l'environnement."
        )
    if cle.startswith("sb_publishable_") or cle.startswith("eyJ") and "anon" in cle:
        raise ConfigManquante(
            "La clé fournie ressemble à la clé publique. Hermès écrit en base : "
            "il lui faut la clé service_role (Supabase > Settings > API > service_role)."
        )
    return url, cle


def _entetes(cle: str) -> dict[str, str]:
    return {
        "apikey": cle,
        "Authorization": f"Bearer {cle}",
        "Content-Type": "application/json",
    }


def lire_collection(collection: str) -> list[dict[str, Any]]:
    """Renvoie les `data` de tous les documents d'une collection."""
    url, cle = _reglages()
    with httpx.Client(timeout=30) as h:
        r = h.get(
            f"{url}/rest/v1/documents",
            params={"select": "doc_id,data", "collection": f"eq.{collection}"},
            headers=_entetes(cle),
        )
        r.raise_for_status()
        return [{"doc_id": x["doc_id"], **(x.get("data") or {})} for x in r.json()]


def ecrire_documents(collection: str, docs: dict[str, dict[str, Any]]) -> None:
    """Insère ou met à jour plusieurs documents en un appel (clé : collection + doc_id)."""
    if not docs:
        return
    url, cle = _reglages()
    corps = [{"collection": collection, "doc_id": doc_id, "data": data} for doc_id, data in docs.items()]
    with httpx.Client(timeout=30) as h:
        r = h.post(
            f"{url}/rest/v1/documents",
            params={"on_conflict": "collection,doc_id"},
            headers={**_entetes(cle), "Prefer": "resolution=merge-duplicates,return=minimal"},
            json=corps,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"Écriture Supabase refusée ({r.status_code}) : {r.text[:300]}")

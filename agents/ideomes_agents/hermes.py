"""Hermès, veille des actualités (hors pipeline des idées).

Chaque matin : recherche web (outil serveur d'Anthropic), propositions vérifiées, envoi à l'API
dans la collection « veille ». L'administrateur approuve dans le tableau de bord : Hermès ne publie jamais seul.
Lancement : `ideomes veille` (planifiez-le avec cron / le Planificateur de tâches Windows à 06:52).
"""

from __future__ import annotations

import json
import re
import time
from datetime import date
from typing import Any

import httpx
import jsonschema

from .config import reglages
from .core.audit import journaliser
from .core.llm import client, modele_pour, prompt_systeme, schema

OUTIL_RECHERCHE = {"type": "web_search_20250305", "name": "web_search", "max_uses": 8}


def _nettoyer(v: Any) -> Any:
    """Règle maison : jamais de tiret long."""
    if isinstance(v, str):
        return re.sub(r"\s*—\s*", " : ", v)
    if isinstance(v, list):
        return [_nettoyer(x) for x in v]
    if isinstance(v, dict):
        return {k: _nettoyer(x) for k, x in v.items()}
    return v


def rechercher(deja_vus: list[str]) -> dict:
    donnees = {"date_du_jour": date.today().isoformat(), "deja_vus": deja_vus}
    if reglages.llm_mode != "anthropic":
        return client().appeler("HERMES", "hermes", "hermes", donnees, "fort").donnees

    import anthropic

    api = anthropic.Anthropic(api_key=reglages.anthropic_api_key, timeout=180)
    sch = schema("hermes")
    outil_sortie = {
        "name": "rendre_resultat",
        "description": "Renvoie les propositions de veille.",
        "input_schema": sch,
    }
    messages: list[dict] = [
        {"role": "user", "content": "<donnees>\n" + json.dumps(donnees, ensure_ascii=False) + "\n</donnees>"}
    ]
    for _ in range(6):  # la recherche serveur peut demander plusieurs tours (pause_turn)
        rep = api.messages.create(
            model=modele_pour("fort"),
            max_tokens=4096,
            system=prompt_systeme("hermes"),
            messages=messages,
            tools=[OUTIL_RECHERCHE, outil_sortie],
        )
        bloc = next(
            (b for b in rep.content if getattr(b, "type", "") == "tool_use" and b.name == "rendre_resultat"), None
        )
        if bloc:
            sortie = dict(bloc.input)
            jsonschema.validate(sortie, sch)
            return sortie
        messages.append({"role": "assistant", "content": rep.content})
        if rep.stop_reason != "pause_turn":
            messages.append({"role": "user", "content": "Termine maintenant en appelant l'outil rendre_resultat."})
    raise RuntimeError("Hermès n'a pas rendu de résultat.")


def executer(api_url: str | None = None) -> dict:
    url = (api_url or reglages.api_url).rstrip("/")
    entetes = {"X-Service-Token": reglages.api_jeton_service}
    with httpx.Client(base_url=url, headers=entetes, timeout=30) as h:
        existants = h.get("/api/db/collection/actus").json().get("docs", []) + h.get(
            "/api/db/collection/veille"
        ).json().get("docs", [])
        deja_vus = sorted(
            {x.get("data", {}).get(k) for x in existants for k in ("lien", "titre") if x.get("data", {}).get(k)}
        )
        sortie = _nettoyer(rechercher(deja_vus))
        maintenant_ms = int(time.time() * 1000)
        for i, p in enumerate(sortie["propositions"]):
            doc = {
                **p,
                "statut": "en_attente",
                "propose_le": maintenant_ms,
                "agent": "Hermès",
                "image": p["categorie"].lower(),
            }
            h.put(f"/api/db/doc/veille/h{maintenant_ms}{i}", json={"data": doc})
        h.put(
            "/api/db/doc/config/hermes",
            json={
                "data": {
                    "derniere_execution": maintenant_ms,
                    "nb_propositions": len(sortie["propositions"]),
                    "message": sortie["message"],
                }
            },
        )
    journaliser("veille", "HERMES", "execution", propositions=len(sortie["propositions"]))
    return sortie

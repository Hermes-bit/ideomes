"""Hermès, veille des actualités (hors pipeline des idées).

Chaque matin : recherche web (outil serveur d'Anthropic), propositions vérifiées, envoi à l'API
dans la collection « veille » de Supabase. L'administrateur approuve dans le tableau de bord :
Hermès ne publie jamais seul.
Lancement : `ideomes veille` (planifié chaque matin par .github/workflows/veille.yml).
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from typing import Any

import jsonschema

from . import supabase_io
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


def executer() -> dict:
    """Lance une veille et dépose les propositions dans Supabase.

    Les noms de champs suivent exactement ce que lit le tableau de bord :
    statut « proposee » pour qu'une proposition s'affiche, et config/hermes avec
    `lastRun` / `message` pour la ligne d'état.
    """
    existants = supabase_io.lire_collection("actus") + supabase_io.lire_collection("veille")
    deja_vus = sorted({x[k] for x in existants for k in ("lien", "titre") if x.get(k)})

    sortie = _nettoyer(rechercher(deja_vus))
    maintenant = datetime.now(timezone.utc).isoformat()

    propositions = {}
    for p in sortie["propositions"]:
        # Identifiant stable dérivé du lien : une même actualité reproposée
        # écrase son entrée au lieu d'en créer une seconde.
        ident = "h" + hashlib.sha1(p["lien"].encode("utf-8")).hexdigest()[:16]
        propositions[ident] = {
            **p,
            "statut": "proposee",
            "proposeLe": maintenant,
            "agent": "Hermès",
            "image": p["categorie"].lower(),
        }
    supabase_io.ecrire_documents("veille", propositions)
    supabase_io.ecrire_documents(
        "config",
        {"hermes": {"lastRun": maintenant, "nbPropositions": len(propositions), "message": sortie["message"]}},
    )

    journaliser("veille", "HERMES", "execution", propositions=len(propositions))
    return sortie

"""Journal d'audit : chaque décision est horodatée avec l'agent, la version du prompt,
le modèle et un résumé des données utilisées (jamais de donnée personnelle en clair)."""

from __future__ import annotations

import contextlib
import json
import threading
from typing import Any

from ..config import reglages
from .dossier import maintenant

_verrou = threading.Lock()
_ecouteurs: list = []  # l'API s'y abonne pour écrire aussi en base


def abonner(fonction) -> None:
    _ecouteurs.append(fonction)


def journaliser(dossier_id: str, agent: str, evenement: str, **infos: Any) -> dict:
    ligne = {
        "date": maintenant(),
        "dossier": dossier_id,
        "agent": agent,
        "evenement": evenement,
        "prompt_version": reglages.prompt_version,
        **infos,
    }
    reglages.journal_fichier.parent.mkdir(parents=True, exist_ok=True)
    with _verrou, reglages.journal_fichier.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    for e in _ecouteurs:
        with contextlib.suppress(Exception):  # un écouteur défaillant ne bloque jamais la chaîne
            e(ligne)
    return ligne

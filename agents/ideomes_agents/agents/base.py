"""Socle commun : journalisation, contrôle de confiance, écriture dans le seul champ de l'agent."""

from __future__ import annotations

import time
from typing import Any

from ..config import reglages
from ..core import llm
from ..core.audit import journaliser
from ..core.contexte import Contexte
from ..core.dossier import Dossier
from ..registry import fiche


class Agent:
    id: str = ""
    prompt: str | None = None  # nom du prompt et du schéma (ex. "athena")

    def __init__(self) -> None:
        self.fiche = fiche(self.id)
        self.nom = self.fiche["nom"]

    # --- à implémenter par chaque agent -------------------------------------------------------
    def traiter(self, dossier: Dossier, ctx: Contexte) -> dict[str, Any]:
        raise NotImplementedError

    # --- appel commun -------------------------------------------------------------------------
    def llm(self, donnees: dict[str, Any], dossier_id: str) -> dict[str, Any]:
        r = llm.client().appeler(self.id, self.prompt, self.prompt, donnees, self.fiche.get("modele"))
        journaliser(
            dossier_id,
            self.id,
            "appel_llm",
            modele=r.modele,
            tentatives=r.tentatives,
            duree_s=round(r.duree_s, 2),
            jetons=[r.jetons_entree, r.jetons_sortie],
        )
        return r.donnees

    def executer(self, dossier: Dossier, ctx: Contexte) -> dict[str, Any]:
        debut = time.monotonic()
        try:
            sortie = self.traiter(dossier, ctx)
        except llm.ErreurAgent as e:
            dossier.revue_humaine = {"agent": self.id, "motif": str(e)}
            dossier.trace(self.id, "erreur", message=str(e))
            journaliser(dossier.id, self.id, "erreur", message=str(e))
            raise
        dossier.sorties[self.id] = sortie
        seuil = self.fiche.get("seuil_confiance")
        conf = sortie.get("confiance")
        if seuil is not None and conf is not None and conf < seuil and not dossier.revue_humaine:
            dossier.revue_humaine = {
                "agent": self.id,
                "motif": f"Confiance {conf:.2f} sous le seuil {seuil}",
                "seuil": seuil,
            }
        dossier.trace(self.id, "sortie", confiance=conf, duree_s=round(time.monotonic() - debut, 2))
        journaliser(dossier.id, self.id, "sortie", confiance=conf, statut=dossier.statut)
        return sortie

    def __repr__(self) -> str:
        return f"<{self.id} {self.nom}>"


def seuil_global() -> float:
    return reglages.seuil_confiance

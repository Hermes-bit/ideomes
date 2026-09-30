"""A8 · Héphaïstos, générateur de solutions (2 à 3 pistes, au moins une à faible coût)."""

from __future__ import annotations

from ..core.llm import ErreurAgent
from .base import Agent


class Hephaistos(Agent):
    id = "A8"
    prompt = "hephaistos"

    def traiter(self, dossier, ctx):
        a3, a5 = dossier.sorties.get("A3", {}), dossier.sorties.get("A5", {})
        sortie = self.llm(
            {
                "resume": a3.get("resume"),
                "besoin_reel": a3.get("besoin_reel"),
                "categorie": a3.get("categorie"),
                "commune": (a5.get("commune") or {}).get("nom"),
                "score": dossier.sorties.get("A7", {}).get("score"),
            },
            dossier.id,
        )
        if not any(p["faible_cout"] for p in sortie["pistes"]):
            raise ErreurAgent("A8 : aucune piste à faible coût (garde-fou)")
        return sortie

"""A11 · Niké, évaluatrice d'impact : distingue mesuré et estimé. Boucle de retour vers Kairos."""

from __future__ import annotations

from .base import Agent


class Nike(Agent):
    id = "A11"
    prompt = "nike"

    def traiter(self, dossier, ctx):
        fiche_projet = dossier.sorties.get("A9", {})
        mesures = dossier.contribution.meta.get("mesures_impact", {})
        sortie = self.llm(
            {
                "objectifs": fiche_projet.get("objectifs"),
                "indicateurs": fiche_projet.get("indicateurs_reussite"),
                "budget_prevu": fiche_projet.get("budget"),
                **mesures,
            },
            dossier.id,
        )
        dossier.statut = "evalue"
        return sortie

"""A9 · Héra, cheffe de projet : ne démarre JAMAIS sans validation humaine tracée."""

from __future__ import annotations

from .base import Agent


class ValidationManquante(PermissionError):
    pass


class Hera(Agent):
    id = "A9"
    prompt = "hera"

    def traiter(self, dossier, ctx):
        d = dossier.decision_comite or {}
        if d.get("decision") != "valide" or not d.get("validateur") or not d.get("date"):
            raise ValidationManquante(
                "Héra ne démarre qu'après une validation du comité tracée (décision, validateur, date)."
            )
        pistes = dossier.sorties.get("A8", {}).get("pistes", [])
        piste = pistes[d.get("piste_retenue", 0)] if pistes else {}
        sortie = self.llm(
            {
                "piste": piste,
                "commentaire_comite": d.get("commentaire"),
                "resume": dossier.sorties.get("A3", {}).get("resume"),
            },
            dossier.id,
        )
        dossier.statut = "en_projet"
        return sortie

"""A1 · Déméter, collecteur multicanal : structure la contribution sans l'interpréter."""

from __future__ import annotations

from ..core.dossier import Dossier
from .base import Agent


class Demeter(Agent):
    id = "A1"

    def traiter(self, dossier: Dossier, ctx):
        c = dossier.contribution
        manquants = [
            k for k, v in {"texte": c.texte.strip(), "consentement_rgpd": c.consentement_rgpd}.items() if not v
        ]
        if not c.consentement_rgpd:
            dossier.statut = "erreur"
        return {
            "texte": c.texte.strip(),
            "canal": c.canal,
            "langue": c.langue or "fr",
            "localisation_declaree": {"region": c.region, "province": c.province, "commune": c.commune},
            "pieces_jointes": c.pieces_jointes,
            "consentements": {"rgpd": c.consentement_rgpd, "contact": c.consentement_contact},
            "complet": not manquants,
            "manquants": manquants,
            # À brancher : transcription vocale, OCR des formulaires papier, traduction (mooré, dioula, fulfuldé)
            "transcription": None,
        }

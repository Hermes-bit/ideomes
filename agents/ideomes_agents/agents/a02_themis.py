"""A2 · Thémis, modération & conformité : masque les données personnelles puis classe.

Le masquage est fait par le programme AVANT tout appel au modèle : aucune donnée personnelle
détectable n'est envoyée à Claude."""

from __future__ import annotations

from ..core.dossier import Dossier
from ..core.texte import masquer
from .base import Agent


class Themis(Agent):
    id = "A2"
    prompt = "themis"

    def traiter(self, dossier: Dossier, ctx):
        brut = dossier.sorties["A1"]["texte"]
        texte_masque, compte = masquer(brut)
        avis = self.llm({"texte": texte_masque, "canal": dossier.contribution.canal}, dossier.id)
        decision = avis["decision"]
        if avis.get("donnees_personnelles_residuelles"):
            decision = "en_revue"  # garde-fou : rien ne passe avec une donnée personnelle visible
        if decision == "rejete" and avis["confiance"] < self.fiche["seuil_confiance"]:
            decision = "en_revue"  # jamais de rejet incertain : un humain tranche
        dossier.statut = {"publie": "publie", "en_revue": "revue_moderation", "rejete": "rejete"}[decision]
        return {**avis, "decision": decision, "texte_masque": texte_masque, "masquages": compte}

"""A4 · Hestia, regroupeur : propose des regroupements, ne fusionne jamais seule.
Deux idées de communes différentes ne sont jamais regroupées."""

from __future__ import annotations

from ..core.texte import cosinus, normaliser, vecteur
from .base import Agent


class Hestia(Agent):
    id = "A4"

    def traiter(self, dossier, ctx):
        seuil = self.fiche.get("seuil_similarite", 0.78)
        texte = dossier.texte_modere()
        v = vecteur(texte)
        commune = normaliser(dossier.contribution.commune or "")
        proches = []
        for autre in ctx.corpus:
            if autre.get("id") == dossier.id:
                continue
            if commune and normaliser(autre.get("commune") or "") not in ("", commune):
                continue
            sim = cosinus(v, autre.get("vecteur") or vecteur(autre.get("texte", "")))
            if sim >= seuil:
                proches.append({"id": autre["id"], "similarite": round(sim, 3)})
        proches.sort(key=lambda x: -x["similarite"])
        ctx.ajouter_au_corpus({"id": dossier.id, "texte": texte, "vecteur": v, "commune": dossier.contribution.commune})
        return {
            "idees_proches": proches[:10],
            "proposition_regroupement": bool(proches),
            "idees_regroupees": 1 + len(proches),
            "fusion_automatique": False,
            "seuil": seuil,
        }

"""Apollon, auditeur qualité : contrôle un échantillon (5 à 10 %) des dossiers traités."""

from __future__ import annotations

import random

from ..core.audit import journaliser
from .base import Agent

CHAMPS = ("A2", "A3", "A5", "A7", "A8")


class Apollon(Agent):
    id = "APOLLON"
    prompt = "apollon"

    def echantillon(self, dossiers: list[dict], graine: int | None = None) -> list[dict]:
        taux = self.fiche.get("echantillon", 0.08)
        k = max(1, round(len(dossiers) * taux)) if dossiers else 0
        return random.Random(graine).sample(dossiers, k)

    def auditer(self, dossier: dict) -> dict:
        s = dossier.get("sorties", {})
        a2 = s.get("A2") or {}
        donnees = {
            "texte_masque": a2.get("texte_masque"),
            "sorties": {
                k: {x: y for x, y in (s.get(k) or {}).items() if x not in ("texte_masque", "vecteur")} for k in CHAMPS
            },
        }
        sortie = self.llm(donnees, dossier["id"])
        journaliser(dossier["id"], self.id, "audit", verdict=sortie["verdict"], problemes=len(sortie["problemes"]))
        return sortie

    def rapport(self, dossiers: list[dict], graine: int | None = None) -> dict:
        resultats = [{"id": d["id"], **self.auditer(d)} for d in self.echantillon(dossiers, graine)]
        conformes = sum(1 for r in resultats if r["verdict"] == "conforme")
        return {
            "echantillon": len(resultats),
            "taux_conformite": round(conformes / max(1, len(resultats)), 3),
            "alerte": bool(resultats) and conformes / len(resultats) < 0.85,
            "details": resultats,
        }

    def traiter(self, dossier, ctx):
        return {}

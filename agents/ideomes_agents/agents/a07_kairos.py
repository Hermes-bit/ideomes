"""A7 · Kairos, priorisateur : le modèle note les 5 critères, le programme calcule le score
avec la grille publique. Même dossier et mêmes notes = même score (reproductible)."""

from __future__ import annotations

from ..core import scoring
from .base import Agent


class Kairos(Agent):
    id = "A7"
    prompt = "kairos"

    def traiter(self, dossier, ctx):
        a3, a4, a5 = dossier.sorties.get("A3", {}), dossier.sorties.get("A4", {}), dossier.sorties.get("A5", {})
        donnees = {
            "resume": a3.get("resume"),
            "categorie": a3.get("categorie"),
            "besoin_reel": a3.get("besoin_reel"),
            "niveau_competence": a3.get("niveau_competence"),
            "hors_competence": a3.get("hors_competence"),
            "idees_regroupees": a4.get("idees_regroupees", 1),
            "territoire": {k: (a5.get(k) or {}).get("nom") for k in ("region", "province", "commune")},
            "orientations_locales": ctx.orientations,
        }
        avis = self.llm(donnees, dossier.id)
        notes = {k: v["note"] for k, v in avis["criteres"].items()}
        base = scoring.score(notes, ctx.ponderations)
        bonus = 0.0
        commune = (a5.get("commune") or {}).get("nom")
        if commune and ctx.population and ctx.corpus:
            total_pop = sum(ctx.population.values()) or 1
            part_pop = ctx.population.get(commune, 0) / total_pop
            part_contrib = sum(1 for d in ctx.corpus if d.get("commune") == commune) / max(1, len(ctx.corpus))
            bonus = scoring.bonus_representativite(part_contrib, part_pop)
        dossier.statut = "en_attente_comite"
        return {
            **avis,
            "notes": notes,
            "score": base,
            "bonus_representativite": bonus,
            "score_affiche": min(100.0, base + bonus),
            "ponderations": ctx.ponderations or scoring.PONDERATIONS_DEFAUT,
            "formule": "20 × (0,30 I + 0,20 B + 0,20 U + 0,20 F + 0,10 A)",
        }

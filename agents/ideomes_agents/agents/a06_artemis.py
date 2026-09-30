"""A6 · Artémis, veilleur des tendances : travaille sur tout le corpus (tâche quotidienne),
pas dossier par dossier. Les chiffres sont calculés par le programme ; le modèle rédige."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta

from ..core.audit import journaliser
from .base import Agent


class Artemis(Agent):
    id = "A6"
    prompt = "artemis"

    def statistiques(self, corpus: list[dict], jours: int = 7, maintenant: datetime | None = None) -> dict:
        m = maintenant or datetime.now(UTC)
        debut, avant = m - timedelta(days=jours), m - timedelta(days=2 * jours)

        def cle(d):
            return (d.get("categorie") or "Autre", d.get("commune") or d.get("province") or "Non localisé")

        def date(d):
            return datetime.fromisoformat(d["date"].replace("Z", "+00:00"))

        actuel = Counter(cle(d) for d in corpus if date(d) >= debut)
        precedent = Counter(cle(d) for d in corpus if avant <= date(d) < debut)
        vmin = self.fiche.get("volume_minimum", 5)
        hausses = [
            {"theme": t, "territoire": z, "actuel": n, "precedent": precedent.get((t, z), 0)}
            for (t, z), n in actuel.items()
            if n >= vmin and n >= 2 * max(1, precedent.get((t, z), 0))
        ]
        return {
            "total": sum(actuel.values()),
            "hausses": sorted(hausses, key=lambda h: -h["actuel"]),
            "volume_minimum": vmin,
        }

    def veille(self, corpus: list[dict], **kw) -> dict:
        stats = self.statistiques(corpus, **kw)
        sortie = self.llm(stats, "corpus")
        journaliser("corpus", self.id, "note_hebdomadaire", alertes=len(sortie["alertes"]))
        return {**sortie, "statistiques": stats}

    def traiter(self, dossier, ctx):  # non utilisé dossier par dossier
        return {}

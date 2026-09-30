"""A3 · Athéna, analyste des besoins."""

from __future__ import annotations

from .base import Agent


class Athena(Agent):
    id = "A3"
    prompt = "athena"

    def traiter(self, dossier, ctx):
        c = dossier.contribution
        return self.llm(
            {
                "texte": dossier.texte_modere(),
                "domaine_declare": c.domaine_declare,
                "solution_proposee": c.solution_proposee,
            },
            dossier.id,
        )

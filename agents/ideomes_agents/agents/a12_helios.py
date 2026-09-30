"""A12 · Hélios, tableau de bord : agrégation déterministe. Chaque chiffre garde la liste
des dossiers sources (anonymisés) pour être cliquable jusqu'aux contributions."""

from __future__ import annotations

from collections import Counter, defaultdict

from .base import Agent


class Helios(Agent):
    id = "A12"

    def agreger(self, dossiers: list[dict]) -> dict:
        par_cat, par_commune, sources = Counter(), Counter(), defaultdict(list)
        revues = scores = 0
        top = []
        for d in dossiers:
            s = d.get("sorties", {})
            cat = s.get("A3", {}).get("categorie", "Autre")
            com = (s.get("A5", {}).get("commune") or {}).get("nom") or "Non localisé"
            par_cat[cat] += 1
            par_commune[com] += 1
            sources[f"categorie:{cat}"].append(d["id"])
            sources[f"commune:{com}"].append(d["id"])
            revues += 1 if d.get("revue_humaine") else 0
            if "A7" in s:
                scores += 1
                top.append(
                    {
                        "id": d["id"],
                        "resume": s.get("A3", {}).get("resume"),
                        "score": s["A7"]["score_affiche"],
                        "categorie": cat,
                        "commune": com,
                    }
                )
        n = len(dossiers) or 1
        return {
            "total": len(dossiers),
            "par_categorie": dict(par_cat),
            "par_commune": dict(par_commune),
            "top_priorites": sorted(top, key=lambda x: -x["score"])[:10],
            "qualite_ia": {"taux_revue_humaine": round(revues / n, 3), "dossiers_scores": scores},
            "sources": dict(sources),
        }

    def traiter(self, dossier, ctx):
        return {}

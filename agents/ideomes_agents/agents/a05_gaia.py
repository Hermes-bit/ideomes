"""A5 · Gaïa, analyste territorial : géocode sur le référentiel officiel et ajoute le contexte.
Pour l'affichage public, la position est arrondie au centre de la commune (vie privée)."""

from __future__ import annotations

from ..core import territoire as T
from .base import Agent


class Gaia(Agent):
    id = "A5"

    def traiter(self, dossier, ctx):
        c = dossier.contribution
        commune = T.trouver("c", c.commune, c.province) if c.commune else None
        province = T.trouver("p", c.province) or (T.trouver("p", commune["p"]) if commune else None)
        region = T.trouver("r", c.region) or (T.trouver("r", province["r"]) if province else None)
        if not (commune or province or region) and c.meta.get("lon") is not None:
            r = T.par_coordonnees(c.meta["lon"], c.meta["lat"])
            if r:
                commune, province, region = r["commune"], r["province"], r["region"]
        niveau = "commune" if commune else "province" if province else "region" if region else "aucun"
        plus_fin = T.fiche_publique(commune or province or region)
        pop = ctx.population.get(commune["n"]) if commune else None
        return {
            "region": T.fiche_publique(region),
            "province": T.fiche_publique(province),
            "commune": T.fiche_publique(commune),
            "precision": niveau,
            "geocode": niveau != "aucun",
            # position affichée publiquement : centre de l'unité administrative, jamais la position exacte
            "position_publique": {"lon": plus_fin["lon"], "lat": plus_fin["lat"]} if plus_fin else None,
            "population_commune": pop,
            "coherence": None if not (commune and province) else commune["p"] == province["n"],
        }

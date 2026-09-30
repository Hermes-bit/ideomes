"""Référentiel territorial du Burkina Faso (13 régions, 45 provinces, 351 communes).

Source des contours : geoBoundaries gbOpen BFA ADM1-ADM3 (domaine public), noms rattachés
par jointure spatiale ; codes HASC et GID GADM pour les jointures SIG.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .texte import normaliser

FICHIER = Path(__file__).resolve().parents[1] / "data" / "bf-limites.json"


@lru_cache
def referentiel() -> dict:
    d = json.loads(FICHIER.read_text(encoding="utf-8"))
    k, s, lon0, lat1 = d["K"], d["S"], d["LON0"], d["LAT1"]

    def anneaux(g):  # décode les anneaux (delta x10, projection plate) en lon/lat
        polys = []
        for poly in g:
            rings = []
            for a in poly:
                x = y = 0
                r = []
                for i in range(0, len(a), 2):
                    x += a[i]
                    y += a[i + 1]
                    r.append((round(x / 10 / (k * s) + lon0, 5), round(lat1 - y / 10 / s, 5)))
                rings.append(r)
            polys.append(rings)
        return polys

    for niveau in ("r", "p", "c"):
        for f in d[niveau]:
            f["polys"] = anneaux(f["g"])
    return d


def _dans(pt, anneau) -> bool:
    x, y = pt
    c = False
    j = len(anneau) - 1
    for i in range(len(anneau)):
        xi, yi = anneau[i]
        xj, yj = anneau[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def contient(f: dict, lon: float, lat: float) -> bool:
    return any(_dans((lon, lat), pg[0]) and not any(_dans((lon, lat), h) for h in pg[1:]) for pg in f["polys"])


def trouver(niveau: str, nom: str | None, parent: str | None = None) -> dict | None:
    if not nom:
        return None
    n = normaliser(nom)
    for f in referentiel()[niveau]:
        if normaliser(f["n"]) == n and (
            parent is None or normaliser(f.get("p") or f.get("r") or "") == normaliser(parent)
        ):
            return f
    return None


def par_coordonnees(lon: float, lat: float) -> dict | None:
    """Commune contenant un point (lon, lat), avec sa province et sa région."""
    for c in referentiel()["c"]:
        if contient(c, lon, lat):
            p = trouver("p", c["p"])
            return {"commune": c, "province": p, "region": trouver("r", p["r"]) if p else None}
    return None


def fiche_publique(f: dict | None) -> dict | None:
    if not f:
        return None
    return {
        "nom": f["n"],
        "hasc": f.get("hasc"),
        "gid": f.get("gid"),
        "shapeID": f.get("sid"),
        "iso": f.get("iso") or None,
        "lon": f["ll"][0],
        "lat": f["ll"][1],
    }

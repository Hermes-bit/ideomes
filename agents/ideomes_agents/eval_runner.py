"""Évaluation hors ligne : chaque agent est mesuré sur un jeu annoté avant tout changement de prompt ou de modèle.
Le jeu fourni est FICTIF et minimal ; remplacez-le par des contributions réelles annotées (anonymisées)."""

from __future__ import annotations

import json
from pathlib import Path

from .agents import TOUS
from .core.contexte import Contexte
from .core.dossier import Contribution, Dossier

JEU = Path(__file__).resolve().parents[1] / "eval" / "jeu_annote.jsonl"
SEUILS = {"A2": 0.95, "A3": 0.85}  # cf. KPI de la stratégie


def evaluer(chemin: str | None = None) -> dict:
    lignes = [json.loads(x) for x in Path(chemin or JEU).read_text(encoding="utf-8").splitlines() if x.strip()]
    ctx, ok, total, echecs = Contexte(), {"A2": 0, "A3": 0}, {"A2": 0, "A3": 0}, []
    a1, a2, a3 = TOUS["A1"](), TOUS["A2"](), TOUS["A3"]()
    for ligne in lignes:
        d = Dossier(id=ligne["id"], contribution=Contribution(texte=ligne["texte"], commune=ligne.get("commune")))
        a1.executer(d, ctx)
        s2 = a2.executer(d, ctx)
        att = ligne["attendu"]
        total["A2"] += 1
        obtenu = {"publie": "publie", "revue_moderation": "en_revue", "rejete": "rejete"}.get(
            d.statut, s2.get("decision")
        )
        ok["A2"] += obtenu == att["A2"]
        if obtenu != att["A2"]:
            echecs.append({"id": ligne["id"], "agent": "A2", "attendu": att["A2"], "obtenu": obtenu})
        if "A3" in att and d.statut == "publie":
            s3 = a3.executer(d, ctx)
            total["A3"] += 1
            ok["A3"] += s3["categorie"] == att["A3"]
            if s3["categorie"] != att["A3"]:
                echecs.append({"id": ligne["id"], "agent": "A3", "attendu": att["A3"], "obtenu": s3["categorie"]})
    taux = {k: round(ok[k] / total[k], 3) if total[k] else None for k in ok}
    return {
        "taux": taux,
        "seuils": SEUILS,
        "echecs": echecs,
        "reussite": all(taux[k] is None or taux[k] >= SEUILS[k] for k in SEUILS),
    }

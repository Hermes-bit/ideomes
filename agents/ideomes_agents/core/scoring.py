"""Grille de priorisation publique de Kairos (A7).

Score = 20 × (0,30 × Impact + 0,20 × Bénéficiaires + 0,20 × Urgence + 0,20 × Faisabilité + 0,10 × Alignement)
Chaque critère est noté de 0 à 5 ; le score est ramené sur 100.
Correctif de représentativité : bonus plafonné à +5 points, affiché séparément.
Les pondérations sont paramétrables par la collectivité mais doivent être publiées.
"""

from __future__ import annotations

PONDERATIONS_DEFAUT = {"impact": 0.30, "beneficiaires": 0.20, "urgence": 0.20, "faisabilite": 0.20, "alignement": 0.10}
BONUS_MAX = 5.0


def verifier(ponderations: dict[str, float]) -> None:
    if set(ponderations) != set(PONDERATIONS_DEFAUT):
        raise ValueError("Les cinq critères doivent tous être pondérés.")
    if abs(sum(ponderations.values()) - 1.0) > 1e-9:
        raise ValueError("La somme des pondérations doit valoir 1.")


def score(notes: dict[str, int], ponderations: dict[str, float] | None = None) -> float:
    p = ponderations or PONDERATIONS_DEFAUT
    verifier(p)
    for k, v in notes.items():
        if not 0 <= v <= 5:
            raise ValueError(f"Note hors échelle pour {k} : {v}")
    return round(20 * sum(p[k] * notes[k] for k in p), 1)


def bonus_representativite(part_contributions: float, part_population: float) -> float:
    """Bonus pour les territoires sous-représentés : proportionnel à l'écart, plafonné à +5."""
    if part_population <= 0 or part_contributions >= part_population:
        return 0.0
    ecart = (part_population - part_contributions) / part_population
    return round(min(BONUS_MAX, BONUS_MAX * ecart), 1)

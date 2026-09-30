"""Règles non négociables : masquage, score reproductible, garde-fous."""

from ideomes_agents.core import scoring
from ideomes_agents.core.texte import cosinus, masquer, vecteur


def test_masquage_donnees_personnelles():
    t, n = masquer("Écrivez à awa.kabore@mail.bf ou au +226 70 12 34 56, CNIB B12345678")
    assert "awa.kabore" not in t and "70 12 34 56" not in t
    assert n


def test_score_reproductible_et_borne():
    notes = {"impact": 4, "beneficiaires": 3, "urgence": 5, "faisabilite": 2, "alignement": 3}
    assert scoring.score(notes) == scoring.score(notes)
    assert 0 <= scoring.score(notes) <= 100
    assert scoring.score({k: 5 for k in notes}) == 100


def test_bonus_representativite_plafonne():
    assert scoring.bonus_representativite(0.001, 0.2) <= 5
    assert scoring.bonus_representativite(0.3, 0.1) == 0


def test_similarite():
    a = vecteur("pas d'eau potable dans le quartier, il faut un forage")
    b = vecteur("il faut un forage, pas d'eau potable au quartier")
    c = vecteur("la route du marché est coupée")
    assert cosinus(a, b) > cosinus(a, c)

"""Réponses simulées, déterministes, pour développer et tester sans appeler Claude.

Elles respectent les schémas de sortie ; les contenus sont volontairement simples et
marqués « [simulé] » pour ne jamais être confondus avec une vraie analyse.
"""

from __future__ import annotations

from typing import Any

from .texte import normaliser

CATEGORIES = {
    "Santé": ["sante", "hopital", "csps", "medecin", "malade", "paludisme", "pharmacie", "maternite"],
    "Éducation": ["ecole", "eleve", "enseignant", "classe", "cours", "bourse", "lycee"],
    "Agriculture & élevage": ["agricult", "semence", "recolte", "betail", "champ", "engrais", "pluie"],
    "Commerce & argent": ["mobile money", "orange money", "credit", "marche", "commerce", "prix"],
    "Transport": ["route", "taxi", "car ", "moto", "piste", "pont", "transport"],
    "Papiers & administration": ["acte", "naissance", "cnib", "mairie", "papier", "etat civil", "certificat"],
    "Eau & électricité": ["eau", "forage", "courant", "electricite", "delestage", "sonabel", "onea", "pompe"],
    "Emploi & formation": ["emploi", "travail", "stage", "formation", "chomage", "metier"],
    "Sécurité": ["securite", "vol", "agression", "eclairage", "insecurite"],
    "Logement": ["logement", "loyer", "parcelle", "maison", "construction"],
    "Culture & loisirs": ["culture", "sport", "musique", "terrain", "loisir"],
}
MOTS_TOXIQUES = ["idiot", "imbecile", "salaud", "tuer", "haine"]
MOTS_SPAM = ["promo", "gagnez", "cliquez", "achetez", "bitcoin", "http://", "https://"]
MOTS_URGENCE = ["urgent", "danger", "mort", "accident", "effondr", "inond", "grave", "enfant"]


def categorie(texte: str) -> str:
    t = normaliser(texte) + " "
    meilleure, score = "Autre", 0
    for cat, mots in CATEGORIES.items():
        s = sum(t.count(normaliser(m)) for m in mots)
        if s > score:
            meilleure, score = cat, s
    return meilleure


def simuler(agent: str, d: dict[str, Any]) -> dict[str, Any]:
    texte = d.get("texte") or d.get("resume") or ""
    t = normaliser(texte)
    if agent == "A2":
        injection = "ignore" in t and ("regle" in t or "instruction" in t or "consigne" in t)
        spam = any(m in t or m in texte.lower() for m in MOTS_SPAM)
        toxique = any(m in t for m in MOTS_TOXIQUES)
        decision = "rejete" if spam else ("en_revue" if toxique or injection else "publie")
        return {
            "decision": decision,
            "motifs": (
                ["Publicité ou spam"]
                if spam
                else ["Propos à vérifier par un modérateur"]
                if decision == "en_revue"
                else []
            ),
            "toxicite": "forte" if toxique else "aucune",
            "spam": spam,
            "donnees_personnelles_residuelles": [],
            "alertes": ["Tentative d'injection de consignes"] if injection else [],
            "confiance": 0.95 if spam else 0.9 if decision == "publie" else 0.6,
        }
    if agent == "A3":
        cat = categorie(texte + " " + (d.get("domaine_declare") or ""))
        court = len(t.split()) < 6
        return {
            "resume": f"[simulé] {texte[:180]}",
            "categorie": cat,
            "besoin_reel": f"[simulé] Besoin lié à : {cat.lower()}.",
            "dit_explicitement": [texte[:120]],
            "deduit": [],
            "causes": [],
            "consequences": [],
            "acteurs": ["Mairie"],
            "niveau_competence": "commune",
            "hors_competence": False,
            **(
                {"question_au_contributeur": "Pouvez-vous préciser le lieu et la fréquence du problème ?"}
                if court
                else {}
            ),
            "alertes": [],
            "confiance": 0.55 if court else 0.85,
        }
    if agent == "A7":
        urg = 4 if any(m in t for m in MOTS_URGENCE) else 2
        nb = int(d.get("idees_regroupees") or 1)
        ben = min(5, 1 + nb // 3)
        return {
            "criteres": {
                "impact": {
                    "note": 3 + (1 if urg >= 4 else 0),
                    "justification": "[simulé] Impact estimé selon la catégorie.",
                },
                "beneficiaires": {"note": ben, "justification": f"[simulé] {nb} contribution(s) convergente(s)."},
                "urgence": {
                    "note": urg,
                    "justification": "[simulé] Mots signalant un danger."
                    if urg >= 4
                    else "[simulé] Pas d'échéance signalée.",
                },
                "faisabilite": {"note": 3, "justification": "[simulé] Compétence communale, coût modéré."},
                "alignement": {"note": 2, "justification": "[simulé] Aucun plan local fourni."},
            },
            "justification": "[simulé] Score indicatif calculé à partir de la grille publique.",
            "confiance": 0.8,
        }
    if agent == "A8":
        return {
            "pistes": [
                {
                    "titre": "[simulé] Solution rapide à faible coût",
                    "description": "Mesure provisoire mise en place par la commune.",
                    "cout_estime": {"min_fcfa": 100000, "max_fcfa": 500000, "estime": True},
                    "delai": "1 à 3 mois",
                    "acteurs": ["Mairie"],
                    "exemples_ailleurs": [],
                    "risques": ["Solution temporaire"],
                    "faible_cout": True,
                    "sources": ["estimation interne"],
                },
                {
                    "titre": "[simulé] Solution durable",
                    "description": "Aménagement pérenne avec un partenaire technique.",
                    "cout_estime": {"min_fcfa": 5000000, "max_fcfa": 20000000, "estime": True},
                    "delai": "6 à 12 mois",
                    "acteurs": ["Mairie", "Région"],
                    "exemples_ailleurs": [],
                    "risques": ["Financement à trouver"],
                    "faible_cout": False,
                    "sources": ["estimation interne"],
                },
            ],
            "confiance": 0.75,
        }
    if agent == "A9":
        return {
            "titre": "[simulé] " + (d.get("piste") or {}).get("titre", "Projet"),
            "objectifs": ["Répondre au besoin exprimé"],
            "etapes": [
                {"intitule": "Étude et devis", "jalon": "Devis validé", "duree": "1 mois"},
                {"intitule": "Réalisation", "jalon": "Réception des travaux", "duree": "2 mois"},
            ],
            "budget": {
                "montant_fcfa": int(((d.get("piste") or {}).get("cout_estime") or {}).get("max_fcfa", 0)),
                "estime": True,
            },
            "responsables": ["Service technique de la mairie"],
            "indicateurs_reussite": ["Réalisation constatée", "Satisfaction des habitants ≥ 4/5"],
        }
    if agent == "A10":
        ev = d.get("evenement", "accuse")
        msgs = {
            "accuse": "Merci, votre idée a bien été reçue. Nous vous tiendrons informé de chaque étape.",
            "regroupement": "Bonne nouvelle : d'autres habitants ont exprimé un besoin proche du vôtre. Vos idées sont désormais suivies ensemble.",
            "decision_valide": "Le comité a retenu votre idée pour étude. Nous vous informerons de la suite.",
            "decision_non_retenu": "Le comité n'a pas retenu votre idée pour le moment. Motif : "
            + str(d.get("motif") or "non précisé")
            + ".",
            "rejet": "Votre contribution n'a pas pu être publiée. Motif : "
            + str(d.get("motif") or "non précisé")
            + ". Vous pouvez la reformuler.",
        }
        return {
            "message": "[simulé] " + msgs.get(ev, msgs["accuse"]) + " (Réponse rédigée avec l'aide de l'IA)",
            "sensible": ev in ("rejet", "decision_non_retenu"),
            "canal": d.get("canal", "whatsapp"),
        }
    if agent == "A6":
        al = [
            {
                "theme": x["theme"],
                "territoire": x["territoire"],
                "evolution": f"{x['precedent']} → {x['actuel']}",
                "message": f"[simulé] {x['theme']} à {x['territoire']} : {x['actuel']} contributions contre {x['precedent']}.",
            }
            for x in d.get("hausses", [])
        ]
        return {"note_hebdomadaire": f"[simulé] {d.get('total', 0)} contributions sur la période.", "alertes": al}
    if agent == "A11":
        return {
            "objectifs_atteints": [
                {"objectif": o, "atteint": "inconnu", "preuve": "[simulé] Donnée à relever"}
                for o in (d.get("objectifs") or ["Objectif"])
            ],
            "beneficiaires": {"nombre": None, "nature": "inconnu"},
            "cout_reel_fcfa": d.get("cout_reel_fcfa"),
            "satisfaction": d.get("satisfaction"),
            "enseignements": ["[simulé] Relever les indicateurs à 6 mois."],
            "mesure_vs_estime": "[simulé] Aucune mesure fournie : tout reste à mesurer.",
        }
    if agent == "APOLLON":
        return {"verdict": "conforme", "problemes": [], "confiance": 0.8}
    if agent == "HERMES":
        return {"propositions": [], "message": "[simulé] Aucune recherche web en mode simulé."}
    raise KeyError(f"Pas de simulation pour {agent}")

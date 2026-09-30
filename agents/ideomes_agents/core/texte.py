"""Outils de texte : masquage des données personnelles, normalisation, vecteurs légers."""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata

# Téléphones du Burkina (+226, 8 chiffres) et internationaux, e-mails, numéros CNIB, IBAN
MOTIFS = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("TELEPHONE", re.compile(r"(?:\+|00)\d{1,3}[\s.-]?(?:\d[\s.-]?){7,11}\d|\b(?:\d{2}[\s.-]?){3}\d{2}\b")),
    ("CNIB", re.compile(r"\bB\d{7,9}\b", re.I)),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}\b")),
]


def masquer(texte: str) -> tuple[str, dict[str, int]]:
    """Remplace les données personnelles détectables par des étiquettes. Renvoie le texte et le décompte."""
    compte: dict[str, int] = {}
    for etiquette, motif in MOTIFS:
        texte, n = motif.subn(f"[{etiquette}]", texte)
        if n:
            compte[etiquette] = compte.get(etiquette, 0) + n
    return texte, compte


def normaliser(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


MOTS_VIDES = set(
    [
        "le",
        "la",
        "les",
        "un",
        "une",
        "des",
        "de",
        "du",
        "d",
        "l",
        "et",
        "ou",
        "a",
        "au",
        "aux",
        "en",
        "dans",
        "pour",
        "par",
        "sur",
        "avec",
        "sans",
        "que",
        "qui",
        "quoi",
        "ce",
        "cet",
        "cette",
        "ces",
        "il",
        "elle",
        "ils",
        "elles",
        "nous",
        "vous",
        "on",
        "je",
        "tu",
        "me",
        "te",
        "se",
        "mon",
        "ma",
        "mes",
        "notre",
        "nos",
        "votre",
        "vos",
        "leur",
        "leurs",
        "est",
        "sont",
        "etre",
        "avoir",
        "ai",
        "a",
        "ont",
        "fait",
        "faire",
        "plus",
        "tres",
        "pas",
        "ne",
        "n",
        "y",
        "tout",
        "tous",
    ]
)


def vecteur(texte: str, dim: int = 512) -> list[float]:
    """Vecteur « sac de mots haché » normalisé : suffisant pour détecter des doublons proches
    sans service externe. À remplacer par de vrais embeddings (pgvector) en production."""
    v = [0.0] * dim
    mots = [m for m in normaliser(texte).split() if m not in MOTS_VIDES and len(m) > 2]
    for i, m in enumerate(mots):
        for jeton in (m, m[:5]) + ((mots[i - 1] + "_" + m,) if i else ()):
            h = int(hashlib.md5(jeton.encode()).hexdigest(), 16)
            v[h % dim] += 1.0 if jeton == m else 0.5
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def cosinus(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=False))

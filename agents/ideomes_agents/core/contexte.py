"""Ce que les agents peuvent consulter hors du dossier : le corpus, les orientations locales,
la population par territoire, et la sortie des notifications. L'API fournit une version reliée
à la base ; la version mémoire sert aux tests et à la démo."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Contexte:
    corpus: list[dict[str, Any]] = field(default_factory=list)  # dossiers déjà analysés
    orientations: list[str] = field(default_factory=list)  # plans et programmes locaux
    population: dict[str, int] = field(default_factory=dict)  # par commune (INSD)
    ponderations: dict[str, float] | None = None  # grille Kairos publiée
    envoyer: Callable[[dict[str, Any]], None] = lambda message: None  # sortie d'Iris (file d'envoi)
    a_relire: Callable[[dict[str, Any]], None] = lambda message: None  # messages sensibles

    def ajouter_au_corpus(self, dossier: dict[str, Any]) -> None:
        self.corpus.append(dossier)


CONTEXTE_DEMO = Contexte()

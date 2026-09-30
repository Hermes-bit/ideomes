"""Le « dossier » d'une idée : la mémoire partagée entre les agents.

Chaque agent lit le dossier et n'écrit que dans son propre champ de `sorties`.
Chaque décision est historisée (traçabilité).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Statut = Literal[
    "recu",
    "en_moderation",
    "revue_moderation",
    "rejete",
    "publie",
    "analyse",
    "revue_humaine",
    "en_attente_comite",
    "valide_comite",
    "non_retenu",
    "en_projet",
    "realise",
    "evalue",
    "erreur",
]


def maintenant() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class Evenement(BaseModel):
    date: str = Field(default_factory=maintenant)
    agent: str
    action: str
    detail: dict[str, Any] = Field(default_factory=dict)


class Contribution(BaseModel):
    """Contribution brute telle qu'elle arrive d'un canal."""

    texte: str
    canal: Literal["web", "appli", "vocal", "sms", "papier", "atelier", "whatsapp"] = "web"
    domaine_declare: str | None = None
    solution_proposee: str | None = None
    region: str | None = None
    province: str | None = None
    commune: str | None = None
    langue: str | None = None
    auteur_id: str | None = None  # identifiant opaque, jamais le nom
    consentement_rgpd: bool = False
    consentement_contact: bool = False
    pieces_jointes: list[str] = Field(default_factory=list)
    recu_le: str = Field(default_factory=maintenant)
    meta: dict[str, Any] = Field(default_factory=dict)


class Dossier(BaseModel):
    id: str
    contribution: Contribution
    statut: Statut = "recu"
    sorties: dict[str, dict[str, Any]] = Field(default_factory=dict)
    historique: list[Evenement] = Field(default_factory=list)
    revue_humaine: dict[str, Any] | None = None  # motif, agent, seuil
    decision_comite: dict[str, Any] | None = None  # décision, validateur, date, commentaire

    def trace(self, agent: str, action: str, **detail: Any) -> None:
        self.historique.append(Evenement(agent=agent, action=action, detail=detail))

    def texte_modere(self) -> str:
        """Texte à analyser : toujours la version masquée par Thémis (A2)."""
        return (self.sorties.get("A2") or {}).get("texte_masque") or ""

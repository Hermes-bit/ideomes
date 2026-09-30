"""Identité et règles d'accès.

DÉVELOPPEMENT : l'identité vient de l'en-tête X-Dev-User (posé par le shim web). Ce n'est PAS une
authentification : avant toute mise en ligne, remplacez `identite()` par une vraie connexion
(code WhatsApp / e-mail, sessions signées). Voir docs/conformite.md.

Règles (reprises de l'artefact) :
- le propriétaire (administrateur Geomessen) lit et écrit tout ;
- un participant lit `actus/*` et `config/video`, lit et écrit SES documents `reponses/<uid>` et `connexions/<uid>` ;
- `adminconf/*`, `veille/*`, `config/hermes` et les dossiers d'agents sont réservés au propriétaire.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException

from .config import reglages


@dataclass
class Identite:
    uid: str
    proprietaire: bool
    service: bool = False


def identite(
    x_dev_user: str | None = Header(default=None), x_service_token: str | None = Header(default=None)
) -> Identite:
    if x_service_token:
        if x_service_token != reglages.api_jeton_service:
            raise HTTPException(401, "Jeton de service invalide")
        return Identite("service", True, True)
    uid = (x_dev_user or reglages.proprietaire_uid).strip()[:100]
    return Identite(uid, uid == reglages.proprietaire_uid)


PUBLIC_LECTURE = {("config", "video")}
PUBLIC_COLLECTIONS = {"actus"}
PERSONNELLES = {"reponses", "connexions"}


def peut_lire(qui: Identite, collection: str, doc_id: str | None = None) -> bool:
    if qui.proprietaire:
        return True
    if collection in PUBLIC_COLLECTIONS:
        return True
    if doc_id is None:
        return False
    return (collection, doc_id) in PUBLIC_LECTURE or (collection in PERSONNELLES and doc_id == qui.uid)


def peut_ecrire(qui: Identite, collection: str, doc_id: str) -> bool:
    return qui.proprietaire or (collection in PERSONNELLES and doc_id == qui.uid)


def exiger_proprietaire(qui: Identite) -> None:
    if not qui.proprietaire:
        raise HTTPException(403, "Réservé à l'administrateur")

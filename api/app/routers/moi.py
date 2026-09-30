"""Équivalent de la capacité `user` de l'artefact."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session as S

from ..base import Document, session
from ..config import reglages
from ..securite import Identite, identite

r = APIRouter(prefix="/api", tags=["identité"])


def _profil(uid: str, s: S) -> dict:
    c = s.get(Document, ("connexions", uid))
    d = (c.data if c else {}) or {}
    nom = (
        "Administrateur Geomessen"
        if uid == reglages.proprietaire_uid or d.get("type") == "admin"
        else (d.get("valeur") or "Participant " + uid.removeprefix("u_")[:8])
    )
    return {"id": uid, "name": nom, "avatarUrl": None}


@r.get("/me")
def moi(qui: Identite = Depends(identite), s: S = Depends(session)):
    return {**_profil(qui.uid, s), "isOwner": qui.proprietaire}


class Ids(BaseModel):
    ids: list[str]


@r.post("/profiles")
def profils(corps: Ids, qui: Identite = Depends(identite), s: S = Depends(session)):
    if not qui.proprietaire:
        return {qui.uid: _profil(qui.uid, s)} if qui.uid in corps.ids else {}
    return {i: _profil(i, s) for i in corps.ids[:500]}

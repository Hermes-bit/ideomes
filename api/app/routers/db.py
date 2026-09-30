"""Base documentaire : même modèle que l'artefact (collections / documents JSON)."""

from __future__ import annotations

import secrets
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session as S

from .. import pipeline
from ..base import Document, session
from ..securite import Identite, identite, peut_ecrire, peut_lire

r = APIRouter(prefix="/api/db", tags=["base"])


class Corps(BaseModel):
    data: dict[str, Any]


def _vue(d: Document | None, doc_id: str) -> dict:
    return {"id": doc_id, "exists": d is not None, "data": d.data if d else None, "version": d.version if d else None}


def _fusion(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and v.get("__delete__") is True:
            out.pop(k, None)
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _fusion(out[k], v)
        else:
            out[k] = v
    return out


@r.get("/doc/{collection}/{doc_id}")
def lire(collection: str, doc_id: str, qui: Identite = Depends(identite), s: S = Depends(session)):
    if not peut_lire(qui, collection, doc_id):
        raise HTTPException(403, "Lecture non autorisée")
    return _vue(s.get(Document, (collection, doc_id)), doc_id)


def _ecrire(collection: str, doc_id: str, data: dict, qui: Identite, s: S, fusion: bool) -> dict:
    if not peut_ecrire(qui, collection, doc_id):
        raise HTTPException(403, "Écriture non autorisée")
    d = s.get(Document, (collection, doc_id))
    avant = dict(d.data) if d else None
    if d:
        d.data = _fusion(d.data, data) if fusion else data
        d.version += 1
        d.modifie_par = qui.uid
    else:
        d = Document(collection=collection, doc_id=doc_id, data=data, version=1, modifie_par=qui.uid)
        s.add(d)
    s.commit()
    if collection == "reponses":
        pipeline.sur_ecriture_reponses(doc_id, avant, d.data)
    return _vue(d, doc_id)


@r.put("/doc/{collection}/{doc_id}")
def remplacer(collection: str, doc_id: str, corps: Corps, qui: Identite = Depends(identite), s: S = Depends(session)):
    return _ecrire(collection, doc_id, corps.data, qui, s, fusion=False)


@r.patch("/doc/{collection}/{doc_id}")
def fusionner(collection: str, doc_id: str, corps: Corps, qui: Identite = Depends(identite), s: S = Depends(session)):
    return _ecrire(collection, doc_id, corps.data, qui, s, fusion=True)


@r.post("/collection/{collection}")
def ajouter(collection: str, corps: Corps, qui: Identite = Depends(identite), s: S = Depends(session)):
    return _ecrire(collection, secrets.token_hex(10), corps.data, qui, s, fusion=False)


@r.delete("/doc/{collection}/{doc_id}")
def supprimer(collection: str, doc_id: str, qui: Identite = Depends(identite), s: S = Depends(session)):
    if not peut_ecrire(qui, collection, doc_id):
        raise HTTPException(403, "Suppression non autorisée")
    d = s.get(Document, (collection, doc_id))
    if d:
        s.delete(d)
        s.commit()
    return {"deleted": d is not None}


@r.get("/collection/{collection}")
def lister(collection: str, qui: Identite = Depends(identite), s: S = Depends(session)):
    if not peut_lire(qui, collection):
        raise HTTPException(403, "Lecture non autorisée")
    docs = s.scalars(select(Document).where(Document.collection == collection)).all()
    return {"docs": [{"id": d.doc_id, "data": d.data, "version": d.version} for d in docs]}

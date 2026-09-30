"""Équivalent de la capacité `assets` : fichiers (vidéo, images) servis sous /_blob/<id>."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as S

from ..base import Asset, session
from ..config import reglages
from ..securite import Identite, exiger_proprietaire, identite

r = APIRouter(tags=["fichiers"])
TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
    "image/svg+xml",
    "video/mp4",
    "video/webm",
    "application/pdf",
}
MAX = 200 * 1024 * 1024


@r.post("/api/assets")
async def televerser(
    fichier: UploadFile = File(...),
    type: str | None = Form(None),
    qui: Identite = Depends(identite),
    s: S = Depends(session),
):
    exiger_proprietaire(qui)
    ct = (type or fichier.content_type or "").split(";")[0].strip()
    if ct not in TYPES:
        raise HTTPException(415, f"Type non accepté : {ct}")
    contenu = await fichier.read()
    if not contenu or len(contenu) > MAX:
        raise HTTPException(413, "Fichier vide ou trop gros")
    aid = secrets.token_hex(16)
    reglages.dossier_blobs.mkdir(parents=True, exist_ok=True)
    (reglages.dossier_blobs / aid).write_bytes(contenu)
    s.add(Asset(id=aid, content_type=ct, taille=len(contenu)))
    s.commit()
    return {"id": aid, "url": f"/_blob/{aid}", "sizeBytes": len(contenu), "contentType": ct}


@r.get("/api/assets")
def lister(qui: Identite = Depends(identite), s: S = Depends(session)):
    exiger_proprietaire(qui)
    a = s.query(Asset).order_by(Asset.cree_le).all()
    return {
        "assets": [
            {
                "id": x.id,
                "url": f"/_blob/{x.id}",
                "contentType": x.content_type,
                "sizeBytes": x.taille,
                "createdAt": x.cree_le.isoformat(),
            }
            for x in a
        ],
        "usage": {"files": len(a), "bytes": sum(x.taille for x in a)},
    }


@r.delete("/api/assets/{aid}")
def supprimer(aid: str, qui: Identite = Depends(identite), s: S = Depends(session)):
    exiger_proprietaire(qui)
    a = s.get(Asset, aid)
    if a:
        (reglages.dossier_blobs / aid).unlink(missing_ok=True)
        s.delete(a)
        s.commit()
    return {"deleted": a is not None}


@r.get("/_blob/{aid}")
def servir(aid: str, s: S = Depends(session)):
    a = s.get(Asset, aid)
    chemin = reglages.dossier_blobs / aid
    if not a or not chemin.exists():
        raise HTTPException(404)
    return FileResponse(chemin, media_type=a.content_type)

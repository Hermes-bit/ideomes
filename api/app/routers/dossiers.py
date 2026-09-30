"""Dossiers d'agents : suivi du pipeline et décisions humaines (modérateur, analyste, comité)."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session as S

from .. import pipeline
from ..base import DossierIdee, JournalAudit, session
from ..securite import Identite, exiger_proprietaire, identite

r = APIRouter(tags=["agents"])


@r.get("/api/dossiers")
def lister(statut: str | None = None, qui: Identite = Depends(identite), s: S = Depends(session)):
    exiger_proprietaire(qui)
    q = select(DossierIdee).order_by(DossierIdee.cree_le.desc())
    if statut:
        q = q.where(DossierIdee.statut == statut)
    return [
        {
            "id": d.id,
            "statut": d.statut,
            "en_attente_de": d.en_attente_de,
            "cree_le": d.cree_le,
            "score": ((d.etat.get("sorties") or {}).get("A7") or {}).get("score"),
            "resume": ((d.etat.get("sorties") or {}).get("A3") or {}).get("resume"),
        }
        for d in s.scalars(q)
    ]


@r.get("/api/synthese")
def helios(qui: Identite = Depends(identite), s: S = Depends(session)):
    """Hélios (A12) : vue agrégée pour les décideurs ; chaque chiffre renvoie à ses sources."""
    exiger_proprietaire(qui)
    from ideomes_agents.agents import TOUS

    dossiers = [
        {"id": d.id, "statut": d.statut, **(d.etat.get("sorties") or {})} for d in s.scalars(select(DossierIdee))
    ]
    return TOUS["A12"]().agreger(dossiers)


@r.get("/api/dossiers/{did}")
def lire(did: str, qui: Identite = Depends(identite), s: S = Depends(session)):
    exiger_proprietaire(qui)
    d = s.get(DossierIdee, did)
    if not d:
        raise HTTPException(404)
    journal = s.scalars(select(JournalAudit).where(JournalAudit.dossier_id == did).order_by(JournalAudit.id)).all()
    return {
        "id": d.id,
        "statut": d.statut,
        "en_attente_de": d.en_attente_de,
        "etat": d.etat,
        "journal": [{"date": j.date, "agent": j.agent, "evenement": j.evenement, **j.infos} for j in journal],
    }


class Decision(BaseModel):
    point: Literal["moderation_humaine", "revue_humaine", "comite"]
    decision: str  # publie | rejete | ok | valide | non_retenu
    commentaire: str = ""
    piste_retenue: int = 0


@r.post("/api/dossiers/{did}/decision")
def decider(did: str, corps: Decision, qui: Identite = Depends(identite)):
    exiger_proprietaire(qui)
    try:
        return pipeline.decider(did, validateur=qui.uid, **corps.model_dump())
    except ValueError as e:
        raise HTTPException(409, str(e)) from e

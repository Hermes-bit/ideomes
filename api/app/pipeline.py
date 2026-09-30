"""Pont entre l'appli et les agents : chaque nouvelle idée enregistrée dans `reponses/<uid>`
devient un dossier traité par Zeus. Les points de validation humaine se règlent via /api/dossiers.

Persistance du graphe : SQLite (data/checkpoints.db) en local ; en production, remplacez par
`langgraph.checkpoint.postgres.PostgresSaver` sur la même base PostgreSQL.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from ideomes_agents.core import audit
from ideomes_agents.core.contexte import Contexte
from ideomes_agents.core.dossier import Contribution
from ideomes_agents.orchestrateur import Zeus

from .base import Document, DossierIdee, JournalAudit, Session
from .config import RACINE, reglages

log = logging.getLogger("ideomes.pipeline")
_verrou = threading.Lock()
_zeus: Zeus | None = None
_executeur = ThreadPoolExecutor(max_workers=2, thread_name_prefix="zeus")

CANAUX = {"whatsapp": "whatsapp", "email": "web", "invite": "web", "admin": "web"}


def _journal_en_base(ligne: dict) -> None:
    with Session() as s:
        s.add(
            JournalAudit(
                dossier_id=str(ligne.get("dossier_id")),
                agent=str(ligne.get("agent")),
                evenement=str(ligne.get("evenement")),
                infos={k: v for k, v in ligne.items() if k not in ("dossier_id", "agent", "evenement", "date")},
            )
        )
        s.commit()


def _file_iris(message: dict) -> None:
    """File d'envoi d'Iris : documents `notifications/*` que le connecteur WhatsApp / e-mail consommera."""
    with Session() as s:
        s.merge(
            Document(
                collection="notifications",
                doc_id=f"{message['dossier']}-{message['evenement']}",
                data=message,
                modifie_par="A10",
            )
        )
        s.commit()


def contexte() -> Contexte:
    with Session() as s:
        corpus = [{"id": d.id, **(d.etat.get("sorties") or {})} for d in s.query(DossierIdee).limit(2000)]
    return Contexte(corpus=corpus, envoyer=_file_iris, a_relire=lambda m: _file_iris({**m, "statut_envoi": "a_relire"}))


def zeus() -> Zeus:
    global _zeus
    with _verrou:
        if _zeus is None:
            try:
                from langgraph.checkpoint.sqlite import SqliteSaver

                (RACINE / "data").mkdir(exist_ok=True)
                cp = SqliteSaver(sqlite3.connect(RACINE / "data" / "checkpoints.db", check_same_thread=False))
            except ImportError:  # paquet optionnel
                from langgraph.checkpoint.memory import MemorySaver

                cp = MemorySaver()
            _zeus = Zeus(contexte(), checkpointer=cp)
            audit.abonner(_journal_en_base)
        return _zeus


def vers_contribution(uid: str, item: dict, type_identite: str) -> Contribution:
    texte = (item.get("probleme") or "").strip()
    return Contribution(
        texte=texte,
        canal=CANAUX.get(type_identite, "web"),
        domaine_declare=item.get("domaine") or None,
        solution_proposee=item.get("solution") or None,
        region=item.get("region") or None,
        province=item.get("province") or None,
        commune=item.get("ville") or None,
        langue=item.get("langue") or None,
        auteur_id=uid,
        consentement_rgpd=bool((item.get("consentement") or {}).get("rgpd")),
        consentement_contact=bool(item.get("aContact")),
        meta={k: item.get(k) for k in ("lon", "lat", "geoPrecision", "frequence", "importance", "age")},
    )


def enregistrer(dossier_id: str, etat: dict) -> None:
    with Session() as s:
        d = s.get(DossierIdee, dossier_id)
        if d:
            d.statut, d.en_attente_de, d.etat = etat.get("statut", "recu"), etat.get("en_attente_de", []), etat
            s.commit()


def traiter(uid: str, item: dict) -> None:
    did = item["id"]
    try:
        z = zeus()
        z.ctx.corpus = contexte().corpus
        etat = z.lancer(did, vers_contribution(uid, item, (item.get("identite") or {}).get("type", "invite")))
        enregistrer(did, etat)
    except Exception as e:  # le dossier reste visible, en erreur, pour reprise manuelle
        log.exception("Échec du pipeline pour %s", did)
        with Session() as s:
            d = s.get(DossierIdee, did)
            if d:
                d.statut, d.etat = "erreur", {**(d.etat or {}), "erreur": str(e)}
                s.commit()


def nouvelles_idees(uid: str, avant: dict | None, apres: dict) -> list[dict]:
    anciens = {x.get("id") for x in (avant or {}).get("items", [])}
    return [
        x
        for x in apres.get("items", [])
        if x.get("id") and x["id"] not in anciens and (x.get("probleme") or "").strip()
    ]


def sur_ecriture_reponses(uid: str, avant: dict | None, apres: dict, synchrone: bool = False) -> list[str]:
    """Appelé par le routeur db à chaque écriture de `reponses/<uid>`."""
    nouvelles = nouvelles_idees(uid, avant, apres)
    if not reglages.pipeline_auto:
        return []
    ids = []
    with Session() as s:
        for item in nouvelles:
            if not s.get(DossierIdee, item["id"]):
                s.add(DossierIdee(id=item["id"], auteur_uid=uid, statut="recu", etat={}))
                ids.append(item["id"])
        s.commit()
    for item in nouvelles:
        if item["id"] in ids:
            (traiter(uid, item) if synchrone else _executeur.submit(traiter, uid, item))
    return ids


def decider(dossier_id: str, **kw: Any) -> dict:
    etat = zeus().decider(dossier_id, **kw)
    enregistrer(dossier_id, etat)
    return etat

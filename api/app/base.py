"""Stockage : SQLite par défaut (zéro installation), PostgreSQL + pgvector avec docker compose.

Le modèle « document » reproduit la base de l'artefact claude.ai (collections et documents JSON),
ce qui permet à l'application web de tourner sans modification. Les dossiers d'agents et le
journal d'audit ont leurs propres tables.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .config import reglages


def maintenant() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"
    collection: Mapped[str] = mapped_column(String(200), primary_key=True)
    doc_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    modifie_par: Mapped[str | None] = mapped_column(String(100))
    modifie_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant, onupdate=maintenant)


class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(100))
    taille: Mapped[int] = mapped_column(Integer)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)


class DossierIdee(Base):
    """Un dossier par idée : l'état complet du graphe de Zeus (sorties de chaque agent, historique)."""

    __tablename__ = "dossiers"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # = id de l'idée dans l'appli
    auteur_uid: Mapped[str] = mapped_column(String(100), index=True)
    statut: Mapped[str] = mapped_column(String(40), index=True)
    en_attente_de: Mapped[list] = mapped_column(JSON, default=list)
    etat: Mapped[dict] = mapped_column(JSON, default=dict)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant)
    modifie_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant, onupdate=maintenant)


class JournalAudit(Base):
    __tablename__ = "journal_audit"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=maintenant, index=True)
    dossier_id: Mapped[str] = mapped_column(String(64), index=True)
    agent: Mapped[str] = mapped_column(String(40))
    evenement: Mapped[str] = mapped_column(String(60))
    infos: Mapped[dict] = mapped_column(JSON, default=dict)


moteur = create_engine(
    reglages.database_url,
    future=True,
    connect_args={"check_same_thread": False} if reglages.database_url.startswith("sqlite") else {},
)
Session = sessionmaker(moteur, expire_on_commit=False)


def initialiser() -> None:
    if reglages.database_url.startswith("sqlite"):
        from pathlib import Path

        Path(reglages.database_url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    reglages.dossier_blobs.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(moteur)


def session():
    with Session() as s:
        yield s

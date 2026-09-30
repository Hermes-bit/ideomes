"""Zeus, l'orchestrateur : graphe d'états LangGraph.

    Déméter → Thémis ─┬─ rejeté ──────────────→ Iris (motif) → fin
                      ├─ en revue → [MODÉRATEUR HUMAIN] ─┐
                      └─ publié → Iris (accusé) ─────────┴→ Athéna ─┬→ Hestia ─┐
                                                                    └→ Gaïa ───┴→ Kairos
    Kairos ─┬─ confiance basse → [REVUE HUMAINE] ─┐
            └─────────────────────────────────────┴→ Héphaïstos → [COMITÉ] ─┬─ validé → Héra → Iris → fin
                                                                           └─ non retenu → Iris → fin

Les trois points marqués [..] sont des interruptions : le graphe s'arrête et attend une décision
humaine tracée (cf. stratégie v2 : modérateur, comité, relecture). Hestia et Gaïa tournent en parallèle.
"""

from __future__ import annotations

import operator
from collections.abc import Callable
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .agents import TOUS
from .agents.a09_hera import ValidationManquante
from .core.audit import journaliser
from .core.contexte import Contexte
from .core.dossier import Contribution, Dossier, maintenant
from .core.llm import ErreurAgent


def _fusion(a: dict, b: dict) -> dict:
    return {**(a or {}), **(b or {})}


def _dernier(a, b):
    return b if b is not None else a


class Etat(TypedDict, total=False):
    dossier_id: str
    contribution: dict
    statut: Annotated[str, _dernier]
    sorties: Annotated[dict, _fusion]
    historique: Annotated[list, operator.add]
    erreurs: Annotated[list, operator.add]
    revue_humaine: Annotated[dict | None, _dernier]
    decision_moderation: Annotated[dict | None, _dernier]
    decision_comite: Annotated[dict | None, _dernier]


def vers_dossier(etat: Etat) -> Dossier:
    return Dossier(
        id=etat["dossier_id"],
        contribution=Contribution(**etat["contribution"]),
        statut=etat.get("statut") or "recu",
        sorties=dict(etat.get("sorties") or {}),
        revue_humaine=etat.get("revue_humaine"),
        decision_comite=etat.get("decision_comite"),
    )


class Zeus:
    """Construit et pilote le graphe. Une instance par processus (API ou CLI)."""

    POINTS_HUMAINS = ["moderation_humaine", "revue_humaine", "comite"]

    def __init__(self, ctx: Contexte | None = None, checkpointer=None) -> None:
        self.ctx = ctx or Contexte()
        self.agents = {k: v() for k, v in TOUS.items()}
        self.graphe = self._construire().compile(
            checkpointer=checkpointer or MemorySaver(), interrupt_before=self.POINTS_HUMAINS
        )

    # ---------- nœuds -------------------------------------------------------------------------
    def _noeud(self, agent_id: str, apres: Callable[[Dossier], None] | None = None):
        def f(etat: Etat) -> dict:
            d = vers_dossier(etat)
            n_hist = len(d.historique)
            maj: dict[str, Any] = {}
            try:
                self.agents[agent_id].executer(d, self.ctx)
            except (ErreurAgent, ValidationManquante) as e:
                maj["erreurs"] = [{"agent": agent_id, "message": str(e), "date": maintenant()}]
                d.revue_humaine = d.revue_humaine or {"agent": agent_id, "motif": str(e)}
            if apres:
                apres(d)
            maj.update(
                {
                    "sorties": {k: v for k, v in d.sorties.items() if k in (agent_id, "A10")},
                    "historique": [e.model_dump() for e in d.historique[n_hist:]],
                    "statut": d.statut if d.statut != etat.get("statut") else None,
                    "revue_humaine": d.revue_humaine,
                }
            )
            return maj

        f.__name__ = agent_id
        return f

    def _iris(self, evenement: str, motif: Callable[[Etat], str | None] = lambda e: None):
        def f(etat: Etat) -> dict:
            d = vers_dossier(etat)
            n = len(d.historique)
            self.agents["A10"].informer(d, self.ctx, evenement, motif=motif(etat))
            return {"sorties": {"A10": d.sorties["A10"]}, "historique": [e.model_dump() for e in d.historique[n:]]}

        return f

    def _pause(self, nom: str):
        def f(etat: Etat) -> dict:
            journaliser(etat["dossier_id"], "ZEUS", "reprise_apres_humain", point=nom)
            return {"revue_humaine": None} if nom != "comite" else {}

        return f

    def _statut(self, statut: str):
        return lambda etat: {"statut": statut}

    # ---------- routage -----------------------------------------------------------------------
    @staticmethod
    def _apres_themis(etat: Etat) -> str:
        return {"rejete": "iris_rejet", "revue_moderation": "moderation_humaine"}.get(etat.get("statut"), "iris_accuse")

    @staticmethod
    def _apres_moderateur(etat: Etat) -> str:
        return "iris_accuse" if (etat.get("decision_moderation") or {}).get("decision") == "publie" else "iris_rejet"

    @staticmethod
    def _apres_kairos(etat: Etat) -> str:
        return "revue_humaine" if etat.get("revue_humaine") else "A8"

    @staticmethod
    def _apres_comite(etat: Etat) -> str:
        return "A9" if (etat.get("decision_comite") or {}).get("decision") == "valide" else "iris_non_retenu"

    def _construire(self) -> StateGraph:
        g = StateGraph(Etat)
        for a in ("A1", "A2", "A3", "A4", "A5", "A7", "A8", "A9"):
            g.add_node(a, self._noeud(a))
        g.add_node("moderation_humaine", self._pause("moderation_humaine"))
        g.add_node("revue_humaine", self._pause("revue_humaine"))
        g.add_node("comite", self._pause("comite"))
        g.add_node("iris_accuse", self._iris("accuse"))
        g.add_node(
            "iris_rejet",
            self._iris(
                "rejet",
                lambda e: (
                    "; ".join((e.get("sorties", {}).get("A2") or {}).get("motifs") or [])
                    or (e.get("decision_moderation") or {}).get("motif")
                ),
            ),
        )
        g.add_node("iris_regroupement", self._iris("regroupement"))
        g.add_node("iris_valide", self._iris("decision_valide"))
        g.add_node(
            "iris_non_retenu",
            self._iris("decision_non_retenu", lambda e: (e.get("decision_comite") or {}).get("commentaire")),
        )
        g.add_node("marquer_non_retenu", self._statut("non_retenu"))

        g.add_edge(START, "A1")
        g.add_edge("A1", "A2")
        g.add_conditional_edges("A2", self._apres_themis, ["iris_rejet", "moderation_humaine", "iris_accuse"])
        g.add_conditional_edges("moderation_humaine", self._apres_moderateur, ["iris_accuse", "iris_rejet"])
        g.add_edge("iris_rejet", END)
        g.add_edge("iris_accuse", "A3")
        g.add_edge("A3", "A4")  # Hestia et Gaïa en parallèle
        g.add_edge("A3", "A5")
        g.add_edge(["A4", "A5"], "A7")
        g.add_conditional_edges("A7", self._apres_kairos, ["revue_humaine", "A8"])
        g.add_edge("revue_humaine", "A8")
        g.add_edge("A8", "comite")
        g.add_conditional_edges("comite", self._apres_comite, ["A9", "iris_non_retenu"])
        g.add_edge("A9", "iris_valide")
        g.add_edge("iris_valide", END)
        g.add_edge("iris_non_retenu", "marquer_non_retenu")
        g.add_edge("marquer_non_retenu", END)
        return g

    # ---------- API publique ------------------------------------------------------------------
    @staticmethod
    def _config(dossier_id: str) -> dict:
        return {"configurable": {"thread_id": dossier_id}}

    def lancer(self, dossier_id: str, contribution: Contribution | dict) -> dict:
        c = contribution if isinstance(contribution, dict) else contribution.model_dump()
        journaliser(dossier_id, "ZEUS", "reception", canal=c.get("canal"))
        self.graphe.invoke(
            {"dossier_id": dossier_id, "contribution": c, "statut": "recu", "sorties": {}, "historique": []},
            self._config(dossier_id),
        )
        return self.etat(dossier_id)

    def etat(self, dossier_id: str) -> dict:
        snap = self.graphe.get_state(self._config(dossier_id))
        v = dict(snap.values)
        v["en_attente_de"] = list(snap.next)
        return v

    def decider(
        self, dossier_id: str, point: str, decision: str, validateur: str, commentaire: str = "", piste_retenue: int = 0
    ) -> dict:
        """Enregistre une décision humaine tracée puis reprend le graphe."""
        snap = self.graphe.get_state(self._config(dossier_id))
        if point not in snap.next:
            raise ValueError(f"Le dossier {dossier_id} n'attend pas « {point} » (attend : {list(snap.next)}).")
        trace = {
            "decision": decision,
            "validateur": validateur,
            "commentaire": commentaire,
            "date": maintenant(),
            "piste_retenue": piste_retenue,
        }
        cle = {"moderation_humaine": "decision_moderation", "comite": "decision_comite"}.get(point)
        maj = {
            "historique": [{"date": trace["date"], "agent": f"HUMAIN:{validateur}", "action": point, "detail": trace}]
        }
        if cle:
            maj[cle] = {**trace, "motif": commentaire}
        if point == "moderation_humaine":
            maj["statut"] = "publie" if decision == "publie" else "rejete"
        if point == "comite":
            maj["statut"] = "valide_comite" if decision == "valide" else "non_retenu"
        self.graphe.update_state(self._config(dossier_id), maj)
        journaliser(dossier_id, f"HUMAIN:{validateur}", point, decision=decision)
        self.graphe.invoke(None, self._config(dossier_id))
        return self.etat(dossier_id)

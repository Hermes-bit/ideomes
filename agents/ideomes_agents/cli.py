"""Ligne de commande : `ideomes <commande>` (ou `python -m ideomes_agents.cli <commande>`)."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from .config import reglages
from .core.contexte import Contexte
from .registry import registre

EXEMPLE = {
    "texte": "Dans notre secteur il n'y a pas de forage, les femmes marchent 5 km chaque jour pour chercher de l'eau. "
    "Appelez-moi au 70 12 34 56.",
    "canal": "web",
    "domaine_declare": "Eau et assainissement",
    "region": "Centre",
    "province": "Kadiogo",
    "commune": "Ouagadougou",
    "auteur_id": "u_demo",
    "consentement_rgpd": True,
    "consentement_contact": True,
}


def _afficher(x) -> None:
    print(json.dumps(x, ensure_ascii=False, indent=2, default=str))


def cmd_agents(_):
    r = registre()
    for bloc in ("orchestrateur", "auditeur", "veille"):
        f = r[bloc]
        print(f"{f['id']:8} {f['nom']:12} {f['role']}")
    for f in r["agents"]:
        print(f"{f['id']:8} {f['nom']:12} {f['role']}  [{f['couche']}, modèle {f.get('modele') or 'aucun'}]")


def cmd_demo(a):
    from .orchestrateur import Zeus

    zeus = Zeus(Contexte())
    did = "demo-" + uuid.uuid4().hex[:6]
    print(f"Mode LLM : {reglages.llm_mode}. Dossier {did}\n")
    etat = zeus.lancer(did, EXEMPLE)
    print("Statut :", etat["statut"], "| en attente de :", etat["en_attente_de"])
    if "moderation_humaine" in etat["en_attente_de"]:
        etat = zeus.decider(did, "moderation_humaine", "publie", "moderateur.demo")
    if "revue_humaine" in etat["en_attente_de"]:
        etat = zeus.decider(did, "revue_humaine", "ok", "analyste.demo")
    print(
        "Score Kairos :",
        etat["sorties"]["A7"]["score"],
        "| pistes :",
        [p["titre"] for p in etat["sorties"]["A8"]["pistes"]],
    )
    etat = zeus.decider(did, "comite", "valide", "comite.demo", "Démarrer par la piste à faible coût.", piste_retenue=0)
    print("Statut final :", etat["statut"])
    if a.complet:
        _afficher(etat)
    else:
        print("\nMessages d'Iris :")
        for m in etat["sorties"]["A10"]["messages"]:
            print(f" · [{m['evenement']}] {m['message']}")


def cmd_run(a):
    from .orchestrateur import Zeus

    contribution = json.loads(Path(a.fichier).read_text(encoding="utf-8")) if a.fichier else EXEMPLE
    _afficher(Zeus(Contexte()).lancer(a.id or uuid.uuid4().hex[:8], contribution))


def cmd_veille(a):
    from . import hermes

    _afficher(hermes.executer(a.api))


def cmd_eval(a):
    from .eval_runner import evaluer

    r = evaluer(a.jeu)
    _afficher(r)
    sys.exit(0 if r["reussite"] else 1)


def main(argv=None):
    p = argparse.ArgumentParser(prog="ideomes", description="Agents IA d'Idéomès")
    s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("agents", help="Liste les agents et leurs noms").set_defaults(f=cmd_agents)
    d = s.add_parser("demo", help="Fait passer une idée d'exemple dans tout le pipeline")
    d.add_argument("--complet", action="store_true")
    d.set_defaults(f=cmd_demo)
    r = s.add_parser("run", help="Traite une contribution (fichier JSON)")
    r.add_argument("fichier", nargs="?")
    r.add_argument("--id")
    r.set_defaults(f=cmd_run)
    v = s.add_parser("veille", help="Lance Hermès (veille des actualités) et envoie les propositions à l'API")
    v.add_argument("--api")
    v.set_defaults(f=cmd_veille)
    e = s.add_parser("eval", help="Évalue les agents sur le jeu annoté")
    e.add_argument("--jeu")
    e.set_defaults(f=cmd_eval)
    a = p.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()

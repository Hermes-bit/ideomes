# Idéomès : plateforme citoyenne et agents IA

**Geomessen Burkina Faso** · version 0.1.0 (30 septembre 2026)

Idéomès recueille les besoins et les idées des Burkinabè (appli mobile web), puis une équipe de
15 agents IA, supervisée par des humains, les analyse, les priorise et suit leur réalisation.

Ce dossier contient la **dernière production de l'appli** (version 29 de l'artefact claude.ai) et
le **squelette complet** pour continuer le développement sur votre poste avec VS Code.

---

## 1. Démarrage rapide (10 minutes)

Prérequis : **Python 3.11 ou plus**, **VS Code**, Git. Docker est facultatif (PostgreSQL).

```bash
# 1. Ouvrir le dossier dans VS Code, puis dans le terminal intégré :
python -m venv .venv
# Windows :   .venv\Scripts\activate
# macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt
pip install -e agents
cp .env.example .env          # Windows : copy .env.example .env

# 2. Construire l'appli et lancer l'API
python web/build.py
cd api && uvicorn app.main:app --reload --port 8000

# 3. Dans un second terminal : remplir la base (vidéo + 5 actualités « À la une »)
python scripts/seed.py
```

Ouvrez ensuite :

| Adresse | Ce que vous voyez |
|---|---|
| http://localhost:8000/?user=u_awa | l'appli vue par une participante |
| http://localhost:8000/?user=owner | l'appli vue par l'administrateur (puis « Connexion administrateur » : admin@geomessen.bf / ideomes-demo — identifiants de démonstration **à changer immédiatement** via « Réinitialiser le mot de passe » avant tout usage réel) |
| http://localhost:8000/docs | la documentation interactive de l'API |

Guide pas à pas : [docs/prise-en-main-vscode.md](docs/prise-en-main-vscode.md).

Raccourcis : `scripts/dev.ps1 install|api|seed|test|demo` (Windows), `scripts/dev.sh ...` ou `make ...` (Linux, macOS).
Dans VS Code : **Exécuter et déboguer** propose « API Idéomès », « Agents : démo complète », « Hermès », « Évaluation ».

### Voir les agents travailler, sans clé ni coût

```bash
ideomes agents     # liste des 15 agents et de leurs noms
ideomes demo       # une idée d'exemple traverse tout le pipeline
pytest agents/tests api/tests
```

Par défaut `LLM_MODE=simule` : les agents répondent de façon déterministe (réponses marquées `[simulé]`).
Pour de vraies analyses, mettez votre clé Anthropic dans `.env` et `LLM_MODE=anthropic`.

---

## 2. Architecture

```
ideomes/
├── web/                     Appli mobile (une page HTML autonome)
│   ├── src/ideomes.src.html     code source de l'appli (celui de l'artefact, inchangé)
│   ├── src/claude-shim.js       remplace window.claude.use(...) par l'API locale
│   ├── assets/                  logos, vidéo de contexte, limites administratives (13 régions, 45 provinces, 351 communes)
│   └── build.py                 assemble web/dist/index.html
├── api/                     FastAPI : base de l'appli, fichiers, dossiers d'agents, décisions humaines
│   ├── app/routers/             db (documents), moi (identité), assets (/_blob), dossiers (agents)
│   ├── app/pipeline.py          chaque nouvelle idée → dossier → Zeus
│   └── tests/
├── agents/                  Paquet Python `ideomes_agents` (LangGraph + Claude)
│   ├── ideomes_agents/agents.yaml   registre : noms, rôles, modèles, seuils (les noms se changent ici)
│   ├── ideomes_agents/orchestrateur.py   Zeus (graphe d'états, validations humaines)
│   ├── ideomes_agents/agents/       A1 à A12, Apollon
│   ├── ideomes_agents/hermes.py     veille des actualités
│   ├── ideomes_agents/prompts/      un prompt par agent (versionné)
│   ├── ideomes_agents/schemas/      un schéma JSON de sortie par agent
│   ├── ideomes_agents/core/         dossier partagé, client Claude, masquage, territoire, score, audit
│   ├── eval/jeu_annote.jsonl        jeu d'évaluation (fictif, à remplacer)
│   └── tests/
├── db/init.sql              PostgreSQL : pgvector et index des plongements
├── docs/                    architecture, agents, conformité, décisions (ADR), stratégie PDF
├── scripts/                 seed, raccourcis Windows / Linux
└── docker-compose.yml       PostgreSQL 16 + pgvector et l'API
```

Détails : [docs/architecture.md](docs/architecture.md).

---

## 3. Les agents

| Id | Nom | Rôle | Couche | Modèle |
|---|---|---|---|---|
| ZEUS | **Zeus** | Orchestrateur | pilotage | aucun (graphe) |
| APOLLON | **Apollon** | Auditeur qualité (échantillon 8 %) | contrôle | fort |
| HERMES | **Hermès** | Veille des actualités « À la une » | veille | fort + recherche web |
| A1 | **Déméter** | Collecteur multicanal | Entrée | aucun |
| A2 | **Thémis** | Modération & conformité | Entrée | léger |
| A3 | **Athéna** | Analyste des besoins | Analyse | fort |
| A4 | **Hestia** | Regroupeur intelligent | Analyse | aucun (similarité) |
| A5 | **Gaïa** | Analyste territorial | Analyse | aucun (géocodage) |
| A6 | **Artémis** | Veilleur des tendances | Analyse | fort |
| A7 | **Kairos** | Priorisateur | Décision | fort (notes) + calcul |
| A8 | **Héphaïstos** | Générateur de solutions | Décision | fort |
| A9 | **Héra** | Chef de projet | Action | fort |
| A10 | **Iris** | Ambassadeur communautaire | Action | léger |
| A11 | **Niké** | Évaluateur d'impact | Action | fort |
| A12 | **Hélios** | Tableau de bord décisionnel | Action | aucun (agrégation) |

Fiches complètes : [docs/agents.md](docs/agents.md). **Changer un nom** : modifiez `nom:` dans
`agents/ideomes_agents/agents.yaml`, c'est le seul endroit.

Parcours d'une idée :

```
Déméter → Thémis ─┬─ rejetée ─────────────→ Iris (motif)
                  ├─ douteuse → [MODÉRATEUR] ─┐
                  └─ publiée → Iris (accusé) ─┴→ Athéna → (Hestia ∥ Gaïa) → Kairos
Kairos ─(confiance < 0,7)→ [REVUE HUMAINE] → Héphaïstos → [COMITÉ] ─┬─ validée → Héra → Iris
                                                                      └─ non retenue → Iris
```

Les trois points entre crochets sont des **interruptions** : rien ne continue sans une décision
humaine tracée (`POST /api/dossiers/{id}/decision`).

---

## 4. Feuille de route

| Phase | Contenu | État dans ce dossier |
|---|---|---|
| MVP | A1, A2, A3, A4, A10, A12 + Zeus | codés, testés en mode simulé |
| Phase 2 | A5 à A8 + Apollon | codés, à calibrer sur données réelles |
| Phase 3 | A9, A11, suivi des projets | codés, à brancher sur les projets réels |

Prochaines étapes conseillées : voir la section « À faire avant la mise en ligne » de
[docs/conformite.md](docs/conformite.md) (vraie authentification, connecteur WhatsApp, hébergement).

---

## 5. Licence

Ce projet est distribué sous licence [AGPL-3.0](LICENSE). Toute personne qui héberge une version
modifiée de ce code (y compris en SaaS) doit republier le code source de sa version.

© 2026 Geomessen. Contact : contact@geomessen.com · +226 55 66 14 49

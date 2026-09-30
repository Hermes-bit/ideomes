# Idéomès : plateforme citoyenne et agents IA

**Geomessen Burkina Faso** · version 0.1.0 (30 septembre 2026)

Idéomès recueille les besoins et les idées des Burkinabè (appli mobile web), puis une équipe de
15 agents IA, supervisée par des humains, les analyse, les priorise et suit leur réalisation.

Ce dossier contient la **dernière production de l'appli** (version 29 de l'artefact claude.ai) et
le **squelette complet** pour continuer le développement sur votre poste avec VS Code.

---

## 1. Démarrage rapide

L'appli web (`web/`) est **statique** et parle directement à **Supabase** (Postgres + Auth + Storage) —
elle ne dépend plus du backend FastAPI de `api/` pour fonctionner (voir § Architecture). Le backend
`api/` + `agents/` reste dans ce dépôt pour une phase ultérieure (pipeline des 15 agents IA), branché
séparément sur la même base Supabase.

### 1.a Appli web (Supabase)

Prérequis : **Python 3.11 ou plus**, un projet Supabase (gratuit) — voir § 5 pour le créer et y
exécuter `db/supabase_schema.sql`.

```bash
# Windows (PowerShell) :
$env:SUPABASE_URL = "https://xxxx.supabase.co"
$env:SUPABASE_ANON_KEY = "eyJ..."
# macOS/Linux :
export SUPABASE_URL=https://xxxx.supabase.co SUPABASE_ANON_KEY=eyJ...

python web/build.py
python -m http.server 8000 --directory web/dist
```

Ouvrez http://localhost:8000 : navigation libre (actualités, carte), connexion par e-mail (lien
magique Supabase) requise pour envoyer une idée. `admin@geomessen.bf` (ou toute adresse ajoutée à la
table `admins`) voit l'espace administrateur dès sa connexion.

Pour remplir la base une première fois (vidéo de contexte + 5 actualités) :
`SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... python scripts/seed_supabase.py` (clé service_role,
jamais celle utilisée pour le build — voir l'en-tête du script).

Déploiement public : § 5 « GitHub Pages + Supabase ».

### 1.b Backend API + agents IA (optionnel, phase ultérieure)

`api/` (FastAPI) et `agents/` (pipeline LangGraph + Claude) forment un second backend, autonome,
pour le traitement des idées par les 15 agents — pas encore branché sur Supabase. Utile dès
maintenant pour développer/tester le pipeline lui-même :

```bash
python -m venv .venv && .venv\Scripts\activate   # macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt && pip install -e agents
cp .env.example .env          # Windows : copy .env.example .env

ideomes agents     # liste des 15 agents et de leurs noms
ideomes demo       # une idée d'exemple traverse tout le pipeline
pytest agents/tests api/tests
```

Par défaut `LLM_MODE=simule` : les agents répondent de façon déterministe (réponses marquées `[simulé]`).
Pour de vraies analyses, mettez votre clé Anthropic dans `.env` et `LLM_MODE=anthropic`. Hébergement
possible via `render.yaml` (Docker) quand ce pipeline sera reconnecté à la base Supabase.

Guide pas à pas (ancien flux tout-FastAPI, pour référence) : [docs/prise-en-main-vscode.md](docs/prise-en-main-vscode.md).
Raccourcis : `scripts/dev.ps1 install|api|seed|test|demo` (Windows), `scripts/dev.sh ...` ou `make ...` (Linux, macOS).

---

## 2. Architecture

```
ideomes/
├── web/                     Appli mobile (une page HTML autonome, statique)
│   ├── src/ideomes.src.html     code source de l'appli
│   ├── src/claude-shim.js       remplace window.claude.use(...) par Supabase (Postgres + Auth + Storage)
│   ├── assets/                  logos, vidéo de contexte, limites administratives (13 régions, 45 provinces, 351 communes)
│   └── build.py                 assemble web/dist/index.html (injecte SUPABASE_URL/SUPABASE_ANON_KEY)
├── db/supabase_schema.sql  Schéma Postgres + Row Level Security pour Supabase (à exécuter une fois)
├── .github/workflows/deploy-pages.yml   build + déploiement GitHub Pages à chaque push sur main
├── scripts/seed_supabase.py Remplit Supabase (vidéo + actualités) via la clé service_role
│
├── api/                     FastAPI (phase ultérieure, pipeline agents — pas branché sur le web actuel)
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
├── db/init.sql              PostgreSQL local (docker-compose) pour l'ancien flux api/ + agents/
├── docs/                    architecture, agents, conformité, décisions (ADR), stratégie PDF
├── scripts/                 seed (Supabase et ancien flux FastAPI), raccourcis Windows / Linux
├── render.yaml              hébergement Docker de api/ + agents/ (phase ultérieure, pipeline)
└── docker-compose.yml       PostgreSQL 16 + pgvector et l'API (ancien flux local)
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
[docs/conformite.md](docs/conformite.md).

---

## 5. Déploiement : GitHub Pages + Supabase

1. **Créer un projet Supabase** sur [supabase.com](https://supabase.com) (gratuit).
2. **Récupérer** `Project URL` et `anon public key` (Settings → API).
3. **Exécuter** [`db/supabase_schema.sql`](db/supabase_schema.sql) dans l'éditeur SQL du projet
   (Database → SQL Editor). Adapte `insert into public.admins (email) values ('admin@geomessen.bf')`
   si l'adresse administrateur doit changer ; d'autres admins peuvent être ajoutés plus tard par un
   simple `insert` supplémentaire.
4. **Authentication → URL Configuration** : ajouter l'URL de la Pages GitHub
   (`https://<compte>.github.io/ideomes/`) et une entrée locale (`http://localhost:8000/**`) aux
   redirections autorisées — sinon le lien de connexion par e-mail est rejeté.
5. **Secrets GitHub** (Settings → Secrets and variables → Actions, ou `gh secret set`) :
   `SUPABASE_URL` et `SUPABASE_ANON_KEY` (valeurs de l'étape 2 — l'anon key est publique par
   conception, ce n'est pas une fuite si elle apparaît dans le HTML généré).
6. **Activer GitHub Pages** (source = GitHub Actions) :
   `gh api --method POST repos/<compte>/ideomes/pages -f build_type=workflow`.
7. **Pousser sur `main`** : le workflow [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml)
   construit `web/dist` et le publie automatiquement.
8. **Remplir le contenu de démo** (une fois) :
   `SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... python scripts/seed_supabase.py`.

Le pipeline des 15 agents IA n'est pas branché à cette étape (voir § 4, Phase 2/3) : les idées
soumises sont stockées dans Supabase mais pas encore traitées automatiquement.

---

## 6. Licence

Ce projet est distribué sous licence [AGPL-3.0](LICENSE). Toute personne qui héberge une version
modifiée de ce code (y compris en SaaS) doit republier le code source de sa version.

© 2026 Geomessen. Contact : contact@geomessen.com · +226 55 66 14 49

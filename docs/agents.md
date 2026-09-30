# Fiches des agents

Source : `agents/ideomes_agents/agents.yaml` (généré à partir du registre). Stratégie complète : `Ideomes_Strategie_Agents_IA_v2.pdf`.

## Zeus (ZEUS) : Orchestrateur

Reçoit chaque dossier, décide quel agent appeler, lance les agents en parallèle quand c'est possible, gère les erreurs et les relances (2 au maximum), journalise chaque étape.

Code : `ideomes_agents/orchestrateur.py`

## Apollon (APOLLON) : Auditeur qualité

Contrôle en continu un échantillon de 5 à 10 % des sorties (erreurs factuelles, biais, cohérence entre agents, représentativité territoriale). Rapport mensuel au comité, alerte immédiate sous seuil.

Code : `ideomes_agents/agents/apollon.py`

## Hermès (HERMES) : Veille des actualités

Cherche chaque matin les avancées récentes au Burkina Faso, vérifie chaque chiffre dans l'article d'origine et propose des actualités à l'administrateur. Ne publie jamais seul.

Code : `ideomes_agents/hermes.py`

## Déméter (A1) : Collecteur multicanal

- **Couche** : entree
- **Mission** : Recevoir les contributions sur tous les canaux et les transformer en dossier structuré, sans les interpréter.
- **Modèle** : leger
- **Seuil de confiance** : sans objet
- **Indicateur** : Contributions complètes >= 95 % ; accusé de réception < 1 min
- **Code** : `ideomes_agents/agents/a01_demeter.py`

## Thémis (A2) : Modération & Conformité

- **Couche** : entree
- **Mission** : Protéger les personnes et la plateforme avant toute analyse (données personnelles masquées, toxicité, spam).
- **Modèle** : leger
- **Seuil de confiance** : 0.7
- **Indicateur** : Faux rejets < 2 % ; 100 % des données personnelles masquées
- **Code** : `ideomes_agents/agents/a02_themis.py`, prompt `prompts/themis.md`

## Athéna (A3) : Analyste des besoins

- **Couche** : analyse
- **Mission** : Comprendre ce que la personne demande vraiment.
- **Modèle** : fort
- **Seuil de confiance** : 0.7
- **Indicateur** : Accord avec un analyste humain >= 85 %
- **Code** : `ideomes_agents/agents/a03_athena.py`, prompt `prompts/athena.md`

## Hestia (A4) : Regroupeur intelligent

- **Couche** : analyse
- **Mission** : Repérer les idées similaires pour donner du poids aux demandes partagées. Propose, ne fusionne jamais seul.
- **Modèle** : aucun (code déterministe)
- **Seuil de confiance** : sans objet
- **Indicateur** : Précision des regroupements >= 90 % ; doublons résiduels < 5 %
- **Code** : `ideomes_agents/agents/a04_hestia.py`

## Gaïa (A5) : Analyste territorial

- **Couche** : analyse
- **Mission** : Situer l'idée et la croiser avec les données du territoire.
- **Modèle** : aucun (code déterministe)
- **Seuil de confiance** : sans objet
- **Indicateur** : Géocodage correct >= 95 %
- **Code** : `ideomes_agents/agents/a05_gaia.py`

## Artémis (A6) : Veilleur des tendances

- **Couche** : analyse
- **Mission** : Détecter les sujets émergents et les signaux faibles sur l'ensemble des contributions.
- **Modèle** : fort
- **Seuil de confiance** : sans objet
- **Indicateur** : Délai de détection d'un sujet émergent < 7 jours
- **Code** : `ideomes_agents/agents/a06_artemis.py`, prompt `prompts/artemis.md`

## Kairos (A7) : Priorisateur

- **Couche** : decision
- **Mission** : Calculer un score de priorité transparent et reproductible.
- **Modèle** : fort
- **Seuil de confiance** : 0.7
- **Indicateur** : Même dossier = même score ; accord comité >= 80 % sur le top 10
- **Code** : `ideomes_agents/agents/a07_kairos.py`, prompt `prompts/kairos.md`

## Héphaïstos (A8) : Générateur de solutions

- **Couche** : decision
- **Mission** : Proposer 2 à 3 pistes concrètes, chiffrées à grands traits, dont au moins une à faible coût.
- **Modèle** : fort
- **Seuil de confiance** : 0.7
- **Indicateur** : Pistes jugées exploitables par le comité >= 70 %
- **Code** : `ideomes_agents/agents/a08_hephaistos.py`, prompt `prompts/hephaistos.md`

## Héra (A9) : Chef de projet

- **Couche** : action
- **Mission** : Transformer une idée validée par le comité en fiche projet. Ne démarre jamais sans validation humaine tracée.
- **Modèle** : fort
- **Seuil de confiance** : sans objet
- **Indicateur** : Fiches acceptées sans refonte majeure >= 75 %
- **Code** : `ideomes_agents/agents/a09_hera.py`, prompt `prompts/hera.md`

## Iris (A10) : Ambassadeur communautaire

- **Couche** : action
- **Mission** : Informer chaque contributeur à chaque étape de la vie de son idée. Mention « réponse générée avec l'aide de l'IA ». Aucun engagement de réalisation.
- **Modèle** : leger
- **Seuil de confiance** : sans objet
- **Indicateur** : 100 % des contributeurs informés ; satisfaction >= 4/5
- **Code** : `ideomes_agents/agents/a10_iris.py`, prompt `prompts/iris.md`

## Niké (A11) : Évaluateur d'impact

- **Couche** : action
- **Mission** : Mesurer ce que les projets réalisés ont changé, en distinguant mesuré et estimé.
- **Modèle** : fort
- **Seuil de confiance** : sans objet
- **Indicateur** : Projets évalués 6 mois après réalisation >= 90 %
- **Code** : `ideomes_agents/agents/a11_nike.py`, prompt `prompts/nike.md`

## Hélios (A12) : Tableau de bord décisionnel

- **Couche** : action
- **Mission** : Donner aux décideurs une vue claire et à jour. Chaque chiffre renvoie aux contributions sources anonymisées.
- **Modèle** : aucun (code déterministe)
- **Seuil de confiance** : sans objet
- **Indicateur** : Utilisation hebdomadaire par au moins 1 décideur
- **Code** : `ideomes_agents/agents/a12_helios.py`

## Grille de Kairos (A7)

Score = 20 × (0,30 Impact + 0,20 Bénéficiaires + 0,20 Urgence + 0,20 Faisabilité + 0,10 Alignement), notes de 0 à 5, score sur 100.
Bonus de représentativité : jusqu'à +5 pour les territoires sous-représentés. Le calcul est fait par le code (`core/scoring.py`), jamais par le LLM.

## Ajouter ou modifier un agent

1. Déclarer l'agent dans `agents.yaml` (id, nom, rôle, modèle, seuil).
2. Écrire son prompt (`prompts/<nom>.md`) et son schéma de sortie (`schemas/<nom>.json`).
3. Créer la classe dans `agents/` (hériter de `Agent`, implémenter `traiter`).
4. L'ajouter au graphe de Zeus (`orchestrateur.py`) et à `agents/__init__.py`.
5. Ajouter des cas au jeu d'évaluation et lancer `ideomes eval` avant tout déploiement.

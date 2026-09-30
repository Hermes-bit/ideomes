# Prise en main dans VS Code

1. **Fichier > Ouvrir le dossier…** : choisissez le dossier `ideomes`.
2. Acceptez l'installation des **extensions recommandées** (Python, Pylance, Ruff, Docker, YAML, Mermaid, REST Client).
3. Terminal intégré (Ctrl + ù ou Ctrl + `) : suivez le « Démarrage rapide » du README.
4. **Ctrl + Maj + P > Python: Select Interpreter** : choisissez `.venv` (sous Windows, VS Code le détecte dans `.venv\Scripts`).
5. Onglet **Exécuter et déboguer** : lancez « API Idéomès ». Points d'arrêt possibles partout (agents compris).
6. Onglet **Tests** (fiole) : tous les tests des agents et de l'API.
7. Ouvrez `api/requetes.http` : cliquez « Send Request » au-dessus de chaque requête pour piloter les dossiers
   (décision du comité, synthèse d'Hélios).

## Modifier l'appli

Éditez `web/src/ideomes.src.html`, puis relancez la tâche **Construire l'appli web** (ou `python web/build.py`)
et rechargez la page. Le même fichier peut être recollé dans l'artefact claude.ai : les emplacements
`__WORD__`, `__IDEO__` et `__BF__` y sont remplacés de la même façon.

## Passer aux vraies analyses Claude

Dans `.env` : `ANTHROPIC_API_KEY=...` et `LLM_MODE=anthropic`. Commencez par `ideomes eval`, puis `ideomes demo`.
Chaque appel est journalisé (modèle, durée, jetons) dans `data/journal_audit.jsonl`.

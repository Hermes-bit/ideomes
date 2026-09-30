# ADR 0001 : choix techniques

**Date** : 30 septembre 2026 · **Statut** : accepté

## Contexte
Passer de l'artefact claude.ai (prototype en ligne) à un projet que Geomessen fait évoluer sur ses postes,
avec une équipe d'agents IA définie dans la stratégie v2.

## Décisions
1. **Python 3.11, FastAPI** pour l'API : simple, typé, documentation automatique (/docs).
2. **LangGraph** pour Zeus : graphe d'états explicite, parallélisme (Hestia ∥ Gaïa), interruptions
   natives pour les validations humaines, reprise après redémarrage grâce aux checkpoints.
3. **Claude (Anthropic)** : modèle « fort » (claude-sonnet-5-5) pour l'analyse et la génération,
   « léger » (claude-haiku-4-5-20251001) pour la modération et les messages. Configurable dans `.env`.
4. **SQLite en local, PostgreSQL + pgvector en production** via SQLAlchemy : zéro installation pour
   démarrer, même code ensuite.
5. **Mode simulé** par défaut : développement, tests et démonstrations sans clé ni coût.
6. **L'appli reste en HTML autonome** avec un shim : un seul code pour l'artefact et le projet local.

## Conséquences
- Le shim fait du « polling » (3 s) au lieu de temps réel : suffisant pour l'usage, à remplacer par
  WebSocket ou SSE si le volume grandit.
- L'identité de développement doit être remplacée avant toute mise en ligne (voir conformite.md).

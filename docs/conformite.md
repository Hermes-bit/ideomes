# Conformité, protection des données et charte IA

## Principes appliqués dans le code

| Exigence | Mise en œuvre |
|---|---|
| Minimisation | Déméter ne garde que les champs utiles ; l'auteur est un identifiant opaque, jamais un nom |
| Masquage avant IA | Thémis masque téléphone, e-mail, CNIB, IBAN avant tout appel à Claude ; un reste détecté part en revue |
| Consentement | case RGPD obligatoire dans l'appli ; recontact seulement si la case dédiée est cochée |
| Contrôle humain | 3 points bloquants : modérateur (Thémis), comité (avant Héra), relecture des messages sensibles (Iris) |
| Seuil de confiance | toute sortie sous 0,7 part en revue humaine |
| Transparence | chaque message d'Iris porte « (Réponse rédigée avec l'aide de l'IA) » ; aucune promesse de réalisation |
| Explicabilité | Kairos publie sa grille ; chaque note est justifiée ; le score est recalculable |
| Traçabilité | table `journal_audit` et fichier `data/journal_audit.jsonl` : agent, modèle, durée, jetons, décision |
| Vie privée sur la carte | position publique arrondie au centre de la commune |
| Audit | Apollon contrôle 8 % des dossiers ; alerte si conformité < 85 % |

## Cadre

- Loi burkinabè n° 001-2021/AN portant protection des personnes à l'égard du traitement des données
  à caractère personnel ; autorité de contrôle : CIL (Commission de l'informatique et des libertés).
  Formalités à accomplir avant la mise en ligne.
- RGPD (contributeurs de la diaspora en Europe) et règlement européen sur l'IA (AI Act) : système à
  risque limité, obligations de transparence.

## À faire avant la mise en ligne

1. ~~**Authentification réelle**~~ : fait pour l'appli web déployée sur GitHub Pages + Supabase —
   connexion par lien magique e-mail (Supabase Auth), permissions appliquées par Row Level Security
   (voir `db/supabase_schema.sql`). Reste à faire : l'en-tête `X-Dev-User` de l'ancien backend
   `api/` (utilisé pour le pipeline agents, § 1.b du README) reste un outil de développement, pas
   une sécurité, tant que ce backend n'est pas lui aussi reconnecté à une vraie authentification.
   WhatsApp OTP (alternative à l'e-mail) reporté : nécessite un compte Twilio payant et une
   validation Meta Business.
2. Changer le mot de passe administrateur et `API_JETON_SERVICE` **de l'ancien backend `api/`**
   s'il est un jour redéployé (le nouveau flux Supabase n'utilise plus ces identifiants).
3. Hébergement avec chiffrement (HTTPS, base chiffrée), sauvegardes, durée de conservation définie.
4. Déclaration auprès de la CIL ; registre des traitements ; mentions d'information à jour.
5. Jeu d'évaluation réel (contributions annotées) et calibrage des seuils avant d'activer `LLM_MODE=anthropic`.
6. Procédure d'exercice des droits (accès, rectification, suppression) : contact@geomessen.com.

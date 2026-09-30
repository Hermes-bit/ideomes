-- Exécuté au premier démarrage du conteneur PostgreSQL.
-- Les tables applicatives sont créées par l'API (SQLAlchemy) ; ici : extensions et index vectoriel.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Plongements des idées pour Hestia (A4) : remplacera le vecteur « sac de mots » local.
CREATE TABLE IF NOT EXISTS plongements (
    dossier_id  VARCHAR(64) PRIMARY KEY,
    commune     VARCHAR(120),
    modele      VARCHAR(80) NOT NULL,
    vecteur     vector(1024) NOT NULL,
    cree_le     TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS plongements_hnsw ON plongements USING hnsw (vecteur vector_cosine_ops);
CREATE INDEX IF NOT EXISTS plongements_commune ON plongements (commune);

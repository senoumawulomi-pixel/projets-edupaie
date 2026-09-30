PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS eleve (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nom TEXT NOT NULL, prenom TEXT NOT NULL,
  classe TEXT NOT NULL, annee_scolaire TEXT NOT NULL,
  total_du REAL NOT NULL CHECK (total_du >= 0)
);
CREATE TABLE IF NOT EXISTS paiement (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  numero_recu TEXT NOT NULL UNIQUE,
  eleve_id INTEGER NOT NULL REFERENCES eleve(id) ON DELETE RESTRICT,
  montant REAL NOT NULL CHECK (montant > 0),
  date_paiement TEXT NOT NULL,
  mode TEXT NOT NULL CHECK (mode IN ('Espèces','Chèque','Virement','Mobile money')),
  solde_apres REAL NOT NULL CHECK (solde_apres >= 0)
);
CREATE INDEX IF NOT EXISTS idx_paiement_eleve ON paiement(eleve_id);

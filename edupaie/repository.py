"""Couche 1 : accès aux données. Seul endroit où du SQL est écrit."""
import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).resolve().parent.parent / "schema.sql"

LIST_SQL = """
SELECT e.*, COALESCE(SUM(p.montant),0) AS paye
FROM eleve e LEFT JOIN paiement p ON p.eleve_id = e.id
WHERE (e.nom LIKE :q OR e.prenom LIKE :q) AND (:classe = '' OR e.classe = :classe)
GROUP BY e.id ORDER BY e.nom, e.prenom"""

class Repository:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA.read_text(encoding="utf-8"))

    # --- élèves
    def add_eleve(self, nom, prenom, classe, annee, total):
        with self.conn:
            return self.conn.execute(
                "INSERT INTO eleve(nom,prenom,classe,annee_scolaire,total_du) VALUES (?,?,?,?,?)",
                (nom, prenom, classe, annee, total)).lastrowid

    def update_eleve(self, id_, nom, prenom, classe, annee, total):
        with self.conn:
            self.conn.execute(
                "UPDATE eleve SET nom=?,prenom=?,classe=?,annee_scolaire=?,total_du=? WHERE id=?",
                (nom, prenom, classe, annee, total, id_))

    def delete_eleve(self, id_):
        with self.conn:
            self.conn.execute("DELETE FROM eleve WHERE id=?", (id_,))

    def list_eleves(self, search="", classe=""):
        return self.conn.execute(LIST_SQL, {"q": f"%{search}%", "classe": classe}).fetchall()

    def get_eleve(self, id_):
        return self.conn.execute(
            "SELECT e.*, COALESCE((SELECT SUM(montant) FROM paiement WHERE eleve_id=e.id),0) AS paye "
            "FROM eleve e WHERE e.id=?", (id_,)).fetchone()

    def classes(self):
        return [r[0] for r in self.conn.execute("SELECT DISTINCT classe FROM eleve ORDER BY classe")]

    # --- paiements
    def add_paiement(self, eleve_id, montant, date, mode):
        """Transaction atomique : contrôle du solde + numéro de reçu unique."""
        try:
            self.conn.execute("BEGIN IMMEDIATE")
            e = self.get_eleve(eleve_id)
            solde = e["total_du"] - e["paye"]
            if montant > solde + 1e-9:
                raise ValueError(f"Le montant dépasse le solde restant ({solde:.0f}).")
            annee = date[:4]
            n = self.conn.execute(
                "SELECT COUNT(*) FROM paiement WHERE numero_recu LIKE ?", (f"R-{annee}-%",)
            ).fetchone()[0] + 1
            numero = f"R-{annee}-{n:06d}"
            cur = self.conn.execute(
                "INSERT INTO paiement(numero_recu,eleve_id,montant,date_paiement,mode,solde_apres) "
                "VALUES (?,?,?,?,?,?)", (numero, eleve_id, montant, date, mode, solde - montant))
            self.conn.commit()
            return cur.lastrowid
        except Exception:
            self.conn.rollback()
            raise

    def paiements_of(self, eleve_id):
        return self.conn.execute(
            "SELECT * FROM paiement WHERE eleve_id=? ORDER BY date_paiement, id", (eleve_id,)).fetchall()

    def get_paiement(self, id_):
        return self.conn.execute(
            "SELECT p.*, e.nom, e.prenom, e.classe, e.annee_scolaire, e.total_du "
            "FROM paiement p JOIN eleve e ON e.id=p.eleve_id WHERE p.id=?", (id_,)).fetchone()

    def count_paiements(self, eleve_id):
        return self.conn.execute("SELECT COUNT(*) FROM paiement WHERE eleve_id=?", (eleve_id,)).fetchone()[0]

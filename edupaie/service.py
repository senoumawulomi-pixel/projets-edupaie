"""Couche 2 : logique métier (validation, solde, statut, tableau de bord)."""
from datetime import date, datetime

MODES = ["Espèces", "Chèque", "Virement", "Mobile money"]
NON_PAYE, PARTIEL, SOLDE = "Non payé", "Partiellement payé", "Soldé"

class ValidationError(Exception):
    pass

def statut(total, paye):
    if paye <= 0:
        return NON_PAYE if total > 0 else SOLDE
    return SOLDE if paye >= total else PARTIEL

def parse_montant(txt, allow_zero=False):
    try:
        v = float(str(txt).replace(" ", "").replace(",", "."))
    except ValueError:
        raise ValidationError("Le montant doit être un nombre.")
    if v < 0 or (v == 0 and not allow_zero):
        raise ValidationError("Le montant doit être strictement positif.")
    return v

class Service:
    def __init__(self, repo):
        self.repo = repo

    def _check_eleve(self, nom, prenom, classe, annee, total):
        if not all(s.strip() for s in (nom, prenom, classe, annee)):
            raise ValidationError("Nom, prénom, classe et année scolaire sont obligatoires.")
        return nom.strip(), prenom.strip(), classe.strip(), annee.strip(), parse_montant(total, True)

    def creer_eleve(self, *f):
        return self.repo.add_eleve(*self._check_eleve(*f))

    def modifier_eleve(self, id_, *f):
        data = self._check_eleve(*f)
        paye = self.repo.get_eleve(id_)["paye"]
        if data[4] < paye:
            raise ValidationError("Le total dû ne peut pas être inférieur aux paiements déjà reçus.")
        self.repo.update_eleve(id_, *data)

    def supprimer_eleve(self, id_):
        if self.repo.count_paiements(id_):
            raise ValidationError("Suppression impossible : cet élève a des paiements (reçus émis).")
        self.repo.delete_eleve(id_)

    def lister(self, search="", classe="", filtre_statut=""):
        out = []
        for r in self.repo.list_eleves(search, classe):
            d = dict(r); d["solde"] = r["total_du"] - r["paye"]; d["statut"] = statut(r["total_du"], r["paye"])
            if not filtre_statut or d["statut"] == filtre_statut:
                out.append(d)
        return out

    def payer(self, eleve_id, montant_txt, date_txt, mode):
        montant = parse_montant(montant_txt)
        try:
            datetime.strptime(date_txt, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("Date invalide (format AAAA-MM-JJ).")
        if mode not in MODES:
            raise ValidationError("Mode de paiement invalide.")
        try:
            return self.repo.add_paiement(eleve_id, montant, date_txt, mode)
        except ValueError as e:
            raise ValidationError(str(e))

    def dashboard(self):
        el = self.lister()
        return {"nb": len(el), "encaisse": sum(e["paye"] for e in el),
                "restant": sum(e["solde"] for e in el),
                "non_soldes": sum(1 for e in el if e["statut"] != SOLDE)}

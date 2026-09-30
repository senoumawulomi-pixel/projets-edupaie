"""Couche 3 : interface PySide6. Aucun SQL ici, uniquement des appels au Service."""
import os, tempfile
from datetime import date
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget, QDialogButtonBox, QAbstractItemView)
from .service import MODES, SOLDE, NON_PAYE, PARTIEL, ValidationError
from .receipt import generate_receipt

def guarded(fn):
    """Aucune exception ne doit faire planter l'appli."""
    def wrap(self, *a):
        try:
            return fn(self)
        except ValidationError as e:
            QMessageBox.warning(self, "Saisie invalide", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur inattendue : {e}")
    return wrap

def fill(table, headers, rows):
    table.setColumnCount(len(headers)); table.setHorizontalHeaderLabels(headers)
    table.setRowCount(len(rows))
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            table.setItem(i, j, QTableWidgetItem(str(v)))
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.horizontalHeader().setStretchLastSection(True)

def open_receipt(repo, paiement_id):
    p = repo.get_paiement(paiement_id)
    path = os.path.join(tempfile.gettempdir(), f"{p['numero_recu']}.pdf")
    generate_receipt(p, path)
    QDesktopServices.openUrl(QUrl.fromLocalFile(path))

class EleveDialog(QDialog):
    def __init__(self, parent, eleve=None):
        super().__init__(parent); self.setWindowTitle("Élève")
        self.f = {k: QLineEdit(str(eleve[k]) if eleve else "") for k in
                  ("nom", "prenom", "classe", "annee_scolaire", "total_du")}
        if not eleve: self.f["annee_scolaire"].setText("2026-2027")
        form = QFormLayout(self)
        for label, k in [("Nom", "nom"), ("Prénom", "prenom"), ("Classe", "classe"),
                         ("Année scolaire", "annee_scolaire"), ("Total dû", "total_du")]:
            form.addRow(label, self.f[k])
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); form.addRow(bb)
    def values(self):
        return [self.f[k].text() for k in ("nom", "prenom", "classe", "annee_scolaire", "total_du")]

class PaiementDialog(QDialog):
    def __init__(self, parent, solde):
        super().__init__(parent); self.setWindowTitle("Nouveau paiement")
        self.montant = QLineEdit(); self.date = QLineEdit(date.today().isoformat())
        self.mode = QComboBox(); self.mode.addItems(MODES)
        form = QFormLayout(self)
        form.addRow(QLabel(f"Solde restant : {solde:,.0f}"))
        form.addRow("Montant", self.montant); form.addRow("Date (AAAA-MM-JJ)", self.date)
        form.addRow("Mode", self.mode)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject); form.addRow(bb)

class FicheDialog(QDialog):
    def __init__(self, parent, svc, eleve_id):
        super().__init__(parent); self.svc, self.id = svc, eleve_id
        self.resize(560, 420); self.setWindowTitle("Fiche élève")
        self.info = QLabel(); self.hist = QTableWidget(); self.hist.doubleClicked.connect(self.reprint)
        b1, b2 = QPushButton("Nouveau paiement"), QPushButton("Réimprimer le reçu sélectionné")
        b1.clicked.connect(self.pay); b2.clicked.connect(self.reprint)
        lay = QVBoxLayout(self)
        for w in (self.info, self.hist, b1, b2): lay.addWidget(w)
        self.refresh()
    def refresh(self):
        from .service import statut
        e = self.svc.repo.get_eleve(self.id); s = e["total_du"] - e["paye"]
        self.info.setText(f"<b>{e['nom']} {e['prenom']}</b> — {e['classe']} ({e['annee_scolaire']})<br>"
            f"Total dû : {e['total_du']:,.0f} | Payé : {e['paye']:,.0f} | Solde : {s:,.0f} | "
            f"Statut : <b>{statut(e['total_du'], e['paye'])}</b>")
        self.ps = self.svc.repo.paiements_of(self.id)
        fill(self.hist, ["Reçu", "Date", "Montant", "Mode", "Solde après"],
             [(p["numero_recu"], p["date_paiement"], f"{p['montant']:,.0f}", p["mode"],
               f"{p['solde_apres']:,.0f}") for p in self.ps])
    @guarded
    def pay(self):
        e = self.svc.repo.get_eleve(self.id)
        d = PaiementDialog(self, e["total_du"] - e["paye"])
        if d.exec():
            pid = self.svc.payer(self.id, d.montant.text(), d.date.text(), d.mode.currentText())
            self.refresh(); QMessageBox.information(self, "Succès", "Paiement enregistré.")
            open_receipt(self.svc.repo, pid)
    @guarded
    def reprint(self):
        r = self.hist.currentRow()
        if r < 0: raise ValidationError("Sélectionnez un paiement dans l'historique.")
        open_receipt(self.svc.repo, self.ps[r]["id"])

class ElevesTab(QWidget):
    def __init__(self, svc, on_change, statut_filter=False):
        super().__init__(); self.svc, self.on_change = svc, on_change
        self.q = QLineEdit(); self.q.setPlaceholderText("Rechercher nom / prénom…")
        self.cl = QComboBox(); self.st = QComboBox()
        self.st.addItems(["", NON_PAYE, PARTIEL, SOLDE]); self.st.setPlaceholderText("Statut")
        self.t = QTableWidget(); self.t.doubleClicked.connect(self.fiche)
        top = QHBoxLayout()
        for w in (self.q, QLabel("Classe"), self.cl, QLabel("Statut"), self.st): top.addWidget(w)
        btns = QHBoxLayout()
        for txt, fn in [("Ajouter", self.add), ("Modifier", self.edit), ("Supprimer", self.delete), ("Fiche / Paiements", self.fiche)]:
            b = QPushButton(txt); b.clicked.connect(fn); btns.addWidget(b)
        lay = QVBoxLayout(self); lay.addLayout(top); lay.addWidget(self.t); lay.addLayout(btns)
        self.q.textChanged.connect(self.refresh); self.cl.currentTextChanged.connect(self.refresh)
        self.st.currentTextChanged.connect(self.refresh); self.reload_classes()
    def reload_classes(self):
        cur = self.cl.currentText(); self.cl.blockSignals(True); self.cl.clear()
        self.cl.addItems([""] + self.svc.repo.classes()); self.cl.setCurrentText(cur)
        self.cl.blockSignals(False); self.refresh()
    def refresh(self):
        self.rows = self.svc.lister(self.q.text(), self.cl.currentText(), self.st.currentText())
        fill(self.t, ["Nom", "Prénom", "Classe", "Total dû", "Payé", "Solde", "Statut"],
             [(r["nom"], r["prenom"], r["classe"], f"{r['total_du']:,.0f}", f"{r['paye']:,.0f}",
               f"{r['solde']:,.0f}", r["statut"]) for r in self.rows])
    def current(self):
        r = self.t.currentRow()
        if r < 0: raise ValidationError("Sélectionnez un élève.")
        return self.rows[r]
    @guarded
    def add(self):
        d = EleveDialog(self)
        if d.exec(): self.svc.creer_eleve(*d.values()); self.on_change()
    @guarded
    def edit(self):
        e = self.current(); d = EleveDialog(self, e)
        if d.exec(): self.svc.modifier_eleve(e["id"], *d.values()); self.on_change()
    @guarded
    def delete(self):
        e = self.current()
        if QMessageBox.question(self, "Confirmer", f"Supprimer {e['nom']} {e['prenom']} ?") == QMessageBox.Yes:
            self.svc.supprimer_eleve(e["id"]); self.on_change()
    @guarded
    def fiche(self):
        FicheDialog(self, self.svc, self.current()["id"]).exec(); self.on_change()

class MainWindow(QMainWindow):
    def __init__(self, svc):
        super().__init__(); self.svc = svc; self.setWindowTitle("EduPaie"); self.resize(900, 560)
        self.tabs = QTabWidget(); self.setCentralWidget(self.tabs)
        self.dash = QLabel(); self.dash.setAlignment(Qt.AlignCenter); self.dash.setStyleSheet("font-size:18px")
        self.eleves = ElevesTab(svc, self.refresh_all)
        dw = QWidget(); dl = QVBoxLayout(dw); dl.addWidget(self.dash)
        self.tabs.addTab(dw, "Tableau de bord"); self.tabs.addTab(self.eleves, "Élèves")
        self.refresh_all()
    def refresh_all(self):
        d = self.svc.dashboard()
        self.dash.setText(f"Élèves : <b>{d['nb']}</b><br>Total encaissé : <b>{d['encaisse']:,.0f}</b><br>"
            f"Total restant dû : <b>{d['restant']:,.0f}</b><br>Élèves non soldés : <b>{d['non_soldes']}</b>")
        self.eleves.reload_classes()

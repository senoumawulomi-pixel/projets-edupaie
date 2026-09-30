"""Génération du reçu PDF à partir des données STOCKÉES (réimpression identique)."""
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas

def generate_receipt(p, path, ecole="École / Centre de formation"):
    c = canvas.Canvas(path, pagesize=A5); w, h = A5
    c.setFont("Helvetica-Bold", 16); c.drawCentredString(w/2, h-40, ecole)
    c.setFont("Helvetica-Bold", 13); c.drawCentredString(w/2, h-65, f"REÇU N° {p['numero_recu']}")
    c.line(30, h-75, w-30, h-75)
    lignes = [("Date", p["date_paiement"]), ("Élève", f"{p['nom']} {p['prenom']}"),
              ("Classe", f"{p['classe']} ({p['annee_scolaire']})"),
              ("Total dû", f"{p['total_du']:,.0f}"), ("Montant payé", f"{p['montant']:,.0f}"),
              ("Mode de paiement", p["mode"]), ("Solde restant", f"{p['solde_apres']:,.0f}")]
    y = h-105
    for k, v in lignes:
        c.setFont("Helvetica-Bold", 11); c.drawString(35, y, k + " :")
        c.setFont("Helvetica", 11); c.drawString(160, y, str(v)); y -= 24
    c.line(30, y, w-30, y)
    c.setFont("Helvetica-Oblique", 9); c.drawString(35, y-18, "Cachet et signature :")
    c.save()

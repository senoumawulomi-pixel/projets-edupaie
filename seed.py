"""Génère edupaie.db avec 18 élèves : soldés, partiels, non payés."""
import os, random
from edupaie.repository import Repository
from edupaie.service import Service
if os.path.exists("edupaie.db"): os.remove("edupaie.db")
svc = Service(Repository("edupaie.db")); random.seed(1)
noms = ["Adjovi","Kokou","Mensah","Agbodji","Amouzou","Dogbe","Tchalla","Akakpo","Lawson","Assogba",
        "Gbadamassi","Sossou","Attiogbe","Kpade","Ayivi","Zinsou","Aholou","Bakary"]
prenoms = ["Ama","Yao","Afi","Koffi","Essi","Komla","Sena","Kossi","Akou","Mawuli","Fatou","Edem","Jean","Rita","Paul","Awa","Luc","Nadia"]
for i, (n, p) in enumerate(zip(noms, prenoms)):
    total = random.choice([150000, 200000, 250000])
    eid = svc.creer_eleve(n, p, ["6e", "5e", "4e"][i % 3], "2026-2027", str(total))
    cible = [0, total, total // 2, total // 3][i % 4]
    dep, k = 0, 0
    while dep < cible:
        m = min(cible - dep, max(total // 5, 1)); k += 1
        svc.payer(eid, str(m), f"2026-{9 + (k % 3)}-{10 + k:02d}".replace("-9-", "-09-"), random.choice(["Espèces","Chèque","Virement","Mobile money"]))
        dep += m
print("OK edupaie.db")

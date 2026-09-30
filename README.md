# EduPaie — gestion des paiements scolaires
Python 3.10+, PySide6, SQLite (sqlite3), reportlab.

## Lancer
    pip install -r requirements.txt
    python seed.py      # crée edupaie.db (18 élèves de test)
    python main.py

## Architecture
- `edupaie/repository.py` : tout le SQL (couche données)
- `edupaie/service.py` : validation, solde, statuts, tableau de bord (métier)
- `edupaie/ui.py` : fenêtres PySide6, aucun SQL
- `edupaie/receipt.py` : PDF du reçu, généré depuis les données stockées (réimpression identique)
- `schema.sql` : script de création (tables `eleve`, `paiement`)

## Modèle (MCD)
ELEVE (1,1) —reçoit— (0,N) PAIEMENT.  Le solde et le statut sont calculés, jamais stockés
(seul `solde_apres` est figé dans le paiement pour que le reçu reste identique).

## Générer l'exécutable (sur Windows)
    pip install pyinstaller
    pyinstaller --onefile --windowed --add-data "schema.sql;." main.py
Placer `dist\main.exe` et `edupaie.db` dans le même dossier, puis double-cliquer sur l'exe.
Tester sur une machine sans Python avant la soutenance.

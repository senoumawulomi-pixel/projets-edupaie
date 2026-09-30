import sys, os
from PySide6.QtWidgets import QApplication, QMessageBox
from edupaie.repository import Repository
from edupaie.service import Service
from edupaie.ui import MainWindow

def db_path():
    base = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
    return os.path.join(base, "edupaie.db")   # .db placée à côté de l'exécutable

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        w = MainWindow(Service(Repository(db_path()))); w.show()
    except Exception as e:
        QMessageBox.critical(None, "Erreur au démarrage", str(e)); sys.exit(1)
    sys.exit(app.exec())

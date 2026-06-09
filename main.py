import os
import sys
import multiprocessing

# 1. FIX MULTIPROCESSING PER ESEGUIBILI (Obbligatorio per Nuitka/PyInstaller)
if __name__ == '__main__':
    multiprocessing.freeze_support()

# 2. GESTIONE PERCORSI INTELLIGENTE
# Se l'app gira come .exe compilato, usa il percorso dell'eseguibile, altrimenti usa __file__
if hasattr(sys, 'frozen'):
    root_dir = os.path.dirname(sys.executable)
else:
    root_dir = os.path.dirname(os.path.abspath(__file__))

if root_dir not in sys.path:
    sys.path.append(root_dir)

# Ora gli import funzioneranno sia in DEV che nel .exe compilato
from views.main_view import HelpDeskView
from controllers.main_controller import HelpDeskController

def main():
    app_view = HelpDeskView()
    app_controller = HelpDeskController(app_view)
    app_view.imposta_controller(app_controller)
    app_view.mainloop()

if __name__ == "__main__":
    main()
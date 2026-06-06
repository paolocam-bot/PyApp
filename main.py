import os
import sys

# Trova la cartella Root del progetto (HelpDeskApp)
root_dir = os.path.dirname(os.path.abspath(__file__))

# Aggiunge la Root a sys.path per gestire gli import in modo assoluto
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Ora possiamo importare dai vari pacchetti in modo pulito
from views.main_view import HelpDeskView
from controllers.main_controller import HelpDeskController

def main():
    app_view = HelpDeskView()
    app_controller = HelpDeskController(app_view)
    app_view.imposta_controller(app_controller)
    app_view.mainloop()

if __name__ == "__main__":
    main()
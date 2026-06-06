import os
import sys
import subprocess
from tkinter import messagebox  # O l'equivalente di CustomTkinter


def installa_driver_zebra():
    # Trova il percorso in cui si trova lo script Python (o l'eseguibile di PyInstaller)
    if getattr(sys, "frozen", False):
        # Se l'app è compilata con PyInstaller
        cartella_app = os.path.dirname(sys.executable)
    else:
        # Se stai eseguendo il file .py normalmente
        cartella_app = os.path.dirname(os.path.abspath(__file__))

    # Sostituisci con il nome esatto del tuo file .bat
    percorso_bat = os.path.join(cartella_app, "installa_zebra.bat")

    # Verifica se il file .bat esiste davvero in quella cartella
    if not os.path.exists(percorso_bat):
        messagebox.showerror(
            "Errore", f"File {percorso_bat} non trovato!"
        )
        return

    try:
        # Avvia il file .bat chiedendo i privilegi di amministratore (runas)
        # 'runas' farà apparire la classica finestra di Windows (UAC) che chiede "Vuoi consentire a questa app..."
        subprocess.Popen(
            ["powershell", "-Command", f"Start-Process '{percorso_bat}' -Verb RunAs"],
            shell=True,
        )
        messagebox.showinfo(
            "Info", "Avvio dell'installazione in corso. Accetta la richiesta di Windows."
        )

    except Exception as e:
        messagebox.showerror(
            "Errore", f"Impossibile avviare lo script: {e}"
        )
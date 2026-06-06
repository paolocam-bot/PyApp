import os
import sys
import sqlite3
import subprocess
from tkinter import messagebox
from models.ticket_model import Ticket

class HelpDeskController:
    def __init__(self, view):
        self.view = view
        self.inizializza_db()

    def inizializza_db(self):
        conn = sqlite3.connect("helpdesk.db")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticket (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titolo TEXT,
                urgenza TEXT,
                descrizione TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def salva_ticket(self):
        titolo = self.view.entry_titolo.get()
        urgenza = self.view.menu_urgenza.get()
        descrizione = self.view.txt_descrizione.get("0.0", "end").strip()
        
        if not titolo or descrizione == "Descrivi qui il problema...":
            messagebox.showwarning("Attenzione", "Compila tutti i campi!")
            return
            
        nuovo_ticket = Ticket(titolo=titolo, urgenza=urgenza, descrizione=descrizione)
        
        conn = sqlite3.connect("helpdesk.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ticket (titolo, urgenza, descrizione) VALUES (?, ?, ?)",
            (nuovo_ticket.titolo, nuovo_ticket.urgenza, nuovo_ticket.descrizione)
        )
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Successo", "Ticket salvato nel database!")
        self.view.entry_titolo.delete(0, "end")

    def ripristina_driver_zebra(self):
        # Cerca il .bat partendo dalla posizione dell'eseguibile o di main.py
        if getattr(sys, 'frozen', False):
            cartella_root = os.path.dirname(sys.executable)
        else:
            # Essendo dentro /controllers/, andiamo indietro di un livello per arrivare alla root
            cartella_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        percorso_bat = os.path.join(cartella_root, "installa_zebra.bat")
        
        if not os.path.exists(percorso_bat):
            messagebox.showerror("Errore", f"File '{percorso_bat}' non trovato nella root!")
            return
            
        try:
            subprocess.Popen(["powershell", "-Command", f"Start-Process '{percorso_bat}' -Verb RunAs"], shell=True)
            messagebox.showinfo("Driver", "Script avviato. Accetta i permessi di Windows.")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile avviare il file .bat: {e}")
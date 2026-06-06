import os
import sys
import sqlite3
import subprocess
from tkinter import messagebox
from models.ticket_model import Ticket
from models.manuale_model import Problema, StepRisoluzione

class HelpDeskController:
    def __init__(self, view):
        self.view = view
        
        # 1. Gestione dinamica del percorso del Database (Spostato dentro __init__)
        if getattr(sys, 'frozen', False):
            # Se l'app è compilata (Opzione 1: DB dentro l'eseguibile)
            # NOTA: Se invece usi l'Opzione 2 (cartella dist), cambia questa riga in:
            # self.db_path = os.path.join(os.path.dirname(sys.executable), "helpdesk.db")
            self.db_path = os.path.join(sys._MEIPASS, "helpdesk.db")
        else:
            # In modalità sviluppo (nella root PyApp)
            self.db_path = "helpdesk.db"
            
        self.inizializza_db()

    def ottieni_connessione(self):
        """Centralizza la connessione attivando le ottimizzazioni di SQLite."""
        conn = sqlite3.connect(self.db_path) # Usa la variabile dinamica!
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def inizializza_db(self):
        """Crea le tabelle del database se non esistono."""
        conn = self.ottieni_connessione()
        cursor = conn.cursor()
        
        # Tabella Ticket
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticket (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titolo TEXT,
                urgenza TEXT,
                descrizione TEXT
            )
        ''')
        
        # Tabella Macro-Problemi del Manuale
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manuale_problemi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                macro_categoria TEXT,
                sotto_categoria TEXT,
                titolo TEXT
            )
        ''')
        
        # Tabella Passaggi Step-by-Step (Collegata a manuale_problemi)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manuale_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_problema INTEGER,
                numero_passo INTEGER,
                testo TEXT,
                immagine_path TEXT,
                video_url TEXT,
                FOREIGN KEY (id_problema) REFERENCES manuale_problemi(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        
        # Popola il DB con dati dimostrativi se è completamente vuoto
        cursor.execute("SELECT COUNT(*) FROM manuale_problemi")
        if cursor.fetchone()[0] == 0:
            self.inserisci_dati_iniziali_manuale(cursor)
            conn.commit()
            
        conn.close()

    def inserisci_dati_iniziali_manuale(self, cursor):
        """Popola il DB la prima volta in assoluto per testare l'app."""
        # Problema 1
        cursor.execute(
            "INSERT INTO manuale_problemi (macro_categoria, sotto_categoria, titolo) VALUES (?, ?, ?)",
            ("Stampanti", "Zebra 420d", "La stampante salta le etichette o lampeggia in rosso")
        )
        id_prob1 = cursor.lastrowid
        cursor.execute("INSERT INTO manuale_steps (id_problema, numero_passo, testo, immagine_path, video_url) VALUES (?, ?, ?, ?, ?)",
                       (id_prob1, 1, "Spegnere la stampante dall'interruttore posteriore.", "assets/zebra_off.png", ""))
        cursor.execute("INSERT INTO manuale_steps (id_problema, numero_passo, testo, immagine_path, video_url) VALUES (?, ?, ?, ?, ?)",
                       (id_prob1, 2, "Tenere premuto il tasto Feed verde e riaccendere il dispositivo.", "assets/zebra_feed.png", ""))
        cursor.execute("INSERT INTO manuale_steps (id_problema, numero_passo, testo, immagine_path, video_url) VALUES (?, ?, ?, ?, ?)",
                       (id_prob1, 3, "Rilasciare il tasto quando lampeggia. La stampante si calibrerà.", "", "https://www.youtube.com/watch?v=calibra_zebra"))

        # Problema 2
        cursor.execute(
            "INSERT INTO manuale_problemi (macro_categoria, sotto_categoria, titolo) VALUES (?, ?, ?)",
            ("Rete", "Wi-Fi", "Il PC si disconnette continuamente dal Wi-Fi")
        )
        id_prob2 = cursor.lastrowid
        cursor.execute("INSERT INTO manuale_steps (id_problema, numero_passo, testo, immagine_path, video_url) VALUES (?, ?, ?, ?, ?)",
                       (id_prob2, 1, "Disattivare e riattivare il Wi-Fi di Windows.", "", ""))
        cursor.execute("INSERT INTO manuale_steps (id_problema, numero_passo, testo, immagine_path, video_url) VALUES (?, ?, ?, ?, ?)",
                       (id_prob2, 2, "Se non risolve, riavviare il PC aziendale.", "", ""))

    # --- FUNZIONI QUERY PER LA VIEW DEL MANUALE ---

    def ottieni_macro_categorie(self):
        """Ritorna la lista unica delle macro categorie presenti nel DB."""
        conn = self.ottieni_connessione()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT macro_categoria FROM manuale_problemi")
        risultati = [r[0] for r in cursor.fetchall()]
        conn.close()
        return risultati

    def ottieni_sotto_categorie(self, macro_categoria):
        """Ritorna le sotto-categorie associate a una specifica macro categoria."""
        conn = self.onn = self.ottieni_connessione()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT sotto_categoria FROM manuale_problemi WHERE macro_categoria = ?", (macro_categoria,))
        risultati = [r[0] for r in cursor.fetchall()]
        conn.close()
        return risultati

    def ottieni_problemi(self, macro, sotto):
        """Ritorna gli oggetti Problema filtrati per macro e sotto categoria."""
        conn = self.ottieni_connessione()
        cursor = conn.cursor()
        cursor.execute("SELECT id, titolo FROM manuale_problemi WHERE macro_categoria = ? AND sotto_categoria = ?", (macro, sotto))
        
        problemi = []
        for row in cursor.fetchall():
            problemi.append(Problema(id_problema=row[0], macro_categoria=macro, sotto_categoria=sotto, titolo=row[1]))
            
        conn.close()
        return problemi

    def ottieni_steps_problema(self, id_problema):
        """Ritorna la lista ordinata di step per un determinato problema."""
        conn = self.ottieni_connessione()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, numero_passo, testo, immagine_path, video_url FROM manuale_steps WHERE id_problema = ? ORDER BY numero_passo ASC",
            (id_problema,)
        )
        
        steps = []
        for row in cursor.fetchall():
            steps.append(StepRisoluzione(
                id_step=row[0], id_problema=id_problema, numero_passo=row[1],
                testo=row[2], immagine_path=row[3], video_url=row[4]
            ))
            
        conn.close()
        return steps

    def salva_ticket(self):
        # Recupera i dati dalla vista del ticket attraverso la main_view
        titolo = self.view.vista_ticket.entry_titolo.get()
        urgenza = self.view.vista_ticket.menu_urgenza.get()
        descrizione = self.view.vista_ticket.txt_descrizione.get("0.0", "end").strip()
        
        if not titolo or descrizione == "Descrivi qui il problema...":
            messagebox.showwarning("Attenzione", "Compila tutti i campi prima di inviare!")
            return
            
        conn = self.ottieni_connessione()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ticket (titolo, urgenza, descrizione) VALUES (?, ?, ?)",
            (titolo, urgenza, descrizione)
        )
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Successo", "Ticket salvato nel database locale!")
        self.view.vista_ticket.entry_titolo.delete(0, "end")
        self.view.vista_ticket.txt_descrizione.delete("0.0", "end")

    def ripristina_driver_zebra(self):
        if getattr(sys, 'frozen', False):
            cartella_root = os.path.dirname(sys.executable)
        else:
            cartella_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        percorso_bat = os.path.join(cartella_root, "installa_zebra.bat")
        
        if not os.path.exists(percorso_bat):
            messagebox.showerror("Errore", f"File '{percorso_bat}' non trovato!")
            return
            
        try:
            subprocess.Popen(["powershell", "-Command", f"Start-Process '{percorso_bat}' -Verb RunAs"], shell=True)
            messagebox.showinfo("Driver", "Script avviato. Accetta la richiesta UAC di Windows.")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile avviare il file .bat: {e}")
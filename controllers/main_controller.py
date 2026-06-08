import os
import sys
import sqlite3
import subprocess
import shutil
from tkinter import messagebox
from tkinter import messagebox
from models.ticket_model import Ticket
from models.manuale_model import Problema, StepRisoluzione

class HelpDeskController:
    def __init__(self, view):
        self.view = view
        
        # 1. Gestione dinamica del percorso del Database
        if getattr(sys, 'frozen', False):
            self.db_path = os.path.join(sys._MEIPASS, "helpdesk.db")
        else:
            self.db_path = "helpdesk.db"
            
        self.inizializza_db()

    def ottieni_connessione(self):
        """Centralizza la connessione attivando le ottimizzazioni di SQLite."""
        conn = sqlite3.connect(self.db_path)
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
        conn = self.ottieni_connessione()
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
        
        messagebox.showinfo("Successo", "Ticket saved into local database!")
        self.view.vista_ticket.entry_titolo.delete(0, "end")
        self.view.vista_ticket.txt_descrizione.delete("0.0", "end")

    def ripristina_driver_zebra(self):
        cartella_root = os.path.dirname(os.path.abspath(sys.argv[0]))
        # AGGIORNATO: puntiamo alla sottocartella scripts
        percorso_bat = os.path.join(cartella_root, "scripts", "ZebraDriver.bat") 
        
        if not os.path.exists(percorso_bat):
            messagebox.showerror("Errore", f"File '{percorso_bat}' non trovato!")
            return
            
        try:
            # Avvia il file .bat forzando la richiesta di Amministratore (UAC) tramite PowerShell
            subprocess.Popen(["powershell", "-Command", f"Start-Process '{percorso_bat}' -Verb RunAs"], shell=True)
            messagebox.showinfo("Driver", "Script avviato. Accetta la richiesta UAC di Windows.")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile avviare lo script: {e}")


    def ripristina_input_hardware(self):
        cartella_root = os.path.dirname(os.path.abspath(sys.argv[0]))
        # AGGIORNATO: puntiamo alla sottocartella scripts
        percorso_bat = os.path.join(cartella_root, "scripts", "RipristinaInput.bat")
        
        if not os.path.exists(percorso_bat):
            messagebox.showerror("Errore", f"File '{percorso_bat}' non trovato!")
            return
            
        try:
            # Esegue il file .bat richiedendo i diritti di amministratore tramite PowerShell
            subprocess.Popen(["powershell", "-Command", f"Start-Process '{percorso_bat}' -Verb RunAs"], shell=True)
            messagebox.showinfo("Reset Hardware", "Procedura avviata! Clicca su 'SÌ' nella finestra di Windows che sta per apparire.")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile avviare il ripristino: {e}")

    # =========================================================================
    # --- METODI ADMIN GESTIONE DATABASE (Ora indentati dentro la classe!) ---
    # =========================================================================

    def carica_tabella_admin(self):
        """Svuota la tabella grafica dell'admin e la ripopola con i dati delle due tabelle collegate."""
        admin_v = self.view.vista_admin
        for row in admin_v.tabella.get_children():
            admin_v.tabella.delete(row)
            
        try:
            conn = self.ottieni_connessione()
            cursor = conn.cursor()
            # Uniamo le due tabelle con una JOIN per mostrare Categoria, Problema e gli Step associati
            cursor.execute('''
                SELECT s.id, p.macro_categoria, p.titolo, s.numero_passo, s.testo 
                FROM manuale_steps s
                JOIN manuale_problemi p ON s.id_problema = p.id
                ORDER BY p.macro_categoria, p.titolo, s.numero_passo
            ''')
            righe = cursor.fetchall()
            conn.close()
            
            for riga in righe:
                admin_v.tabella.insert("", "end", values=riga)
        except Exception as e:
            print(f"Errore nel caricamento della tabella admin: {e}")

    def recupera_media_per_form(self, id_step):
        """Trova i path multimediali dello step selezionato e li scrive nel campo di input."""
        try:
            conn = self.ottieni_connessione()
            cursor = conn.cursor()
            cursor.execute("SELECT immagine_path FROM manuale_steps WHERE id = ?", (id_step,))
            risultato = cursor.fetchone()
            conn.close()
            
            if risultato:
                self.view.vista_admin.ent_path_media.delete(0, "end")
                self.view.vista_admin.ent_path_media.insert(0, risultato[0] if risultato[0] else "")
        except Exception as e:
            print(e)

    def aggiungi_guida_db(self):
        """Inserisce un nuovo step copiando automaticamente l'immagine in assets se esterna."""
        admin_v = self.view.vista_admin
        
        categoria = admin_v.ent_categoria.get().strip()
        problema = admin_v.ent_problema.get().strip()
        step_num = admin_v.ent_step_num.get().strip()
        descrizione = admin_v.txt_descrizione.get("0.0", "end").strip()
        path_media_originale = admin_v.ent_path_media.get().strip()
        
        if not categoria or not problema or not step_num or not descrizione:
            messagebox.showwarning("Attenzione", "Compila tutti i campi principali!")
            return
            
        # --- GESTIONE AUTOMATICA COPIA IMMAGINE ---
        path_media_finale = ""
        if path_media_originale and os.path.exists(path_media_originale):
            try:
                # 1. Crea la cartella assets se per caso non esiste
                os.makedirs("assets", exist_ok=True)
                
                # 2. Estrae solo il nome del file (es. da "C:/Scrivania/foto.png" a "foto.png")
                nome_file = os.path.basename(path_media_originale)
                path_destinazione = os.path.join("assets", nome_file)
                
                # Normalizziamo i percorsi per evitare falsi controlli differenti scritti male
                assoluto_originale = os.path.abspath(path_media_originale)
                assoluto_destinazione = os.path.abspath(path_destinazione)
                
                # 3. Se il file non è già dentro la cartella assets, lo copia fisicamente
                if assoluto_originale != assoluto_destinazione:
                    shutil.copy2(path_media_originale, path_destinazione)
                
                # Il percorso che salveremo nel database sarà sempre quello standard locale
                path_media_finale = f"assets/{nome_file}"
                
            except Exception as e:
                messagebox.showerror("Errore Media", f"Impossibile copiare l'immagine in assets: {e}")
                return
        
        # --- SALVATAGGIO NEL DATABASE ---
        try:
            conn = self.ottieni_connessione()
            cursor = conn.cursor()
            
            # 1. Controlla se il problema esiste già
            cursor.execute('''
                SELECT id FROM manuale_problemi 
                WHERE macro_categoria = ? AND titolo = ?
            ''', (categoria, problema))
            res = cursor.fetchone()
            
            if res:
                id_problema = res[0]
            else:
                cursor.execute('''
                    INSERT INTO manuale_problemi (macro_categoria, sotto_categoria, titolo)
                    VALUES (?, ?, ?)
                ''', (categoria, categoria, problema))
                id_problema = cursor.lastrowid
            
            # 2. Inserisce lo step usando il path_media_finale (es. assets/foto.png)
            cursor.execute('''
                INSERT INTO manuale_steps (id_problema, numero_passo, testo, immagine_path, video_url)
                VALUES (?, ?, ?, ?, ?)
            ''', (id_problema, int(step_num), descrizione, path_media_finale, ""))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Successo", "Nuovo step e immagine salvati correttamente!")
            admin_v.svuota_form()
            self.carica_tabella_admin()
            self.view.vista_manuale.inizializza_manuale(self)
            
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile aggiungere la guida: {e}")

    def modifica_guida_db(self):
        """Aggiorna lo step, copia la nuova immagine in assets e pulisce la vecchia se inutilizzata."""
        admin_v = self.view.vista_admin
        if not admin_v.id_selezionato:
            messagebox.showwarning("Attenzione", "Seleziona prima uno step dalla tabella!")
            return
            
        path_media_nuovo_input = admin_v.ent_path_media.get().strip()
        
        try:
            conn = self.ottieni_connessione()
            cursor = conn.cursor()
            
            # 1. Recuperiamo il percorso della VECCHIA immagine prima di fare qualsiasi modifica
            cursor.execute("SELECT immagine_path FROM manuale_steps WHERE id = ?", (admin_v.id_selezionato,))
            riga_vecchia = cursor.fetchone()
            path_media_vecchio = riga_vecchia[0] if riga_vecchia else None
            
            # --- GESTIONE AUTOMATICA COPIA E PULIZIA IN MODIFICA ---
            path_media_finale = ""
            
            if path_media_nuovo_input:
                # Se l'utente ha inserito un percorso che esiste fisicamente sul disco (es. da Desktop)
                if os.path.exists(path_media_nuovo_input):
                    try:
                        os.makedirs("assets", exist_ok=True)
                        nome_file = os.path.basename(path_media_nuovo_input)
                        path_destinazione = os.path.join("assets", nome_file)
                        
                        assoluto_originale = os.path.abspath(path_media_nuovo_input)
                        assoluto_destinazione = os.path.abspath(path_destinazione)
                        
                        # Copia la nuova immagine solo se non si trova già dentro assets
                        if assoluto_originale != assoluto_destinazione:
                            shutil.copy2(path_media_nuovo_input, path_destinazione)
                        
                        path_media_finale = f"assets/{nome_file}"
                    except Exception as e:
                        messagebox.showerror("Errore Media", f"Impossibile copiare la nuova immagine in assets: {e}")
                        conn.close()
                        return
                else:
                    # Se l'utente non ha cambiato l'immagine (nel form c'è scritto ancora il vecchio 'assets/foto.png')
                    path_media_finale = path_media_nuovo_input
            
            # 2. SE L'IMMAGINE È CAMBIATA, controlliamo se dobbiamo eliminare dal disco quella vecchia
            if path_media_vecchio and path_media_vecchio != path_media_finale and path_media_vecchio.strip() != "":
                # Chiediamo al DB quanti ALTRI step usano la vecchia immagine
                cursor.execute("SELECT COUNT(*) FROM manuale_steps WHERE immagine_path = ? AND id != ?", 
                               (path_media_vecchio, admin_v.id_selezionato))
                conteggio_usi_vecchia = cursor.fetchone()[0]
                
                # Se nessun altro la usa ed esiste sul disco, la eliminiamo
                if conteggio_usi_vecchia == 0 and os.path.exists(path_media_vecchio):
                    try:
                        os.remove(path_media_vecchio)
                    except Exception as e:
                        print(f"Impossibile rimuovere la vecchia immagine orfana {path_media_vecchio}: {e}")

            # 3. Aggiorniamo i dati dello step nel Database
            cursor.execute('''
                UPDATE manuale_steps 
                SET numero_passo = ?, testo = ?, immagine_path = ?
                WHERE id = ?
            ''', (
                int(admin_v.ent_step_num.get()), 
                admin_v.txt_descrizione.get("0.0", "end").strip(), 
                path_media_finale, 
                admin_v.id_selezionato
            ))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Successo", "Modifiche salvate e cartella assets ottimizzata!")
            admin_v.svuota_form()
            self.carica_tabella_admin()
            self.view.vista_manuale.inizializza_manuale(self)
            
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile modificare lo step: {e}")

    def elimina_guida_db(self):
        """Cancella lo step dal DB e rimuove l'immagine da assets se non è usata da altre guide."""
        admin_v = self.view.vista_admin
        if not admin_v.id_selezionato:
            messagebox.showwarning("Attenzione", "Seleziona prima un elemento da eliminare!")
            return
            
        conferma = messagebox.askyesno("Conferma", "Vuoi eliminare definitivamente questo step?")
        if conferma:
            try:
                conn = self.ottieni_connessione()
                cursor = conn.cursor()
                
                # 1. Recuperiamo il percorso dell'immagine associata a QUESTO step specifico
                cursor.execute("SELECT immagine_path FROM manuale_steps WHERE id = ?", (admin_v.id_selezionato,))
                riga = cursor.fetchone()
                immagine_da_controllare = riga[0] if riga else None
                
                # 2. Eliminiamo lo step dal database
                cursor.execute("DELETE FROM manuale_steps WHERE id = ?", (admin_v.id_selezionato,))
                conn.commit()
                
                # 3. Se lo step aveva un'immagine, controlliamo se è usata da qualcun altro ORA
                if immagine_da_controllare and immagine_da_controllare.strip() != "":
                    cursor.execute("SELECT COUNT(*) FROM manuale_steps WHERE immagine_path = ?", (immagine_da_controllare,))
                    conteggio_usi = cursor.fetchone()[0]
                    
                    # Se il conteggio è 0, significa che nessun'altra guida usa questa foto
                    if conteggio_usi == 0 and os.path.exists(immagine_da_controllare):
                        try:
                            os.remove(immagine_da_controllare)
                        except Exception as e:
                            print(f"Impossibile eliminare il file fisico {immagine_da_controllare}: {e}")
                
                conn.close()
                
                messagebox.showinfo("Eliminato", "Step rimosso dal database (e file multimediale ripulito se inutilizzato).")
                admin_v.svuota_form()
                self.carica_tabella_admin()
                self.view.vista_manuale.inizializza_manuale(self)
                
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile eliminare lo step: {e}")


    
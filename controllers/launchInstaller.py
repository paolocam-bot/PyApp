import json
import os
import glob
import sys
import subprocess
import urllib.request
from tkinter import messagebox
import customtkinter as ctk


GITHUB_RELEASE_URL = "https://api.github.com/repos/paolocam-bot/PyApp/releases/latest"

# =====================================================================
# 1. FUNZIONI DI UTILITY E AGGIORNAMENTO (Globali)
# =====================================================================

def get_app_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    current_file = os.path.abspath(__file__)
    # Risale di due cartelle per trovare la Root del progetto
    return os.path.dirname(os.path.dirname(current_file))


def scarica_asset(asset, destination_folder):
    name = asset.get("name")
    url = asset.get("browser_download_url")
    if not name or not url:
        raise ValueError("Asset GitHub non valido: manca name o browser_download_url")

    destination = os.path.join(destination_folder, name)
    if os.path.exists(destination):
        return False, destination

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Python-urllib/3.11",
            "Accept": "application/octet-stream",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()

    with open(destination, "wb") as handle:
        handle.write(data)

    return True, destination


def scarica_asset_mancanti():
    cartella_app = get_app_base_dir()
    try:
        request = urllib.request.Request(
            GITHUB_RELEASE_URL,
            headers={
                "User-Agent": "Python-urllib/3.11",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            release_data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        messagebox.showerror(
            "Errore aggiornamento",
            f"Impossibile leggere le release GitHub: {e}"
        )
        return None

    assets = release_data.get("assets", [])
    if not assets:
        messagebox.showinfo(
            "Aggiornamento",
            "Nessun asset trovato nell'ultima release GitHub."
        )
        return []

    scaricati = []
    for asset in assets:
        try:
            was_downloaded, _ = scarica_asset(asset, cartella_app)
            if was_downloaded:
                scaricati.append(asset.get("name"))
        except Exception as e:
            messagebox.showerror(
                "Errore download asset",
                f"Impossibile scaricare {asset.get('name', 'asset sconosciuto')}: {e}"
            )
            return None

    return scaricati

# =====================================================================
# 2. CLASSE CONTROLLER (Ospita le funzioni che usano self)
# =====================================================================

class PrinterManagerController:
    def __init__(self):
        pass

    def esegui_singolo_comando_sicuro(self, comando, cartella_lavoro=None):
        """
        Metodo di supporto per eseguire i comandi di sistema.
        Nota: Assicurati che questo metodo sia identico a quello che usi già.
        """
        try:
            risultato = subprocess.run(
                comando, 
                cwd=cartella_lavoro, 
                shell=True, 
                capture_output=True, 
                text=True
            )
            return risultato.returncode == 0
        except Exception as e:
            print(f"Errore esecuzione comando {comando}: {e}")
            return False

    def installa_driver_zebra(self):
        cartella_app = get_app_base_dir()
        percorso_bat = os.path.join(cartella_app, "scripts", "installa_zebra.bat")

        if not os.path.exists(percorso_bat):
            messagebox.showerror("Errore", f"File {percorso_bat} non trovato!")
            return

        try:
            subprocess.Popen(
                ["powershell", "-Command", f"Start-Process '{percorso_bat}' -Verb RunAs"],
                shell=True,
            )
            messagebox.showinfo(
                "Info", "Avvio dell'installazione in corso. Accetta la richiesta di Windows."
            )
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile avviare lo script: {e}")

    def aggiorna_app(self):
        cartella_app = get_app_base_dir()
        scaricati = scarica_asset_mancanti()
        if scaricati is None:
            return

        if scaricati:
            messagebox.showinfo(
                "Aggiornamento",
                "Scaricati gli asset mancanti dalla release GitHub:\n" + "\n".join(scaricati)
            )
        else:
            messagebox.showinfo(
                "Aggiornamento",
                "Tutti gli asset relativi all'ultima release sono già presenti localmente."
            )

        percorso_bat = os.path.join(cartella_app, "scripts", "aggiornamento.bat")
        if not os.path.exists(percorso_bat):
            messagebox.showerror("Errore", f"File {percorso_bat} non trovato!")
            return

        try:
            subprocess.Popen(
                ["powershell", "-Command", f"Start-Process '{percorso_bat}' -Verb RunAs"],
                shell=True,
            )
            messagebox.showinfo(
                "Info", "Aggiornamento in corso. Accetta la richiesta di Windows."
            )
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile avviare lo script di aggiornamento: {e}")

    def cmd_pulizia_spooler_stampa(self):
        print("\n=== INIZIO PULIZIA SPOOLER DI STAMPA ===")
        
        print("Arresto del servizio Spooler di stampa...")
        self.esegui_singolo_comando_sicuro(["net", "stop", "spooler"])

        cartella_printers = r"C:\Windows\System32\spool\PRINTERS"
        print(f"Svuotamento dei file di stampa bloccati in: {cartella_printers}")
        
        try:
            file_bloccati = glob.glob(os.path.join(cartella_printers, "*"))
            for f in file_bloccati:
                try:
                    os.remove(f)
                    print(f" -> Eliminato file di spool: {os.path.basename(f)}")
                except Exception as e:
                    print(f" [AVVISO] Impossibile eliminare {os.path.basename(f)}: {e}")
        except Exception as e:
            print(f" [ERRORE] Errore durante l'accesso alla cartella PRINTERS: {e}")

        print("Riavvio del servizio Spooler di stampa...")
        esito = self.esegui_singolo_comando_sicuro(["net", "start", "spooler"])
        
        if esito:
            print("=== COMPLETATO: Spooler di stampa ripulito e riavviato! ===")
        else:
            print("=== ERRORE: Impossibile riavviare lo spooler. Verificare i permessi Admin! ===")

    def cmd_refresh_internet_sicuro(self):
        print("\n=== INIZIO REFRESH RETE INTERNET (IP STATICO PRESERVATO) ===")
        
        print("Svuotamento della cache DNS (FlushDNS)...")
        self.esegui_singolo_comando_sicuro(["ipconfig", "/flushdns"])
        
        print("Ripristino del catalogo Winsock...")
        self.esegui_singolo_comando_sicuro(["netsh", "winsock", "reset"])
        
        print("Purging e ricaricamento della tabella dei nomi NetBIOS...")
        self.esegui_singolo_comando_sicuro(["nbtstat", "-R"])
        
        print("=== COMPLETATO: Refresh di rete eseguito con successo! ===")
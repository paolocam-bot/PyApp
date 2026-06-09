import concurrent.futures
import socket
import threading
import win32print
import win32api
import win32con
import sys
import subprocess
import platform
import time
import os
from tkinter import messagebox
from zebra import Zebra


class PrinterManagerController:

    def __init__(self, vista_stampanti):
        self.vista_stampanti = vista_stampanti

    def cmd_rileva_stampanti(self, mostra_popup_esito=False):
        """Avvia lo scanner automatico unificato USB + IP."""
        self.vista_stampanti.cmb_dispositivo.set("Scansione hardware in corso...")
        threading.Thread(
            target=self._esegui_scansione_unificata,
            args=(mostra_popup_esito,),
            daemon=True,
        ).start()

    def _esegui_scansione_unificata(self, mostra_popup):
        dispositivi_finali = []

        try:
            z = Zebra()
            code_sistema = z.getqueues()
            for coda in code_sistema:
                dispositivi_finali.append(coda)
        except Exception as e:
            print(f"Errore scansione USB tramite libreria Zebra: {e}")

        sottorete = "192.168.1."
        ips_da_testare = [f"{sottorete}{i}" for i in range(1, 255)]

        def controlla_singolo_ip(ip):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.1)
                s.connect((ip, 9100))
                s.close()
                return f"{ip} (Rete IP)"
            except:
                return None

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                risultati = executor.map(controlla_singolo_ip, ips_da_testare)
                for ris in risultati:
                    if ris:
                        dispositivi_finali.append(ris)
        except Exception as e:
            print(f"Errore scansione di rete: {e}")

        self.vista_stampanti.after(
            100,
            lambda: self._elabora_risultati_gui(dispositivi_finali, mostra_popup),
        )

    def _elabora_results_gui(self, dispositivi, mostra_popup):
        self._elabora_risultati_gui(dispositivi, mostra_popup)

    def _elabora_risultati_gui(self, dispositivi, mostra_popup):
        if dispositivi:
            self.vista_stampanti.cmb_dispositivo.configure(state="normal")
            self.vista_stampanti.cmb_dispositivo.configure(values=dispositivi)
            self.vista_stampanti.cmb_dispositivo.set(dispositivi[0])

            if mostra_popup:
                messagebox.showinfo(
                    "HardwareHero",
                    f"Riconfigurazione completata!\nTrovate {len(dispositivi)} stampanti pronte all'uso.",
                )
        else:
            self.vista_stampanti.cmb_dispositivo.configure(values=["Nessuna stampante collegata"])
            self.vista_stampanti.cmb_dispositivo.set("Nessuna stampante collegata")
            messagebox.showerror(
                "Errore Hardware",
                "Nessuna stampante collegata!\n\nVerifica che la Zebra sia accesa e collegata.",
            )

    def cmd_riallinea_stampante(self):
        """Esegue la simulazione software del tasto FEED e ricalibra i sensori."""
        dati = self.vista_stampanti.get_dati_interfaccia()
        tipo = dati.get("tipo", "USB")
        target = dati.get("target", "").strip()

        if not target or "Nessuna" in target:
            messagebox.showwarning("Azione Annullata", "Nessuna stampante selezionata.")
            return

        # STRATEGIA DI SIMULAZIONE FEED E PULIZIA COMANDI:
        # Inseriamo i ritorni a capo (\n) per forzare il firmware a processare i blocchi in sequenza.
        # ~PS simula la pressione fisica del FEED. ~jc forza la calibrazione fustella. ^JUS salva tutto.
        stringa_zpl_calibrazione = "^XA\n~PS\n^XZ\n^XA\n~jc\n^JUS\n^XZ\n"

        if tipo == "USB":
            try:
                import win32print
                
                # Convertiamo esplicitamente in byte ASCII puliti
                dati_raw = stringa_zpl_calibrazione.encode("ascii")
                
                # Invio diretto allo spooler di Windows in modalità RAW (Bypassa la libreria Zebra)
                handle = win32print.OpenPrinter(target)
                job = win32print.StartDocPrinter(handle, 1, ("Simulazione_Feed_ZPL", None, "RAW"))
                win32print.StartPagePrinter(handle)
                win32print.WritePrinter(handle, dati_raw)
                win32print.EndPagePrinter(handle)
                win32print.EndDocPrinter(handle)
                win32print.ClosePrinter(handle)
                
                messagebox.showinfo(
                    "Simulazione FEED USB",
                    f"Comando RAW di simulazione FEED e calibrazione inviato a: {target}\n\n"
                    "La stampante eseguirà l'avanzamento e salverà la misura in memoria.",
                )
            except Exception as e:
                messagebox.showerror("Errore USB", f"Dettaglio errore hardware/driver: {e}")
        else:
            # Connessione di Rete IP (Porta 9100)
            try:
                ip_pulito = target.replace(" (Rete IP)", "").strip()
                
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3.0)
                s.connect((ip_pulito, 9100))
                
                # Invio in puro formato ASCII (fondamentale per i PrintServer Zebra rispetto a UTF-8)
                s.sendall(stringa_zpl_calibrazione.encode("ascii"))
                s.close()
                
                messagebox.showinfo(
                    "Simulazione FEED Rete", 
                    f"Comando FEED e calibrazione inviato correttamente all'IP: {ip_pulito}"
                )
            except Exception as e:
                messagebox.showerror("Errore Rete", f"Dettaglio errore di connessione: {e}")

    def cmd_click_status(self):
        """Invia un comando RAW per costringere la stampante a stampare lo stato dei sensori."""
        dati = self.vista_stampanti.get_dati_interfaccia()
        tipo = dati.get("tipo", "USB")
        target = dati.get("target", "").strip()

        if not target or "Nessuna" in target:
            return

        if tipo == "USB":
            try:
                z = Zebra()
                z.setqueue(target)
                z.output("~WC") 
                messagebox.showinfo(
                    "Diagnostica Hardware", 
                    f"Comando di autodiagnostica inviato a '{target}'.\n\n"
                    "La stampante sta stampando la configurazione dei sensori su etichetta."
                )
            except Exception as e:
                messagebox.showerror("Errore RAW", f"Impossibile inviare il comando: {e}")

    def cmd_riavvia_stampante(self):
        """Invia un comando di Reset hardware ZPL (~JR)."""
        dati = self.vista_stampanti.get_dati_interfaccia()
        tipo = dati.get("tipo", "USB")
        target = dati.get("target", "").strip()

        if not target or "Nessuna" in target:
            return

        if tipo == "USB":
            try:
                z = Zebra()
                z.setqueue(target)
                z.output("~JR")
                messagebox.showinfo("Reset USB", f"Comando di reset inviato a: {target}")
            except Exception as e:
                messagebox.showerror("Errore USB", f"Dettaglio errore: {e}")
        else:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((target.replace(" (Rete IP)", ""), 9100))
                s.sendall(b"~JR")
                s.close()
                messagebox.showinfo("Reset Rete", f"Comando di reset inviato a: {target}")
            except Exception as e:
                messagebox.showerror("Errore Rete", f"Dettaglio errore: {e}")

    def cmd_stampa_prova(self):
        """Invia un'etichetta ZPL reale alla stampante tramite output."""
        dati = self.vista_stampanti.get_dati_interfaccia()
        tipo = dati.get("tipo", "USB")
        target = dati.get("target", "").strip()

        if not target or "Nessuna" in target:
            messagebox.showwarning("Azione Annullata", "Nessuna stampante selezionata.")
            return

        if "GARANZIE" in target.upper():
            stringa_zpl = "^XA^FO20,20^GB280,200,4^FS^FO50,90^A0N,40,40^FDGARANZIE OK^FS^XZ"
        else:
            stringa_zpl = "^XA^FO40,40^GB480,720,4^FS^FO80,350^A0N,60,60^FDZEBRA 7x10 OK^FS^XZ"

        if tipo == "USB":
            try:
                z = Zebra()
                z.setqueue(target)
                z.output(stringa_zpl)
                messagebox.showinfo(
                    "Stampa di Prova USB",
                    f"Etichetta di prova inviata con successo a: {target}",
                )
            except Exception as e:
                messagebox.showerror("Errore USB", f"Dettaglio errore: {e}")
        else:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((target.replace(" (Rete IP)", ""), 9100))
                s.sendall(stringa_zpl.encode("utf-8"))
                s.close()
                messagebox.showinfo(
                    "Stampa di Prova Rete",
                    f"Etichetta di prova inviata con successo a IP: {target}",
                )
            except Exception as e:
                messagebox.showerror("Errore Rete", f"Dettaglio errore: {e}")

    def cmd_aggiorna_preferenze_windows(self):
        """Modifica le impostazioni di stampa avanzate (DevMode) direttamente in Windows."""
        dati = self.vista_stampanti.get_dati_interfaccia()
        target = dati.get("target", "").strip()

        if not target or "Nessuna" in target:
            return

        if "GARANZIE" in target.upper():
            larghezza_mm_10 = 400  
            altezza_mm_10 = 300    
            info = "GARANZIE (4x3 cm)"
        elif "ZEBRA" in target.upper():
            larghezza_mm_10 = 700  
            altezza_mm_10 = 1000   
            info = "ZEBRA (7x10 cm)"
        else:
            return

        try:
            PRINTER_ACCESS_ADMINISTER = 0x00000004
            PRINTER_ACCESS_USE = 0x00000008
            differenze = {"DesiredAccess": PRINTER_ACCESS_ADMINISTER | PRINTER_ACCESS_USE}
            
            hPrinter = win32print.OpenPrinter(target, differenze)
            try:
                info_stampante = win32print.GetPrinter(hPrinter, 2)
                devmode = info_stampante['pDevMode']
                
                devmode.PaperWidth = larghezza_mm_10
                devmode.PaperLength = altezza_mm_10
                devmode.Fields |= win32print.DM_PAPERWIDTH | win32print.DM_PAPERLENGTH
                
                win32print.SetPrinter(hPrinter, 2, info_stampante, 0)
                messagebox.showinfo("Proprietà Windows Aggiornate", f"Profilo applicato: {info}")
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            print(f"Errore aggiornamento preferenze: {e}")

    def setta_formato_zebra_etichette(self):
        try:
            lista_stampanti = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]
            lista_maiuscola = [nome.strip().upper() for nome in lista_stampanti]

            if "ZEBRA" in lista_maiuscola:
                idx = lista_maiuscola.index("ZEBRA")
                nome_reale = lista_stampanti[idx]
                try:
                    p_handle = win32print.OpenPrinter(nome_reale, {"DesiredAccess": win32print.PRINTER_ALL_ACCESS})
                    info = win32print.GetPrinter(p_handle, 2)
                    devmode = info['pDevMode']
                    devmode.Fields |= (win32con.DM_ORIENTATION | win32con.DM_PAPERSIZE | win32con.DM_PAPERWIDTH | win32con.DM_PAPERLENGTH)
                    devmode.Orientation = win32con.DMORIENT_LANDSCAPE
                    devmode.PaperSize = 0  
                    devmode.PaperWidth = 700   
                    devmode.PaperLength = 1000 
                    win32print.SetPrinter(p_handle, 2, info, 0)
                    win32print.ClosePrinter(p_handle)
                except Exception as e:
                    print(f"Errore configurazione ZEBRA: {e}")

            if "GARANZIE" in lista_maiuscola:
                idx = lista_maiuscola.index("GARANZIE")
                nome_reale = lista_stampanti[idx]
                try:
                    p_handle = win32print.OpenPrinter(nome_reale, {"DesiredAccess": win32print.PRINTER_ALL_ACCESS})
                    info = win32print.GetPrinter(p_handle, 2)
                    devmode = info['pDevMode']
                    devmode.Fields |= (win32con.DM_ORIENTATION | win32con.DM_PAPERSIZE | win32con.DM_PAPERWIDTH | win32con.DM_PAPERLENGTH)
                    devmode.Orientation = win32con.DMORIENT_LANDSCAPE
                    devmode.PaperSize = 0  
                    devmode.PaperWidth = 400  
                    devmode.PaperLength = 300 
                    win32print.SetPrinter(p_handle, 2, info, 0)
                    win32print.ClosePrinter(p_handle)
                except Exception as e:
                    print(f"Errore configurazione GARANZIE: {e}")
        except Exception as e:
            print(f"Errore generale: {e}")

    def cmd_scambia_porte_zebra(self):
        try:
            lista_stampanti = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL, None, 2)
            porta_attuale_zebra = None
            porta_attuale_garanzie = None
            
            for stampante in lista_stampanti:
                nome = stampante['pPrinterName'].strip().upper()
                porta = stampante['pPortName'] 
                if nome == "ZEBRA":
                    porta_attuale_zebra = porta.upper()
                elif nome == "GARANZIE":
                    porta_attuale_garanzie = porta.upper()

            if not porta_attuale_zebra or not porta_attuale_garanzie:
                return

            if "USB001" in porta_attuale_zebra:
                nuova_porta_zebra = "USB002"
                nuova_porta_garanzie = "USB001"
            else:
                nuova_porta_zebra = "USB001"
                nuova_porta_garanzie = "USB002"

            subprocess.run(f'rundll32 printui.dll,PrintUIEntry /Xs /n "ZEBRA" PortName "{nuova_porta_zebra}"', shell=True)
            subprocess.run(f'rundll32 printui.dll,PrintUIEntry /Xs /n "GARANZIE" PortName "{nuova_porta_garanzie}"', shell=True)
        except Exception as e:
            print(f"Errore scambio porte: {e}")

    def cmd_forza_formato_fustella_finale(self):
        try:
            for nome_stampante in ["ZEBRA", "GARANZIE"]:
                script_ps = f"Set-PrintConfiguration -PrinterName '{nome_stampante}' -PaperSize 'UserDefined' -LabelHeight 70mm -LabelWidth 100mm -Orientation Landscape"
                subprocess.run(["powershell", "-NoProfile", "-Command", script_ps], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            comandi_zpl = b"~jc^XA^JUS^XZ"
            for nome_stampante in ["ZEBRA", "GARANZIE"]:
                try:
                    handle = win32print.OpenPrinter(nome_stampante)
                    win32print.StartDocPrinter(handle, 1, ("Calibrazione_Fustella", None, "RAW"))
                    win32print.StartPagePrinter(handle)
                    win32print.WritePrinter(handle, comandi_zpl)
                    win32print.EndPagePrinter(handle)
                    win32print.EndDocPrinter(handle)
                    win32print.ClosePrinter(handle)
                except Exception:
                    print(f" -> Nota: Taratura hardware via USB non riuscita for {nome_stampante}")
            return True
        except Exception as e:
            print(f"Errore: {e}")
            return False
        


    def noncliccare(self):
        """
        Easter egg avanzato: stampa un'etichetta con cornice nera perimetrale,
        testo in grassetto e tutto maiuscolo, formattato per evitare la stampa dei codici.
        """
        dati = self.vista_stampanti.get_dati_interfaccia()
        tipo = dati.get("tipo", "USB")
        target = dati.get("target", "").strip()

        testo_insulto = "MA ALLORA SEI STRONZO"
        print(f"[Easter Egg Layout] {testo_insulto} (Invio a {target})")

        if not target or "Nessuna" in target:
            return

        # LA STRINGA DEVE ESSERE IN LINEA CONTINUA E SENZA SPAZI AD INIZIO RIGA
        # Altrimenti la stampante non riconosce i caratteri di controllo ^ e ~
        stringa_zpl = f"^XA^LH5,5^FO0,0^GB310,230,4^FS^FO5,75^A0N,30,30^FB300,2,0,C^FDMA ALLORA\&SEI STRONZO^FS^XZ"
        if tipo == "USB":
            try:
                import win32print
                # Usiamo la codifica 'ascii' pura
                dati_raw = stringa_zpl.encode("ascii")
                
                handle = win32print.OpenPrinter(target)
                # Il tipo di documento DEVE essere passato come "RAW" per dire a Windows: "Non toccare questi codici!"
                job = win32print.StartDocPrinter(handle, 1, ("Easter_Egg_Cornice", None, "RAW"))
                win32print.StartPagePrinter(handle)
                win32print.WritePrinter(handle, dati_raw)
                win32print.EndPagePrinter(handle)
                win32print.EndDocPrinter(handle)
                win32print.ClosePrinter(handle)
            except Exception as e:
                print(f"[Errore Easter Egg USB]: {e}")
        else:
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3.0)
                s.connect((target, 9100))
                s.sendall(stringa_zpl.encode("ascii"))
                s.close()
            except Exception as e:
                print(f"[Errore Easter Egg Rete]: {e}")
   
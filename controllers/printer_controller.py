import concurrent.futures
import socket
import threading
from tkinter import messagebox
from zebra import Zebra


class PrinterManagerController:

    def __init__(self, vista_stampanti):
        self.vista_stampanti = vista_stampanti

    def cmd_rileva_stampanti(self, mostra_popup_esito=False):
        """Avvia lo scanner automatico unificato USB + IP."""
        self.vista_stampanti.cmb_dispositivo.set(
            "Scansione hardware in corso..."
        )
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
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=50
            ) as executor:
                risultati = executor.map(controlla_singolo_ip, ips_da_testare)
                for ris in risultati:
                    if ris:
                        dispositivi_finali.append(ris)
        except Exception as e:
            print(f"Errore scansione di rete: {e}")

        self.vista_stampanti.after(
            100,
            lambda: self._elabora_risultati_gui(
                dispositivi_finali, mostra_popup
            ),
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
            self.vista_stampanti.cmb_dispositivo.configure(
                values=["Nessuna stampante collegata"]
            )
            self.vista_stampanti.cmb_dispositivo.set(
                "Nessuna stampante collegata"
            )
            messagebox.showerror(
                "Errore Hardware",
                "Nessuna stampante collegata!\n\nVerifica che la Zebra sia accesa e collegata.",
            )

    def cmd_riallinea_stampante(self):
        """Esegue il comando di calibrazione dei sensori."""
        dati = self.vista_stampanti.get_dati_interfaccia()
        tipo = dati.get("tipo", "USB")
        target = dati.get("target", "").strip()

        if not target or "Nessuna" in target:
            messagebox.showwarning(
                "Azione Annullata", "Nessuna stampante selezionata."
            )
            return

        if tipo == "USB":
            try:
                z = Zebra()
                z.setqueue(target)
                z.autosense()
                messagebox.showinfo(
                    "Calibrazione USB",
                    f"Comando AutoSense inviato correttamente a: {target}",
                )
            except Exception as e:
                messagebox.showerror("Errore USB", f"Dettaglio errore: {e}")
        else:
            # Connessione di Rete IP
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3.0)
                s.connect((target.replace(" (Rete IP)", ""), 9100))
                s.sendall(b"~JC")
                s.close()
                messagebox.showinfo(
                    "Calibrazione Rete", f"Comando inviato a IP: {target}"
                )
            except Exception as e:
                messagebox.showerror("Errore Rete", f"Dettaglio errore: {e}")

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
                
                # Spara il comando RAW di stampa configurazione hardware (ZPL)
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
                # Sostituito z.reset() [EPL2] con z.output("~JR") [ZPL] universale
                z.output("~JR")
                messagebox.showinfo(
                    "Reset USB", f"Comando di reset inviato a: {target}"
                )
            except Exception as e:
                messagebox.showerror("Errore USB", f"Dettaglio errore: {e}")
        else:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((target.replace(" (Rete IP)", ""), 9100))
                s.sendall(b"~JR")
                s.close()
                messagebox.showinfo(
                    "Reset Rete", f"Comando di reset inviato a: {target}"
                )
            except Exception as e:
                messagebox.showerror("Errore Rete", f"Dettaglio errore: {e}")

    def cmd_stampa_prova(self):
        """Invia un'etichetta ZPL reale alla stampante tramite output."""
        dati = self.vista_stampanti.get_dati_interfaccia()
        tipo = dati.get("tipo", "USB")
        target = dati.get("target", "").strip()

        if not target or "Nessuna" in target:
            messagebox.showwarning(
                "Azione Annullata", "Nessuna stampante selezionata."
            )
            return

        # Riquadro di prova proporzionato alla fustella selezionata
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
    
    def cmd_applica_formato_fustella(self):
        """Imposta dinamicamente la fustella sia a livello hardware (Zebra) sia a livello software (Windows)."""
        dati = self.vista_stampanti.get_dati_interfaccia()
        tipo = dati.get("tipo", "USB")
        target = dati.get("target", "").strip()

        if not target or "Nessuna" in target:
            messagebox.showwarning(
                "Azione Annullata", "Seleziona prima una stampante valida."
            )
            return

        # ---> INSERISCI QUI LA CHIAMATA ALLA FUNZIONE DI WINDOWS <---
        # Prima di toccare l'hardware, forziamo i parametri nel pannello di controllo
        self.cmd_forza_dimensioni_in_windows()

        # 1. PARAMETRIZZAZIONE DELLE MISURE HARDWARE (Dots per 203 DPI)
        if "GARANZIE" in target.upper():
            width_dots = 320
            height_dots = 240
            gap_dots = 24
            info_testo = "GARANZIE (4x3 cm) Orizzontale"
            
        elif "ZEBRA" in target.upper():
            width_dots = 560
            height_dots = 800
            gap_dots = 24
            info_testo = "ZEBRA (7x10 cm) Orizzontale"
            
        else:
            return

        # 2. SEZIONE AZIONE: AGGIORNAMENTO DIRETTO HARDWARE (RAM ZEBRA)
        if tipo == "USB":
            try:
                z = Zebra()
                z.setqueue(target)
                
                # Invia il setup dei margini hardware alla memoria della Zebra
                z.setup(
                    direct_thermal=True, 
                    label_height=(height_dots, gap_dots), 
                    label_width=width_dots
                )
                
                # Forza la ricalibrazione dei sensori fisici (giro della fustella)
                z.autosense()
                
                messagebox.showinfo(
                    "Fustella & Driver Aggiornati", 
                    f"Configurazione completata con successo!\n\n"
                    f"Profilo: {info_testo}\n"
                    f"I sensori della stampante sono allineati."
                )
                
            except Exception as e:
                messagebox.showerror(
                    "Errore Hardware", f"Impossibile riconfigurare i sensori USB: {e}"
                )

    def cmd_forza_dimensioni_in_windows(self):
        """Modifica le impostazioni di stampa avanzate (DevMode) direttamente in Windows."""
        dati = self.vista_stampanti.get_dati_interfaccia()
        target = dati.get("target", "").strip()

        if not target or "Nessuna" in target:
            return

        # 1. Definiamo le misure in DECIMI DI MILLIMETRO (lo standard che vuole Windows)
        if "GARANZIE" in target.upper():
            larghezza_mm_10 = 400  # 40 mm -> 400 decimi
            altezza_mm_10 = 300    # 30 mm -> 300 decimi
            info = "GARANZIE (4x3 cm)"
        elif "ZEBRA" in target.upper():
            larghezza_mm_10 = 700  # 70 mm -> 700 decimi
            altezza_mm_10 = 1000   # 100 mm -> 1000 decimi
            info = "ZEBRA (7x10 cm)"
        else:
            return

        try:
            import win32print
            import numpy as np # A volte serve per gestire i puntatori, ma win32print nativo basta
            
            # Apriamo la stampante con i permessi di configurazione amministrativa
            PRINTER_ACCESS_ADMINISTER = 0x00000004
            PRINTER_ACCESS_USE = 0x00000008
            differenze = {"DesiredAccess": PRINTER_ACCESS_ADMINISTER | PRINTER_ACCESS_USE}
            
            hPrinter = win32print.OpenPrinter(target, differenze)
            
            try:
                # Recuperiamo le impostazioni attuali (Livello 2 contiene il DEVMODE)
                info_stampante = win32print.GetPrinter(hPrinter, 2)
                devmode = info_stampante['pDevMode']
                
                # Modifichiamo i campi interni del driver Windows
                devmode.PaperWidth = larghezza_mm_10
                devmode.PaperLength = altezza_mm_10
                devmode.Fields |= win32print.DM_PAPERWIDTH | win32print.DM_PAPERLENGTH
                
                # Sovrascriviamo le impostazioni di Windows
                win32print.SetPrinter(hPrinter, 2, info_stampante, 0)
                
                messagebox.showinfo(
                    "Proprietà Windows Aggiornate", 
                    f"Il formato è stato modificato anche nelle impostazioni avanzate di Windows!\n\n"
                    f"Profilo: {info}\nOra Windows vede la fustella corretta."
                )
            finally:
                win32print.ClosePrinter(hPrinter)
                
        except Exception as e:
            messagebox.showerror(
                "Errore Driver Windows", 
                f"Impossibile aggiornare le preferenze di Windows: {e}\n\n"
                "Nota: Per modificare le impostazioni di sistema, avvia l'app come Amministratore."
            )

    def cmd_manutenzione_totale_driver(self):
        """Controlla vecchi driver, salta la rimozione se non esistono e installa da zero."""
        import subprocess
        import os
        import time
        from tkinter import messagebox
        import win32print

        percorso_driver_inf = os.path.abspath("drivers/ZBRN.inf") 
        nome_modello_inf = "ZDesigner GK420d"  
        nomi_target = ["ZEBRA", "GARANZIE"]

        try:
            assert os.path.exists(percorso_driver_inf), f"Impossibile trovare il file driver in:\n{percorso_driver_inf}"

            print("[1/4] Controllo presenza vecchie code di stampa...")
            stampanti_esistenti = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]
            
            porta_rilevata = "USB001" # Default di fallback

            # 1. Recuperiamo la porta se almeno una stampante esiste davvero
            for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL, None, 2):
                if any(target in p['pPrinterName'].upper() for target in nomi_target):
                    porta_rilevata = p['pPortName']
                    break

            # 2. RIMOZIONE TOTALMENTE SILENZIOSA E INDIVIDUALE
            for nome_stampa in stampanti_esistenti:
                if any(target in nome_stampa.upper() for target in nomi_target):
                    print(f" -> Tentativo rimozione di: {nome_stampa}")
                    try:
                        # ABBIAMO AGGIUNTO IL FLAG /q (Quiet/Silenzioso)
                        # Questo impedisce a Windows di mostrare finestre di errore grafiche!
                        cmd_delete = f'rundll32 printui.dll,PrintUIEntry /dl /n "{nome_stampa}" /q'
                        subprocess.run(cmd_delete, shell=True, capture_output=True, text=True)
                    except Exception as e_rimozione:
                        # Se Windows fa i capricci, Python lo ignora e passa alla stampante successiva
                        print(f" -> [IGNORATO] Impossibile rimuovere {nome_stampa}: {e_rimozione}")
            
            # Pausa per dare tempo allo spooler di Windows di digerire la richiesta
            time.sleep(2)

            print(f"[2/4] Iniezione del driver ZBRN.inf nel sistema sulla porta {porta_rilevata}...")
            # ... da qui in poi il codice continua identico a prima ...
            print("[3/4] Registrazione modello hardware...")
            cmd_register = f'rundll32 printui.dll,PrintUIEntry /ia /m "{nome_modello_inf}" /f "{percorso_driver_inf}"'
            res_register = subprocess.run(cmd_register, shell=True, capture_output=True, text=True)

            assert res_register.returncode == 0, (
                f"Errore registrazione hardware.\nVerifica il nome modello '{nome_modello_inf}'\n"
                f"Dettaglio: {res_register.stderr if res_register.stderr else res_store.stderr}"
            )

            print("[4/4] Creazione nuove code personalizzate...")
            cmd_add_zebra = f'rundll32 printui.dll,PrintUIEntry /if /b "ZEBRA" /m "{nome_modello_inf}" /r "{porta_rilevata}" /f "{percorso_driver_inf}"'
            subprocess.run(cmd_add_zebra, shell=True, capture_output=True)

            cmd_add_garanzie = f'rundll32 printui.dll,PrintUIEntry /if /b "GARANZIE" /m "{nome_modello_inf}" /r "{porta_rilevata}" /f "{percorso_driver_inf}"'
            subprocess.run(cmd_add_garanzie, shell=True, capture_output=True)

            # Configurazione layout geometrico nativo (senza PowerShell!)
            time.sleep(2)
            self._applica_devmode_silenzioso("ZEBRA", 700, 1000)
            self._applica_devmode_silenzioso("GARANZIE", 400, 300)

            if hasattr(self, 'cmd_rileva_stampanti'):
                self.cmd_rileva_stampanti(mostra_popup_esito=False)

            messagebox.showinfo("Successo", "Installazione pulita completata con successo!")

        except AssertionError as errore_controllo:
            messagebox.showerror("Blocco di Sicurezza", str(errore_controllo))
        except Exception as e:
            messagebox.showerror("Errore", f"Errore imprevisto: {e}")

    def _applica_devmode_silenzioso(self, nome_stampante, larghezza_mm_10, altezza_mm_10):
        """Metodo di supporto per iniettare i millimetri senza mostrare popup all'utente."""
        try:
            import win32print
            PRINTER_ACCESS_ADMINISTER = 0x00000004
            PRINTER_ACCESS_USE = 0x00000008
            hPrinter = win32print.OpenPrinter(nome_stampante, {"DesiredAccess": PRINTER_ACCESS_ADMINISTER | PRINTER_ACCESS_USE})
            try:
                info = win32print.GetPrinter(hPrinter, 2)
                devmode = info['pDevMode']
                devmode.PaperWidth = larghezza_mm_10
                devmode.PaperLength = altezza_mm_10
                devmode.Fields |= win32print.DM_PAPERWIDTH | win32print.DM_PAPERLENGTH
                win32print.SetPrinter(hPrinter, 2, info, 0)
                print(f"[DIAGNOSTICA] Configurato DevMode per {nome_stampante} a {larghezza_mm_10}x{altezza_mm_10}")
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            print(f"[DIAGNOSTICA] Impossibile pre-configurare {nome_stampante}: {e}")
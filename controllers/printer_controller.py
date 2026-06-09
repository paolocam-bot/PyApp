import concurrent.futures
import socket
import threading
import win32print
import win32api
import win32con
import subprocess
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
        try:
            print("[1/5] Pulizia vecchie stampanti Zebra...")
            # 1. Cancelliamo le vecchie code per evitare conflitti di nome
            stampanti_esistenti = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]
            for nome_stampa in stampanti_esistenti:
                if "ZEBRA" in nome_stampa.upper():
                    print(f"Rimozoione vecchia coda: {nome_stampa}")
                    subprocess.run(f'rundll32 printui.dll,PrintUIEntry /dl /n "{nome_stampa}" /q', shell=True)
            
            time.sleep(2)

            # 2. Installazione del driver nel sistema tramite PNPUTIL
            percorso_driver_inf = os.path.abspath("drivers/ZBRN.inf")
            print("[2/5] Iniezione driver ZBRN.inf nel sistema...")
            subprocess.run(f'pnputil /add-driver "{percorso_driver_inf}" /install', shell=True, capture_output=True)

            # Il nome esatto del modello scritto dentro il file .inf (es. "Zebra ZD220")
            NOME_MODELLO_DRIVER = "Zebra ZD220" 

            # 3. Creazione delle due code distinte su porte diverse (USB001 e USB002)
            print("[3/5] Creazione delle nuove code di stampa differenziate...")
            
            # Coda 1: ETICHETTE sulla porta USB001
            cmd_crea_etichette = f'rundll32 printui.dll,PrintUIEntry /if /b "Zebra Etichette" /f "{percorso_driver_inf}" /r "USB001" /m "{NOME_MODELLO_DRIVER}"'
            subprocess.run(cmd_crea_etichette, shell=True)

            # Coda 2: GARANZIE sulla porta USB002
            cmd_crea_garanzie = f'rundll32 printui.dll,PrintUIEntry /if /b "Zebra Garanzie" /f "{percorso_driver_inf}" /r "USB002" /m "{NOME_MODELLO_DRIVER}"'
            subprocess.run(cmd_crea_garanzie, shell=True)

            time.sleep(2)

            # 4. CONFIGURAZIONE FORMATO FOGLIO (Solo per "Zebra Etichette")
            print("[4/5] Configurazione formato pagina 7x10 Landscape per Zebra Etichette...")
            setta_formato_zebra_etichette("Zebra Etichette")
            
            print("[5/5] Manutenzione completata con successo!")

        except Exception as e:
            print(f"Errore durante la manutenzione: {e}")

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

    
    def setta_formato_zebra_etichette(self):
        try:
            # 1. Recupera l'elenco di TUTTE le stampanti installate su questo PC
            lista_stampanti = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]
            # Crea una lista in maiuscolo per fare i controlli di sicurezza
            lista_maiuscola = [nome.strip().upper() for nome in lista_stampanti]
            
            print(f"[Scanner] Stampanti rilevate sul PC: {lista_stampanti}")

            # =====================================================================
            # CONTROLLO E CONFIGURAZIONE PER "ZEBRA" (Etichette 7x10)
            # =====================================================================
            if "ZEBRA" in lista_maiuscola:
                idx = lista_maiuscola.index("ZEBRA")
                nome_reale = lista_stampanti[idx]
                print(f"[Configurazione] Trovata '{nome_reale}'. Applico formato 7x10cm Landscape...")
                
                try:
                    p_handle = win32print.OpenPrinter(nome_reale, {"DesiredAccess": win32print.PRINTER_ALL_ACCESS})
                    info = win32print.GetPrinter(p_handle, 2)
                    devmode = info['pDevMode']
                    
                    devmode.Fields |= (win32con.DM_ORIENTATION | win32con.DM_PAPERSIZE | win32con.DM_PAPERWIDTH | win32con.DM_PAPERLENGTH)
                    devmode.Orientation = win32con.DMORIENT_LANDSCAPE
                    devmode.PaperSize = 0  
                    devmode.PaperWidth = 700   # 7 cm
                    devmode.PaperLength = 1000 # 10 cm
                    
                    win32print.SetPrinter(p_handle, 2, info, 0)
                    win32print.ClosePrinter(p_handle)
                    print(f" -> OK: Configurazione '{nome_reale}' completata.")
                except Exception as e:
                    print(f"[AVVISO] Impossibile configurare {nome_reale} (forse è offline): {e}")
            else:
                print("[Scanner] Stampante 'ZEBRA' non collegata al momento. Salto.")

            # =====================================================================
            # CONTROLLO E CONFIGURAZIONE PER "GARANZIE" (Garanzie 4x3)
            # =====================================================================
            if "GARANZIE" in lista_maiuscola:
                idx = lista_maiuscola.index("GARANZIE")
                nome_reale = lista_stampanti[idx]
                print(f"[Configurazione] Trovata '{nome_reale}'. Applico formato 4x3cm Landscape...")
                
                try:
                    p_handle = win32print.OpenPrinter(nome_reale, {"DesiredAccess": win32print.PRINTER_ALL_ACCESS})
                    info = win32print.GetPrinter(p_handle, 2)
                    devmode = info['pDevMode']
                    
                    devmode.Fields |= (win32con.DM_ORIENTATION | win32con.DM_PAPERSIZE | win32con.DM_PAPERWIDTH | win32con.DM_PAPERLENGTH)
                    devmode.Orientation = win32con.DMORIENT_LANDSCAPE
                    devmode.PaperSize = 0  
                    devmode.PaperWidth = 400  # 4 cm
                    devmode.PaperLength = 300 # 3 cm
                    
                    # QUI HO AGGIUNTO IL SALVATAGGIO CHE MANCAVA NEL TUO CODICE
                    win32print.SetPrinter(p_handle, 2, info, 0)
                    win32print.ClosePrinter(p_handle)
                    print(f" -> OK: Configurazione '{nome_reale}' completata.")
                except Exception as e:
                    print(f"[AVVISO] Impossibile configurare {nome_reale} (forse è offline): {e}")
            else:
                print("[Scanner] Stampante 'GARANZIE' non collegata al momento. Salto.")

        except Exception as e:
            print(f"Errore generale nella routine di scansione: {e}")

            import subprocess


    def cmd_scambia_porte_zebra(self):
        try:
            print("[Port Manager] Controllo la posizione attuale delle porte USB...")
            
            # Usiamo il livello 2 per ottenere un dizionario completo e sicuro per ogni stampante
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

            print(f"[Port Manager] Stato attuale -> ZEBRA: {porta_attuale_zebra} | GARANZIE: {porta_attuale_garanzie}")

            # BLOCCO RIGIDO DI SICUREZZA: se non trova ENTRAMBE le stampanti, esce in modo pulito
            if not porta_attuale_zebra or not porta_attuale_garanzie:
                print("[AVVISO RIGIDO] Impossibile scambiare le porte: una delle due stampanti manca su Windows.")
                return

            # LOGICA DI INVERSIONE
            if "USB001" in porta_attuale_zebra:
                nuova_porta_zebra = "USB002"
                nuova_porta_garanzie = "USB001"
            else:
                nuova_porta_zebra = "USB001"
                nuova_porta_garanzie = "USB002"

            print(f"[Port Manager] Applico lo scambio -> ZEBRA su {nuova_porta_zebra} | GARANZIE su {nuova_porta_garanzie}...")

            res1 = subprocess.run(f'rundll32 printui.dll,PrintUIEntry /Xs /n "ZEBRA" PortName "{nuova_porta_zebra}"', shell=True, capture_output=True)
            res2 = subprocess.run(f'rundll32 printui.dll,PrintUIEntry /Xs /n "GARANZIE" PortName "{nuova_porta_garanzie}"', shell=True, capture_output=True)

            if res1.returncode == 0 and res2.returncode == 0:
                print("Porte invertite con successo!")
            else:
                print("[ERRORE] Windows ha rifiutato lo scambio delle porte.")

        except Exception as e:
            print(f"Errore durante lo scambio delle porte USB: {e}")
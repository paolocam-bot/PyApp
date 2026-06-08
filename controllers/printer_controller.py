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
        """Interroga direttamente i sensori hardware della stampante via USB o IP."""
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
                import win32print
                
                # 1. Apriamo la stampante con permessi di lettura/scrittura diretti (RAW)
                p_handle = win32print.OpenPrinter(target, {"DesiredAccess": win32print.PRINTER_ACCESS_ADMINISTER | win32print.PRINTER_ACCESS_USE})
                
                # Configura il tipo di documento come RAW per inviare comandi bypassando il driver
                job_data = ("Diagnostica Hardware", None, "RAW")
                hJob = win32print.StartDocPrinter(p_handle, 1, job_data)
                win32print.StartPagePrinter(p_handle)
                
                # Invia il comando Host Status (~HS) direttamente alla scheda madre della Zebra
                comando = b"~HS"
                win32print.WritePrinter(p_handle, comando)
                
                win32print.EndPagePrinter(p_handle)
                win32print.EndDocPrinter(p_handle)
                
                # 2. LETTURA DEI SENSORI (Legge la risposta hardware dal buffer della stampante)
                # Attendiamo un millisecondo per permettere alla Zebra di elaborare e rispondere
                import time
                time.sleep(0.1)
                
                # Leggiamo i dati di ritorno dal chip USB della stampante
                err, risposta_byte = win32print.ReadPrinter(p_handle, 1024)
                win32print.ClosePrinter(p_handle)
                
                if risposta_byte:
                    risposta_testo = risposta_byte.decode("utf-8", errors="ignore").strip()
                    
                    # Decodifica base dei sensori Zebra (La stringa ~HS restituisce 3 righe separate da codici speciali)
                    # Esempio tipico di risposta: 030,0,0,1234,000,0,-...
                    info_sensori = "Risposta Sensori Zebra (USB):\n\n"
                    
                    if "1" in risposta_testo: # Analisi preliminare dei flag comuni
                        if "Paper Out" in risposta_testo or ",1," in risposta_testo:
                            info_sensori += "⚠️ ATTENZIONE: Carta/Etichette esaurite!\n"
                        if "Ribbon Out" in risposta_testo:
                            info_sensori += "⚠️ ATTENZIONE: Nastro (Ribbon) esaurito o inserito male!\n"
                        if "Head Open" in risposta_testo:
                            info_sensori += "⚠️ ATTENZIONE: Sportello/Testina aperta!\n"
                    else:
                        info_sensori += "✅ Hardware OK: Sensori in stato regolare.\n"
                        
                    messagebox.showinfo(
                        "Diagnostica Hardware Reale", 
                        f"{info_sensori}\n[Stringa Raw ricevuta dalla Zebra]:\n{risposta_testo}"
                    )
                else:
                    # Se il chip USB non risponde, molto spesso è perché la stampante è bloccata in un errore critico
                    messagebox.showwarning(
                        "Nessun Segnale", 
                        f"La stampante '{target}' è connessa ma i sensori hardware non rispondono.\n\n"
                        "Consiglio: Se la spia della Zebra è ROSSA, spegni e riaccendi la stampante "
                        "per svuotare la memoria hardware bloccata."
                    )
                    
            except Exception as e:
                messagebox.showerror(
                    "Errore Canale RAW", 
                    f"Impossibile aprire la comunicazione diretta USB.\nDettaglio: {e}\n\n"
                    "Nota: Assicurati di eseguire l'app come Amministratore se Windows blocca l'accesso RAW."
                )
        
        else:
            # Connessione di Rete IP (Qui la comunicazione bidirezionale è nativa e funziona sempre direttamente)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2.0)
                s.connect((target.replace(" (Rete IP)", ""), 9100))
                s.sendall(b"~HS")
                risposta = s.recv(1024).decode("utf-8")
                s.close()
                
                messagebox.showinfo(
                    "Stato Rete Hardware", f"Risposta diagnostica sensori da {target}:\n{risposta}"
                )
            except Exception as e:
                messagebox.showerror("Errore LAN", f"Dettaglio errore: {e}")

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
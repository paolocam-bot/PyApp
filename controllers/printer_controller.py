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
import usb.core
import usb.util
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
        """
        Interroga la stampante bypassando lo spooler di Windows.
        Usa i Socket per la rete IP e PySerial per la connessione USB RAW bidirezionale,
        garantendo la lettura istantanea dello sportello aperto o della carta finita.
        """
        import socket
        import time
        try:
            import serial
            import serial.tools.list_ports
        except ImportError:
            messagebox.showerror("Errore", "Libreria 'pyserial' mancante. Installala usando: pip install pyserial")
            return

        dati = self.vista_stampanti.get_dati_interfaccia()
        tipo = dati.get("tipo", "USB")
        target = dati.get("target", "").strip()

        if not target or "Nessuna" in target or "Ricerca in corso" in target:
            messagebox.showwarning("Attenzione", "Seleziona una stampante valida prima di controllare lo stato.")
            return

        comando_status = b"~HS"
        risposta = ""
        esito_finale = ""

        # ======================================================================
        # 1. ACQUISIZIONE DATI DIRETTAMENTE DALL'HARDWARE
        # ======================================================================

        # --- CASO RETE IP (Nativamente bidirezionale) ---
        if tipo == "IP":
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2.0)
                s.connect((target, 9100))
                s.sendall(comando_status)
                risposta_byte = s.recv(1024)
                s.close()
                risposta = risposta_byte.decode("ascii", errors="ignore")
            except Exception as e:
                esito_finale = f"DISCONNESSA: Impossibile raggiungere la stampante sulla rete IP.\n\nDettaglio: {e}"

        # --- CASO USB HARDWARE PURO (Bypassa lo spooler di Windows tramite COM) ---
        else:
            porta_com_rilevata = None
            
            # Cerchiamo se la stampante Zebra ha esposto una porta COM virtuale attiva
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                # Cerca identificativi Zebra nel nome o nella descrizione hardware
                if "zebra" in p.description.lower() or "zdesigner" in p.description.lower() or "usb serial" in p.description.lower():
                    porta_com_rilevata = p.device
                    break
            
            # Fallback: Se non trova la parola chiave, prova a usare la prima COM disponibile o una di default (es. COM3)
            if not porta_com_rilevata:
                # Se conosci la porta fissa (es: "COM3") puoi impostarla qui direttamente, 
                # altrimenti prende la prima disponibile nel sistema per tentare il test
                if ports:
                    porta_com_rilevata = ports[0].device
                else:
                    porta_com_rilevata = "COM3" 

            try:
                # Apriamo un canale di comunicazione seriale puro (asincrono e bidirezionale)
                ser = serial.Serial(porta_com_rilevata, baudrate=9600, timeout=1.0)
                
                # Inviamo il comando direttamente ai registri della stampante
                ser.write(comando_status)
                time.sleep(0.2)
                
                # Leggiamo il buffer di ritorno generato dai sensori fisici
                risposta_bytes = ser.read(1024)
                risposta = risposta_bytes.decode("ascii", errors="ignore")
                ser.close()
            except Exception as e:
                esito_finale = (f"STACCATA / ERRORE PORTA: Impossibile comunicare direttamente con la stampante.\n"
                                f"Verifica che il cavo sia inserito e che nessuna stampa sia rimasta bloccata in coda.\n\n"
                                f"Dettaglio porta [{porta_com_rilevata}]: {e}")

        # ======================================================================
        # 2. PARSING DELLO STATO REALE (STRINGA ~HS FORMATO SDK ZEBRA)
        # ======================================================================
        if not esito_finale:
            if risposta and "," in risposta:
                # La stampante risponde con stringhe separate da ritorni a capo
                righe = risposta.split("\n")
                if len(righe) >= 2:
                    parti_riga1 = righe[0].split(",")
                    parti_riga2 = righe[1].split(",")
                    
                    try:
                        # Pulizia dei caratteri di controllo non numerici
                        flag_testina_aperta = ''.join(c for c in parti_riga1[1] if c.isdigit()).strip()
                        flag_carta_finita   = ''.join(c for c in parti_riga1[2] if c.isdigit()).strip()
                        flag_in_pausa       = ''.join(c for c in parti_riga2[4] if c.isdigit()).strip()
                        
                        # Controllo dei flag hardware reali
                        if flag_testina_aperta == "1":
                            esito_finale = "ERRORE CRITICO: Testina di stampa aperta!\n\nChiudi saldamente lo sportello superiore della Zebra."
                        elif flag_carta_finita == "1":
                            esito_finale = "ERRORE CARTA: Rotolo esaurito!\n\nInserisci un nuovo rotolo e premi il tasto FEED."
                        elif flag_in_pausa == "1":
                            esito_finale = "ATTENZIONE: Stampante in PAUSA.\n\nVerifica il nastro o la calibrazione del sensore fustella."
                        else:
                            esito_finale = "PRONTA: La stampante risponde correttamente, lo sportello è chiuso ed è pronta a stampare."
                    except Exception:
                        esito_finale = "Risposta parziale ricevuta dall'hardware. Chiudi lo sportello e riprova."
                else:
                    esito_finale = "Dati incompleti ricevuti dai sensori hardware."
            else:
                esito_finale = ("Nessuna risposta dall'hardware.\n\n"
                                "Lo spooler di Windows potrebbe aver bloccato la porta. "
                                "Svuota la coda di stampa di Windows e riprova.")

        # ======================================================================
        # 3. MOSTRA POPUP INFORMATIVO
        # ======================================================================
        messagebox.showinfo("Stato Hardware Stampante", esito_finale)
    
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
    # ^LL240 -> Forza l'altezza dell'etichetta a esattamente 3 cm (240 punti)
    # ^PW320 -> Forza la larghezza di stampa a esattamente 4 cm (320 punti)
    # ^GB300,220,4 -> Il rettangolo ora copre quasi tutta l'etichetta (lascia 10 punti di margine per lato)
            stringa_zpl = (
                "^XA^LL240^PW320"
                "^FO10,10^GB300,220,4^FS"
                "^FO10,50^A0N,30,30^FB300,3,,C"
                "^FDBuon lavoro\&da paolo\&:P^FS^XZ"
    )
        else:
            # FUSTELLA GRANDE: Margine 40, Larghezza rettangolo 480 -> Fine rettangolo a 520.
            # TESTO: Parte a 40 (preciso con la fustella) e lo facciamo largo 480 (^FB480).
            stringa_zpl = "^XA^FO40,40^GB480,720,4^FS^FO40,280^A0N,55,55^FB480,3,,C^FDBuon lavoro\&da paolo\&:P^FS^XZ"

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
            # Recuperiamo la lista delle stampanti locali installate
            lista_stampanti = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]
            
            # Variabili di supporto per estrarre il nome reale corretto
            nome_reale_zebra = None
            nome_reale_garanzie = None

            # Cerchiamo le stampanti controllando se il nome CONTIENE la parola chiave
            for nome in lista_stampanti:
                nome_upper = nome.upper()
                if "ZEBRA" in nome_upper:
                    nome_reale_zebra = nome
                elif "GARANZIE" in nome_upper:
                    nome_reale_garanzie = nome

            # --- CONFIGURAZIONE STAMPANTE ZEBRA ---
            if nome_reale_zebra:
                try:
                    # 1. Impostiamo la Zebra come stampante PREDEFINITA di Windows
                    win32print.SetDefaultPrinter(nome_reale_zebra)
                    print(f"Stampante predefinita impostata su: {nome_reale_zebra}")

                    # 2. Configurazione del formato e orientamento etichetta
                    p_handle = win32print.OpenPrinter(nome_reale_zebra, {"DesiredAccess": win32print.PRINTER_ALL_ACCESS})
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
                    print(f"Errore configurazione o default ZEBRA: {e}")
            else:
                print("Stampante ZEBRA non trovata nel sistema.")

            # --- CONFIGURAZIONE STAMPANTE GARANZIE ---
            if nome_reale_garanzie:
                try:
                    p_handle = win32print.OpenPrinter(nome_reale_garanzie, {"DesiredAccess": win32print.PRINTER_ALL_ACCESS})
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
            else:
                print("Stampante GARANZIE non trovata nel sistema.")

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
        




    def _recupera_porte_usb_disponibili(self):
        """Scansiona il sistema Windows alla ricerca delle porte USB di stampa disponibili."""
        import win32print
        porte_rilevate = []

        # Enumera tutte le porte del sistema con livello di dettaglio 1
        for porta_info in win32print.EnumPorts(None, 1):
            # Correggiamo 'pName' in 'Name' per evitare il KeyError
            p_name = porta_info.get('Name', '')
            if p_name.upper().startswith("USB"):
                porte_rilevate.append(p_name)

        # Ordina le porte (USB001, USB002, etc.)
        porte_rilevate.sort()

        # Se non trova porte USB attive (es. nessuna stampante USB è mai stata installata prima),
        # prepariamo un fallback standard sicuro
        if not porte_rilevate:
            porte_rilevate = ["USB001", "USB002", "USB003"]

        return porte_rilevate



    """
    def noncliccare(self):
        
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
    """

    def cmd_manutenzione_totale_driver_indipendente():
        print("=== INIZIO MANUTENZIONE E INSTALLAZIONE DRIVER ===")

        # 1 e 2. DEFINIZIONE DEL PERCORSO STATICO ASSOLUTO LOCALE
        cartella_lavoro_normalizzata = r"C:\Servizio\ZBRN\Win64"
        nome_file_inf = "ZBRN.inf"
        percorso_inf_normalizzato = os.path.normpath(
            os.path.join(cartella_lavoro_normalizzata, nome_file_inf)
        )

        print("DEBUG - Tipo esecuzione: FUNZIONE INDIPENDENTE / PERCORSO STATICO")
        print(f"DEBUG - Percorso INF finale: {percorso_inf_normalizzato}")

        # Controllo di sicurezza preventivo sulla cartella locale fissa
        if not os.path.exists(percorso_inf_normalizzato):
            print(
                f" [STOP] Errore 000003: Impossibile trovare il file INF nel percorso statico: {percorso_inf_normalizzato}"
            )
            print(
                " -> Verifica che la cartella C:\\Servizio\\ZBRN\\Win64 esista e contenga i file sul PC."
            )
            return

        # 3. RILEVAMENTO PORTE USB (Integrato direttamente senza chiamare funzioni esterne)
        porte_usb = []
        try:
            # Interroga Windows tramite PowerShell per trovare le porte USB virtuali di stampa attive
            risultato = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Get-PrinterPort | Where-Object {$_.Name -like 'USB*'} | Select-Object -ExpandProperty Name",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            # Pulisce l'output separando le righe vuote
            porte_usb = [
                line.strip() for line in risultato.stdout.splitlines() if line.strip()
            ]
        except Exception as e:
            print(f" [WARNING] Impossibile rilevare porte tramite PowerShell: {e}")

        # Se non trova porte o fallisce, assegna delle porte di fallback standard
        if not porte_usb:
            porte_usb = ["USB001"]

        porta_garanzie = porte_usb[0]
        if len(porte_usb) > 1:
            porta_zebra = porte_usb[1]
        else:
            # Calcola la porta successiva (es. se trova USB001, imposta USB002)
            numero_porta = "".join(filter(str.isdigit, porta_garanzie))
            prossimo_num = int(numero_porta) + 1 if numero_porta else 2
            porta_zebra = f"USB{prossimo_num:03d}"

        print(f"DEBUG - Porte rilevate/assegnate: GARANZIE -> {porta_garanzie}, ZEBRA -> {porta_zebra}")

        # 4. PULIZIA VECCHIE INSTALLAZIONI (Esecuzione diretta con subprocess)
        print("\nRimozione vecchie istanze...")
        try:
            subprocess.run(
                ["rundll32", "printui.dll,PrintUIEntry", "/dl", "/n", "GARANZIE", "/q"],
                check=False,
            )
            print("[OK] Rimozione 'GARANZIE' inviata.")
        except Exception as e:
            print(f"[ERRORE] Impossibile pulire GARANZIE: {e}")

        try:
            subprocess.run(
                ["rundll32", "printui.dll,PrintUIEntry", "/dl", "/n", "ZEBRA", "/q"],
                check=False,
            )
            print("[OK] Rimozione 'ZEBRA' inviata.")
        except Exception as e:
            print(f"[ERRORE] Impossibile pulire ZEBRA: {e}")

        # 5. ESECUZIONE INSTALLAZIONE CON PERCORSI CORRETTI (Senza doppie virgolette nocive)
        modello_driver = "ZDesigner GK420d"
        percorso_protetto = percorso_inf_normalizzato  # CORRETTO: rimosse le virgolette f'"{}"', ci pensa subprocess se ci sono spazi

        print(f"\nInstallazione 'GARANZIE' su {porta_garanzie}...")
        cmd_garanzie = [
            "rundll32",
            "printui.dll,PrintUIEntry",
            "/if",
            "/b",
            "GARANZIE",
            "/f",
            percorso_protetto,
            "/r",
            porta_garanzie,
            "/m",
            modello_driver,
        ]
        try:
            # Esegue il comando impostando la cartella di lavoro (cwd) corretta per i file interni del driver
            subprocess.run(cmd_garanzie, cwd=cartella_lavoro_normalizzata, check=True)
            print("[OK] Coda 'GARANZIE' installata con successo.")
        except subprocess.CalledProcessError as e:
            print(f" [FALLITO] Errore installazione 'GARANZIE'. Codice d'uscita: {e.returncode}")

        print(f"\nInstallazione 'ZEBRA' su {porta_zebra}...")
        cmd_zebra = [
            "rundll32",
            "printui.dll,PrintUIEntry",
            "/if",
            "/b",
            "ZEBRA",
            "/f",
            percorso_protetto,
            "/r",
            porta_zebra,
            "/m",
            modello_driver,
        ]
        try:
            subprocess.run(cmd_zebra, cwd=cartella_lavoro_normalizzata, check=True)
            print("[OK] Coda 'ZEBRA' installata con successo.")
        except subprocess.CalledProcessError as e:
            print(f" [FALLITO] Errore installazione 'ZEBRA'. Codice d'uscita: {e.returncode}")

        print("\n=== CONFIGURAZIONE COMPLETATA CON SUCCESSO ===")
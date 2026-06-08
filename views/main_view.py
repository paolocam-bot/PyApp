import customtkinter as ctk
import os
import sys
from PIL import Image, ImageTk

# Importiamo le viste separate che risiedono nella stessa cartella
from views.manuale_view import ManualeView
from views.ticket_view import TicketView
from views.driver_view import DriverView
from views.admin_view import AdminView
from views.printer_manager_view import FrameGestioneStampante
from controllers.printer_controller import PrinterManagerController


class HelpDeskView(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Impostazioni della finestra principale
        self.title("HardwareHero - Help Desk per Assistenza Tecnica")
        self.geometry("850x650")
        
        # --- GESTIONE ICONA COMPATIBILE MAC / WINDOWS ---
        try:
            if sys.platform.startswith("win"):
                if os.path.exists("app_icon.ico"):
                    self.wm_iconbitmap("app_icon.ico")
            else:
                percorso_png = os.path.join("assets", "app_icon.png")  
                if os.path.exists(percorso_png):
                    img_aperta = Image.open(percorso_png)
                    img_ridimensionata = img_aperta.resize((512, 512))
                    self.icona_sviluppo = ImageTk.PhotoImage(img_ridimensionata)
                    self.iconphoto(False, self.icona_sviluppo)
        except Exception as e:
            print(f"Nota: Impossibile caricare l'icona in sviluppo: {e}")
            
        ctk.set_appearance_mode("System")
        
        # --- 1. PRIMA IL PACK DELLE STRUTTURE ANCORATE (Fondo dello schermo) ---
        self.lbl_firma = ctk.CTkLabel(
            self, 
            text="Developed by PaoloCamedda - V.0.1 prealfa", 
            font=ctk.CTkFont(size=11, weight="normal"),
            text_color="gray"
        )
        self.lbl_firma.pack(side="bottom", pady=5, padx=10, fill="x")
        
        # --- 2. DOPO IL PACK DEL COMPONENTE CENTRALE ESPANDIBILE ---
        # Aggiunto il 'command' per intercettare il cambio scheda delle commesse
        self.tabview = ctk.CTkTabview(self, width=830, height=600, command=self.rilevato_cambio_tab)
        self.tabview.pack(pady=10, padx=10, fill="both", expand=True)
        
        # 3. Aggiungiamo le schede nell'ordine desiderato
        self.tab_manuale = self.tabview.add("Manuale di Risoluzione")
        #self.tab_ticket = self.tabview.add("Apri un Ticket")
        self.tab_driver = self.tabview.add("Risoluzione Problemi")
        self.tab_stampanti = self.tabview.add("Gestione Stampante")
        self.tab_admin = self.tabview.add("Admin")
        
        # 4. Inizializziamo le sotto-viste dentro i rispettivi tab
        self.vista_manuale = ManualeView(self.tab_manuale)
        self.vista_manuale.pack(fill="both", expand=True)
        
        #self.vista_ticket = TicketView(self.tab_ticket)
        #self.vista_ticket.pack(fill="both", expand=True)
        
        self.vista_driver = DriverView(self.tab_driver)
        self.vista_driver.pack(fill="both", expand=True)

        # Inizializziamo il modulo di gestione stampante
        self.vista_stampanti = FrameGestioneStampante(self.tab_stampanti, None)
        self.vista_stampanti.pack(fill="both", expand=True)

        self.vista_admin = AdminView(self.tab_admin)
        self.vista_admin.pack(fill="both", expand=True)

        # 5. FORZATURA: Seleziona la scheda del manuale come attiva all'avvio
        self.tabview.set("Manuale di Risoluzione")

    def rilevato_cambio_tab(self):
        """Esegue automaticamente i controlli hardware in background all'accesso della tab."""
        scelta = self.tabview.get()
        # Se la commessa entra nella gestione stampante, avviamo la scansione USB+IP senza mostrare popup invasivi se tutto va bene
        if scelta == "Gestione Stampante" and hasattr(self, 'printer_controller'):
            self.printer_controller.cmd_rileva_stampanti(mostra_popup_esito=False)

    def imposta_controller(self, controller):
        """Collega le funzioni dei controller ai pulsanti delle sotto-viste."""
        
        # 1. Collegamenti del Main Controller (Pagine standard)
        self.vista_driver.btn_zebra.configure(command=controller.ripristina_driver_zebra)
        self.vista_driver.btn_input.configure(command=controller.ripristina_input_hardware)
        self.vista_manuale.inizializza_manuale(controller)
        
        self.vista_admin.controller = controller
        self.vista_admin.btn_aggiungi.configure(command=controller.aggiungi_guida_db)
        self.vista_admin.btn_modifica.configure(command=controller.modifica_guida_db)
        self.vista_admin.btn_elimina.configure(command=controller.elimina_guida_db)
        
        # ----------------------------------------------------------------------
        # 2. CREAZIONE E COLLEGAMENTO DEL CONTROLLER SEPARATO PER LA STAMPANTE
        # ----------------------------------------------------------------------
        # Creiamo il controller dedicato passando il frame della stampante
        self.printer_controller = PrinterManagerController(self.vista_stampanti)
        
        # Diciamo al frame chi è il suo controller specifico
        self.vista_stampanti.controller = self.printer_controller
        
        # Mappatura del pulsante di Scansione Manuale (Forzato con popup di esito positivo/negativo)
        self.vista_stampanti.btn_scan.configure(
            command=lambda: self.printer_controller.cmd_rileva_stampanti(mostra_popup_esito=True)
        )
        
        # Mappatura dei pulsanti operativi standard della stampante unificata
        self.vista_stampanti.btn_status.configure(command=self.printer_controller.cmd_click_status)
        self.vista_stampanti.btn_allinea.configure(command=self.printer_controller.cmd_riallinea_stampante)
        self.vista_stampanti.btn_reboot.configure(command=self.printer_controller.cmd_riavvia_stampante)
        self.vista_stampanti.btn_test.configure(command=self.printer_controller.cmd_stampa_prova)
        
        # Mappatura del bottone Driver riposizionato (Spostato dentro il modulo stampante)
        self.vista_stampanti.btn_installa_driver.configure(command=controller.ripristina_driver_zebra)
        
        # Esegue un controllo immediato iniziale se l'app per qualche motivo dovesse partire già su questa scheda
        if self.tabview.get() == "Gestione Stampante":
            self.printer_controller.cmd_rileva_stampanti(mostra_popup_esito=False)
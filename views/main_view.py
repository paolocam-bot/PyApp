import customtkinter as ctk
import os
import sys
from PIL import Image, ImageTk

# Manteniamo tutti gli import intatti per non rompere la logica del progetto
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
        
        # --- GESTIONE ICONA COMPATIBILE SVILUPPO E COMPILAZIONE (NUITKA) ---
        try:
            if getattr(sys, 'frozen', False):
                cartella_base = os.path.dirname(sys.executable)
            else:
                cartella_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            if sys.platform.startswith("win"):
                percorso_ico = os.path.join(cartella_base, "assets", "app_icon.ico")
                if os.path.exists(percorso_ico):
                    self.wm_iconbitmap(percorso_ico)
                else:
                    print(f"[NOTA] Icona .ico non trovata nel percorso: {percorso_ico}")
            else:
                percorso_png = os.path.join(cartella_base, "assets", "app_icon.png")  
                if os.path.exists(percorso_png):
                    img_aperta = Image.open(percorso_png)
                    img_ridimensionata = img_aperta.resize((512, 512))
                    self.icona_sviluppo = ImageTk.PhotoImage(img_ridimensionata)
                    self.iconphoto(False, self.icona_sviluppo)
        except Exception as e:
            print(f"Nota: Impossibile caricare l'icona: {e}")
            
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
        self.tabview = ctk.CTkTabview(self, width=830, height=600, command=self.rilevato_cambio_tab)
        self.tabview.pack(pady=10, padx=10, fill="both", expand=True)
        
        # 3. CREAZIONE DELLE SCHEDE VISIBILI ALL'UTENTE FINALE
        # Abbiamo rimosso .add("Manuale di Risoluzione") e .add("Admin")
        self.tab_driver = self.tabview.add("Risoluzione Problemi")
        self.tab_stampanti = self.tabview.add("Gestione Stampante")
        
        # 4. INIZIALIZZAZIONE DELLE SOTTO-VISTE
        # Inizializziamo Manuale e Admin passandogli 'self' invece del tab rimosso.
        # In questo modo gli oggetti esistono in memoria ma l'utente non ha modo di vederli o cliccarli.
        self.vista_manuale = ManualeView(self) 
        self.vista_driver = DriverView(self.tab_driver)
        self.vista_driver.pack(fill="both", expand=True)

        self.vista_stampanti = FrameGestioneStampante(self.tab_stampanti, None)
        self.vista_stampanti.pack(fill="both", expand=True)

        self.vista_admin = AdminView(self)

        # 5. IMPOSTAZIONE SCHEDA ATTIVA ALL'AVVIO
        # Cambiata la forzatura sulla prima scheda realmente visibile all'utente
        self.tabview.set("Risoluzione Problemi")

    def rilevato_cambio_tab(self):
        """Esegue automaticamente i controlli hardware in background all'accesso della tab."""
        scelta = self.tabview.get()
        if scelta == "Gestione Stampante" and hasattr(self, 'printer_controller'):
            self.printer_controller.cmd_rileva_stampanti(mostra_popup_esito=False)

    def imposta_controller(self, controller):
        """Collega le funzioni dei controller ai pulsanti delle sotto-viste (Anche quelle nascoste)."""
        
        # 1. Collegamenti del Main Controller (Pagine standard e nascoste)
        self.vista_driver.controller = controller
        self.vista_driver.btn_spooler.configure(command=controller.cmd_pulizia_spooler_stampa)
        self.vista_driver.btn_refresh_rete.configure(command=controller.cmd_refresh_internet_sicuro)
        self.vista_driver.btn_input.configure(command=controller.ripristina_input_hardware)
        self.vista_driver.btn_aggiornamento.configure(command=controller.aggiorna_app)
        self.vista_manuale.inizialiale_manuale = self.vista_manuale.inizializza_manuale(controller)
        
        # L'Admin mantiene tutti i suoi binding attivi in background per lo sviluppo
        self.vista_admin.controller = controller
        self.vista_admin.btn_aggiungi.configure(command=controller.aggiungi_guida_db)
        self.vista_admin.btn_modifica.configure(command=controller.modifica_guida_db)
        self.vista_admin.btn_elimina.configure(command=controller.elimina_guida_db)
        
        # ----------------------------------------------------------------------
        # 2. CREAZIONE E COLLEGAMENTO DEL CONTROLLER SEPARATO PER LA STAMPANTE
        # ----------------------------------------------------------------------
        self.printer_controller = PrinterManagerController(self.vista_stampanti)
        self.vista_stampanti.controller = self.printer_controller
        
        self.vista_stampanti.btn_scan.configure(
            command=lambda: self.printer_controller.cmd_rileva_stampanti(mostra_popup_esito=True)
        )
        
        self.vista_stampanti.btn_status.configure(command=self.printer_controller.cmd_click_status)
        self.vista_stampanti.btn_allinea.configure(command=self.printer_controller.cmd_riallinea_stampante)
        self.vista_stampanti.btn_reboot.configure(command=self.printer_controller.cmd_riavvia_stampante)
        self.vista_stampanti.btn_test.configure(command=self.printer_controller.cmd_stampa_prova)
        
        self.vista_stampanti.btn_installa_driver.configure(command=controller.ripristina_driver_zebra)
        
        if self.tabview.get() == "Gestione Stampante":
            self.printer_controller.cmd_rileva_stampanti(mostra_popup_esito=False)
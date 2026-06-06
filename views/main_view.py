import customtkinter as ctk
# Importiamo le viste separate che risiedono nella stessa cartella
from views.manuale_view import ManualeView
from views.ticket_view import TicketView
from views.driver_view import DriverView

class HelpDeskView(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Impostazioni della finestra principale (ingrandita per ospitare la guida)
        self.title("Help Desk Aziendale - Portale Supporto")
        self.geometry("850x650") 
        ctk.set_appearance_mode("System")
        
        # 1. Creazione del sistema a Schede (Tabview)
        self.tabview = ctk.CTkTabview(self, width=830, height=630)
        self.tabview.pack(pady=10, padx=10, fill="both", expand=True)
        
        # 2. Aggiungiamo le schede nell'ordine desiderato
        self.tab_manuale = self.tabview.add("Manuale di Risoluzione")
        self.tab_ticket = self.tabview.add("Apri un Ticket")
        self.tab_driver = self.tabview.add("Gestione Driver")
        
        # 3. Inizializziamo le sotto-viste dentro i rispettivi tab
        self.vista_manuale = ManualeView(self.tab_manuale)
        self.vista_manuale.pack(fill="both", expand=True)
        
        self.vista_ticket = TicketView(self.tab_ticket)
        self.vista_ticket.pack(fill="both", expand=True)
        
        self.vista_driver = DriverView(self.tab_driver)
        self.vista_driver.pack(fill="both", expand=True)

        # 4. FORZATURA: Seleziona la scheda del manuale come attiva all'avvio
        self.tabview.set("Manuale di Risoluzione")

    def imposta_controller(self, controller):
        """Collega le funzioni del controller ai pulsanti delle sotto-viste."""
        # Collega il pulsante invia del form ticket
        self.vista_ticket.btn_salva.configure(command=controller.salva_ticket)
        
        # Collega il pulsante della Zebra
        self.vista_driver.btn_zebra.configure(command=controller.ripristina_driver_zebra)
        
        # Inizializza i dati dinamici (i menu a tendina) del manuale prendendoli dal DB
        self.vista_manuale.inizializza_manuale(controller)
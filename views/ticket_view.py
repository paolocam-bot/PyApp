import customtkinter as ctk
from models.ticket_model import Urgenza

class TicketView(ctk.CTkFrame): # <-- Il nome deve essere esattamente TicketView
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Elementi Grafici del Form (Spostati qui dal vecchio main_view)
        self.label_titolo = ctk.CTkLabel(self, text="Nuovo Ticket", font=("Arial", 18, "bold"))
        self.label_titolo.pack(pady=15)
        
        self.entry_titolo = ctk.CTkEntry(self, placeholder_text="Oggetto del problema", width=300)
        self.entry_titolo.pack(pady=10)
        
        self.menu_urgenza = ctk.CTkOptionMenu(self, values=[u.value for u in Urgenza], width=300)
        self.menu_urgenza.pack(pady=10)
        
        self.txt_descrizione = ctk.CTkTextbox(self, width=300, height=100)
        self.txt_descrizione.insert("0.0", "Descrivi qui il problema...")
        self.txt_descrizione.pack(pady=10)
        
        # Pulsante di invio gestito dal controller
        self.btn_salva = ctk.CTkButton(self, text="Invia Ticket Help Desk")
        self.btn_salva.pack(pady=15)
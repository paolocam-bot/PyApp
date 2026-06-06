import customtkinter as ctk
from models.ticket_model import Urgenza

class HelpDeskView(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Help Desk Panel")
        self.geometry("450x500")
        ctk.set_appearance_mode("System")
        
        # Elementi Grafici
        self.label_titolo = ctk.CTkLabel(self, text="Nuovo Ticket", font=("Arial", 18, "bold"))
        self.label_titolo.pack(pady=15)
        
        self.entry_titolo = ctk.CTkEntry(self, placeholder_text="Oggetto del problema", width=300)
        self.entry_titolo.pack(pady=10)
        
        self.menu_urgenza = ctk.CTkOptionMenu(self, values=[u.value for u in Urgenza], width=300)
        self.menu_urgenza.pack(pady=10)
        
        self.txt_descrizione = ctk.CTkTextbox(self, width=300, height=100)
        self.txt_descrizione.insert("0.0", "Descrivi qui il problema...")
        self.txt_descrizione.pack(pady=10)
        
        self.separatore = ctk.CTkLabel(self, text="------------------------------------", text_color="gray")
        self.separatore.pack(pady=10)
        
        self.btn_zebra = ctk.CTkButton(self, text="Ripristina Driver Zebra", fg_color="darkgreen", hover_color="green")
        self.btn_zebra.pack(pady=5)
        
        self.btn_salva = ctk.CTkButton(self, text="Invia Ticket Help Desk")
        self.btn_salva.pack(pady=15)

    def imposta_controller(self, controller):
        self.btn_zebra.configure(command=controller.ripristina_driver_zebra)
        self.btn_salva.configure(command=controller.salva_ticket)
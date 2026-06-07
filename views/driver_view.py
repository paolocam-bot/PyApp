import customtkinter as ctk

class DriverView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Titolo della sezione all'interno della scheda
        self.label_titolo = ctk.CTkLabel(
            self, 
            text="Strumenti di Ripristino Rapido", 
            font=("Arial", 20, "bold")
        )
        self.label_titolo.pack(pady=20)
        
        self.label_sottotitolo = ctk.CTkLabel(
            self, 
            text="Se qualcosa non funziona, clicca sul pulsante corrispondente e accetta la richiesta di Windows.", 
            font=("Arial", 12, "italic")
        )
        self.label_sottotitolo.pack(pady=5)

        # --- PULSANTE 1: STAMPANTE ZEBRA ---
        self.btn_zebra = ctk.CTkButton(
            self, 
            text="Sblocca / Ripristina Stampante Zebra", 
            font=("Arial", 14, "bold"),
            fg_color="#1f538d", # Colore blu standard
            height=45,
            width=300
        )
        self.btn_zebra.pack(pady=15)

        # --- PULSANTE 2: TASTIERA E MOUSE (NUOVO) ---
        self.btn_input = ctk.CTkButton(
            self, 
            text="Sblocca Tastiera o Mouse Bloccati", 
            font=("Arial", 14, "bold"),
            fg_color="#2b712b", # Un bel verde per differenziarlo dalla stampante
            hover_color="#1e4e1e",
            height=45,
            width=300
        )
        self.btn_input.pack(pady=15)
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

        # Contenitore per i pulsanti (per mantenerli ordinati e centrati)
        self.button_container = ctk.CTkFrame(self, fg_color="transparent")
        self.button_container.pack(pady=10)

        # --- SEZIONE INPUT HARDWARE (Ex Pulsante 2, ora unico rimasto qui) ---
        self.btn_input = ctk.CTkButton(
            self.button_container, 
            text="Sblocca Tastiera o Mouse Bloccati", 
            font=("Arial", 14, "bold"),
            fg_color="#2b712b", 
            hover_color="#1e4e1e",
            height=45,
            width=300
        )
        self.btn_input.pack(pady=15)
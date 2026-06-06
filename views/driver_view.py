import customtkinter as ctk

class DriverView(ctk.CTkFrame): # <-- Il nome deve essere esattamente DriverView
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.label_titolo = ctk.CTkLabel(self, text="Manutenzione Driver", font=("Arial", 18, "bold"))
        self.label_titolo.pack(pady=15)
        
        self.separatore = ctk.CTkLabel(self, text="------------------------------------", text_color="gray")
        self.separatore.pack(pady=10)
        
        # Pulsante Zebra gestito dal controller
        self.btn_zebra = ctk.CTkButton(self, text="Ripristina Driver Zebra", fg_color="darkgreen", hover_color="green")
        self.btn_zebra.pack(pady=5)
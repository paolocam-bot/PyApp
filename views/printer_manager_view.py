import customtkinter as ctk
from tkinter import messagebox

class FrameGestioneStampante(ctk.CTkFrame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        
        # --- TITOLO ---
        self.lbl_titolo = ctk.CTkLabel(self, text="🖨️ CONTROLLO E MANUTENZIONE STAMPANTI", font=("Arial", 16, "bold"))
        self.lbl_titolo.pack(pady=(20, 10))
        
        # --- FRAME PER SELEZIONE DISPOSITIVO (UNIFICATO) ---
        self.frame_dispositivo = ctk.CTkFrame(self)
        self.frame_dispositivo.pack(pady=10, padx=30, fill="x")
        
        self.lbl_disp = ctk.CTkLabel(self.frame_dispositivo, text="Stampante Selezionata:")
        self.lbl_disp.pack(side="left", padx=10, pady=5)
        
        # ComboBox che conterrà sia stampanti USB che IP trovate
        self.cmb_dispositivo = ctk.CTkComboBox(
            self.frame_dispositivo, 
            values=["Ricerca in corso..."],
            width=300
        )
        self.cmb_dispositivo.pack(side="left", padx=10, fill="x", expand=True)

        # --- CONTENITORE PULSANTI OPERATIVI (CON SCROLLBAR INTEGRATA) ---
        self.frame_azioni = ctk.CTkScrollableFrame(self, orientation="vertical")
        self.frame_azioni.pack(pady=15, padx=30, fill="both", expand=True)
        
        # Pulsante Scansione / Riconfigurazione manuale
        self.btn_scan = ctk.CTkButton(self.frame_azioni, text="🔄 Cerca Stampanti", fg_color="#6366f1", font=("Arial", 13, "bold"))
        self.btn_scan.pack(pady=(15, 10), fill="x", padx=40)
        
        self.btn_status = ctk.CTkButton(
            self.frame_azioni, 
            text="🔍 Verifica Stato Errori Windows", 
            fg_color="#1f538d",
            command=lambda: self.controller.cmd_click_status() if self.controller else None
        )
        self.btn_status.pack(pady=10, fill="x", padx=40)
        
        self.btn_allinea = ctk.CTkButton(self.frame_azioni, text="📏 Riallinea Sensore (Calibrazione)", fg_color="#2b712b")
        self.btn_allinea.pack(pady=10, fill="x", padx=40)
        
        self.btn_reboot = ctk.CTkButton(self.frame_azioni, text="🔄 Spegni e Riaccendi (Reset)", fg_color="#9e3a3a")
        self.btn_reboot.pack(pady=10, fill="x", padx=40)
        
        self.btn_test = ctk.CTkButton(self.frame_azioni, text="📄 Effettua Stampa di Prova", fg_color="#d97706")
        self.btn_test.pack(pady=10, fill="x", padx=40)

        # --- PULSANTE DI SBLOCCO AREA PROTETTA ---
        self.btn_sblocca_admin = ctk.CTkButton(
            self.frame_azioni, 
            text="🔒 Sblocca Funzioni Avanzate (Richiede Password)", 
            fg_color="#374151",
            hover_color="#1f2937",
            command=self.richiedi_sblocco_admin
        )
        self.btn_sblocca_admin.pack(pady=20, fill="x", padx=40)

        # =====================================================================
        # --- CONTAINER NASCOSTO: MANUTENZIONE AVANZATA (PROTEZIONE PASSWORD) ---
        # =====================================================================
        self.frame_avanzato_nascosto = ctk.CTkFrame(self.frame_azioni, fg_color="transparent")
        # NOTA: Non facciamo il .pack() iniziale di questo frame per tenerlo nascosto

        # --- SEZIONE UTILITÀ (SPOSTAMENTO BOTTONE DRIVER) ---
        self.lbl_driver_info = ctk.CTkLabel(self.frame_avanzato_nascosto, text="La stampante non viene rilevata in nessun modo?", font=("Arial", 11, "italic"), text_color="gray")
        self.lbl_driver_info.pack(pady=(15, 2))

        self.btn_installa_driver = ctk.CTkButton(
            self.frame_avanzato_nascosto, 
            text="⚙️ Installa / Ripristina Driver Stampante", 
            fg_color="#4b5563",
            command=lambda: self.controller.cmd_manutenzione_totale_driver_indipendente() if self.controller else None
        )
        self.btn_installa_driver.pack(pady=(0, 15), fill="x", padx=40)

        # --- SEZIONE FORMATO FUSTELLA MODULARE ---
        self.btn_imposta_fustella = ctk.CTkButton(
            master=self.frame_avanzato_nascosto,  
            text="📐 Applica Formato Fustella",
            fg_color="#2563eb",
            command=lambda: self.controller.setta_formato_zebra_etichette() if self.controller else None
        )
        self.btn_imposta_fustella.pack(pady=10, fill="x", padx=40)

        # --- SEZIONE SCAMBIA CONFIGURAZIONI ---
        self.btn_scambia_porte = ctk.CTkButton(
            master=self.frame_avanzato_nascosto,  
            text="🔄 Scambia Configurazioni Porte",
            fg_color="#ffe604",
            text_color="black",
            command=lambda: self.controller.cmd_scambia_porte_zebra() if self.controller else None
        )
        self.btn_scambia_porte.pack(pady=10, fill="x", padx=40)

    def richiedi_sblocco_admin(self):
        """Mostra un input di testo per verificare i privilegi dell'operatore."""
        PASSWORD_CORRETTA = "admingdv2026"
        
        dialogo = ctk.CTkInputDialog(
            text="Inserisci la password per sbloccare i tool di manutenzione:", 
            title="Sblocco Funzioni Avanzate"
        )
        
        password_inserita = dialogo.get_input()
        
        if password_inserita == PASSWORD_CORRETTA:
            # Nascondiamo il bottone di sblocco
            self.btn_sblocca_admin.pack_forget()
            
            # Mostriamo il contenitore con i 3 bottoni avanzati
            self.frame_avanzato_nascosto.pack(pady=10, fill="x")
            messagebox.showinfo("Sbloccato", "Funzioni di amministrazione caricate correttamente.")
        elif password_inserita is not None:
            messagebox.showerror("Errore", "Password non valida! Accesso negato.")

    def get_dati_interfaccia(self):
        """Restituisce il target selezionato e deduce il tipo in base al testo."""
        scelta = self.cmb_dispositivo.get().strip()
        
        tipo = "USB"
        if "(Rete IP)" in scelta:
            tipo = "IP"
            scelta = scelta.replace(" (Rete IP)", "")
        elif "(Cavo USB)" in scelta:
            tipo = "USB"
            scelta = scelta.replace(" (Cavo USB)", "")
            
        return {
            "tipo": tipo,
            "target": scelta
        }
import customtkinter as ctk

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
        # Trasformato in CTkScrollableFrame per evitare il taglio dei bottoni inferiori
        self.frame_azioni = ctk.CTkScrollableFrame(self, orientation="vertical")
        self.frame_azioni.pack(pady=15, padx=30, fill="both", expand=True)
        
        # Pulsante Scansione / Riconfigurazione manuale
        self.btn_scan = ctk.CTkButton(self.frame_azioni, text="🔄 Riconfigura e Cerca Stampanti", fg_color="#6366f1", font=("Arial", 13, "bold"))
        self.btn_scan.pack(pady=(15, 10), fill="x", padx=40)
        
        self.btn_status = ctk.CTkButton(self.frame_azioni, text="🔍 Verifica Stato Errori (Get Status)", fg_color="#1f538d")
        self.btn_status.pack(pady=10, fill="x", padx=40)
        
        self.btn_allinea = ctk.CTkButton(self.frame_azioni, text="📏 Riallinea Sensore (Calibrazione)", fg_color="#2b712b")
        self.btn_allinea.pack(pady=10, fill="x", padx=40)
        
        self.btn_reboot = ctk.CTkButton(self.frame_azioni, text="🔄 Spegni e Riaccendi (Reset)", fg_color="#9e3a3a")
        self.btn_reboot.pack(pady=10, fill="x", padx=40)
        
        self.btn_test = ctk.CTkButton(self.frame_azioni, text="📄 Effettua Stampa di Prova", fg_color="#d97706")
        self.btn_test.pack(pady=10, fill="x", padx=40)

        # --- SEZIONE UTILITÀ (SPOSTAMENTO BOTTONE DRIVER) ---
        self.lbl_driver_info = ctk.CTkLabel(self.frame_azioni, text="La stampante non viene rilevata in nessun modo?", font=("Arial", 11, "italic"), text_color="gray")
        self.lbl_driver_info.pack(pady=(15, 2))

        self.btn_installa_driver = ctk.CTkButton(
            self.frame_azioni, 
            text="⚙️ Installa / Ripristina Driver Stampante", 
            fg_color="#4b5563",
            command=lambda: self.controller.cmd_manutenzione_totale_driver() if self.controller else None
        )
        self.btn_installa_driver.pack(pady=(0, 15), fill="x", padx=40)

        # --- SEZIONE FORMATO FUSTELLA MODULARE ---
        self.btn_imposta_fustella = ctk.CTkButton(
            master=self.frame_azioni,  
            text="📐 Applica Formato Fustella",
            fg_color="#2563eb",
            command=lambda: self.controller.setta_formato_zebra_etichette() if self.controller else None
        )
        self.btn_imposta_fustella.pack(pady=10, fill="x", padx=40)

        # --- SEZIONE SCAMBIA CONFIGURAZIONI ---
        self.btn_scambia_porte = ctk.CTkButton(
            master=self.frame_azioni,  
            text="🔄 Scambia Configurazioni Porte",
            fg_color="#ffe604",
            text_color="black",
            command=lambda: self.controller.cmd_scambia_porte_zebra() if self.controller else None
        )
        self.btn_scambia_porte.pack(pady=10, fill="x", padx=40)

    # --- NUOVO PULSANTE DI AVVERTIMENTO ---
        self.btn_non_cliccare = ctk.CTkButton(
            master=self.frame_azioni,
            text="⚠️ Non cliccare",
            fg_color="#ef4444", # Rosso vivido per dare un tono di avvertimento
            hover_color="#dc2626",
            font=("Arial", 12, "bold"),
            command=lambda: self.controller.noncliccare() if self.controller else None
        )
        self.btn_non_cliccare.pack(pady=10, fill="x", padx=40)
        
    def get_dati_interfaccia(self):
        """Restituisce il target selezionato e deduce il tipo in base al testo."""
        scelta = self.cmb_dispositivo.get().strip()
        
        # Capiamo se è un IP o una stampante USB dal testo inserito dal controller
        tipo = "USB"
        if "(Rete IP)" in scelta:
            tipo = "IP"
            # Puliamo la stringa tenendo solo l'IP numerico
            scelta = scelta.replace(" (Rete IP)", "")
        elif "(Cavo USB)" in scelta:
            tipo = "USB"
            scelta = scelta.replace(" (Cavo USB)", "")
            
        return {
            "tipo": tipo,
            "target": scelta
        }
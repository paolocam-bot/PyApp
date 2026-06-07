import customtkinter as ctk
from tkinter import messagebox, ttk

class AdminView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.controller = None
        self.id_selezionato = None  
        
        # --- 1. Schermata di Login ---
        self.frame_login = ctk.CTkFrame(self)
        self.frame_login.pack(pady=50, padx=20, fill="none", expand=True)
        
        ctk.CTkLabel(self.frame_login, text="Area Riservata Amministratore", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.ent_password = ctk.CTkEntry(self.frame_login, placeholder_text="Inserisci Password", show="*")
        self.ent_password.pack(pady=10, padx=20)
        
        self.btn_login = ctk.CTkButton(self.frame_login, text="Accedi", command=self.verifica_accesso)
        self.btn_login.pack(pady=10)
        
        # --- 2. Pannello di Gestione Principale (Creato subito, ma NON impacchettato) ---
        self.frame_gestione = ctk.CTkFrame(self)
        
        lbl_titolo = ctk.CTkLabel(self.frame_gestione, text="Elenco Guide nel Database", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_titolo.pack(pady=5)
        
        self.tree_frame = ctk.CTkFrame(self.frame_gestione)
        self.tree_frame.pack(pady=5, padx=10, fill="both", expand=True)
        
        colonne = ("id", "categoria", "problema", "step", "descrizione")
        self.tabella = ttk.Treeview(self.tree_frame, columns=colonne, show="headings", height=6)
        self.tabella.heading("id", text="ID")
        self.tabella.heading("categoria", text="Categoria")
        self.tabella.heading("problema", text="Problema")
        self.tabella.heading("step", text="N° Step")
        self.tabella.heading("descrizione", text="Descrizione Soluzione")
        
        self.tabella.column("id", width=40, anchor="center")
        self.tabella.column("categoria", width=100)
        self.tabella.column("problema", width=150)
        self.tabella.column("step", width=60, anchor="center")
        self.tabella.column("descrizione", width=300)
        
        self.tabella.pack(side="left", fill="both", expand=True)
        self.tabella.bind("<<TreeviewSelect>>", self.riga_selezionata)
        
        self.form_frame = ctk.CTkFrame(self.frame_gestione)
        self.form_frame.pack(pady=10, padx=10, fill="x")
        
        self.ent_categoria = ctk.CTkEntry(self.form_frame, placeholder_text="Categoria")
        self.ent_categoria.pack(side="top", pady=2, padx=10, fill="x")
        
        self.ent_problema = ctk.CTkEntry(self.form_frame, placeholder_text="Problema")
        self.ent_problema.pack(side="top", pady=2, padx=10, fill="x")
        
        self.ent_step_num = ctk.CTkEntry(self.form_frame, placeholder_text="Numero Step")
        self.ent_step_num.pack(side="top", pady=2, padx=10, fill="x")
        
        self.txt_descrizione = ctk.CTkTextbox(self.form_frame, height=60)
        self.txt_descrizione.pack(side="top", pady=2, padx=10, fill="x")
        
        self.ent_path_media = ctk.CTkEntry(self.form_frame, placeholder_text="Path immagine o Link Video")
        self.ent_path_media.pack(side="top", pady=2, padx=10, fill="x")
        
        self.btn_frame = ctk.CTkFrame(self.frame_gestione, fg_color="transparent")
        self.btn_frame.pack(pady=10, padx=10, fill="x")
        
        # Ora i pulsanti esistono dal primo millisecondo di vita dell'app!
        self.btn_aggiungi = ctk.CTkButton(self.btn_frame, text="Aggiungi Nuovo", fg_color="green", hover_color="darkgreen")
        self.btn_aggiungi.pack(side="left", padx=5, expand=True, fill="x")
        
        self.btn_modifica = ctk.CTkButton(self.btn_frame, text="Salva Modifiche", fg_color="#1f538d")
        self.btn_modifica.pack(side="left", padx=5, expand=True, fill="x")
        
        self.btn_elimina = ctk.CTkButton(self.btn_frame, text="Elimina Selezionato", fg_color="red", hover_color="darkred")
        self.btn_elimina.pack(side="left", padx=5, expand=True, fill="x")

    def verifica_accesso(self):
        if self.ent_password.get() == "admin1998":
            self.frame_login.pack_forget()
            self.mostra_pannello_gestione()
            if self.controller:
                self.controller.carica_tabella_admin()
        else:
            messagebox.showerror("Errore", "Password errata!")
            
    def mostra_pannello_gestione(self):
        # Questo metodo ora si limita a mostrare a schermo il frame già pronto
        self.frame_gestione.pack(pady=10, padx=10, fill="both", expand=True)

    def riga_selezionata(self, event):
        item = self.tabella.selection()
        if not item:
            return
            
        valori = self.tabella.item(item, "values")
        self.id_selezionato = valori[0]
        
        self.ent_categoria.delete(0, "end")
        self.ent_categoria.insert(0, valori[1])
        
        self.ent_problema.delete(0, "end")
        self.ent_problema.insert(0, valori[2])
        
        self.ent_step_num.delete(0, "end")
        self.ent_step_num.insert(0, valori[3])
        
        self.txt_descrizione.delete("0.0", "end")
        self.txt_descrizione.insert("0.0", valori[4])
        
        if self.controller:
            self.controller.recupera_media_per_form(self.id_selezionato)
            
    def svuota_form(self):
        self.id_selezionato = None
        self.ent_categoria.delete(0, "end")
        self.ent_problema.delete(0, "end")
        self.ent_step_num.delete(0, "end")
        self.txt_descrizione.delete("0.0", "end")
        self.ent_path_media.delete(0, "end")
        self.tabella.selection_remove(self.tabella.selection())
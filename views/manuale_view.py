import os
import customtkinter as ctk
import webbrowser
from PIL import Image

class ManualeView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.controller = None
        self.problemi_correnti = []
        self.steps_correnti = []
        self.indice_step_corrente = 0
        
        # Dividiamo la schermata: Sinistra (Filtri) e Destra (Risoluzione Step-by-Step)
        self.colonna_sinistra = ctk.CTkFrame(self, width=250)
        self.colonna_sinistra.pack(side="left", fill="y", padx=10, pady=10)
        
        self.colonna_destra = ctk.CTkFrame(self)
        self.colonna_destra.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # --- ELEMENTI COLONNA SINISTRA ---
        ctk.CTkLabel(self.colonna_sinistra, text="Filtri Ricerca", font=("Arial", 14, "bold")).pack(pady=10)
        
        self.menu_macro = ctk.CTkOptionMenu(self.colonna_sinistra, values=["Seleziona..."], command=self.on_macro_cambiata)
        self.menu_macro.pack(pady=10, padx=10, fill="x")
        
        self.menu_sotto = ctk.CTkOptionMenu(self.colonna_sinistra, values=["Seleziona..."], command=self.on_sotto_cambiata)
        self.menu_sotto.pack(pady=10, padx=10, fill="x")
        
        self.menu_problemi = ctk.CTkOptionMenu(self.colonna_sinistra, values=["Seleziona..."], command=self.on_problema_selezionato)
        self.menu_problemi.pack(pady=10, padx=10, fill="x")
        
        # --- ELEMENTI COLONNA DESTRA (Dettaglio Guida) ---
        self.lbl_titolo_problema = ctk.CTkLabel(self.colonna_destra, text="Seleziona un problema dal menu a sinistra", font=("Arial", 16, "bold"), wraplength=450)
        self.lbl_titolo_problema.pack(pady=15, padx=10)
        
        self.lbl_passo_num = ctk.CTkLabel(self.colonna_destra, text="", font=("Arial", 12, "italic"))
        self.lbl_passo_num.pack(pady=5)
        
        self.txt_guida = ctk.CTkLabel(self.colonna_destra, text="", font=("Arial", 13), wraplength=450, justify="left")
        self.txt_guida.pack(pady=15, padx=10)
        
        self.lbl_immagine = ctk.CTkLabel(self.colonna_destra, text="") # Contenitore per le foto dello step
        self.lbl_immagine.pack(pady=10)
        
        self.btn_video = ctk.CTkButton(self.colonna_destra, text="🎬 Guarda Video Tutorial", fg_color="purple", command=self.apri_video_step)
        
        # Pulsanti Navigazione Step
        self.frame_navigazione = ctk.CTkFrame(self.colonna_destra, fg_color="transparent")
        self.frame_navigazione.pack(side="bottom", pady=20)
        
        self.btn_precedente = ctk.CTkButton(self.frame_navigazione, text="⬅ Precedente", command=self.passo_precedente, width=100)
        self.btn_precedente.pack(side="left", padx=10)
        
        self.btn_successivo = ctk.CTkButton(self.frame_navigazione, text="Successivo ➡", command=self.passo_successivo, width=100)
        self.btn_successivo.pack(side="left", padx=10)

    def inizializza_manuale(self, controller):
        """Viene chiamata dal main_view per caricare i primi dati dal DB."""
        self.controller = controller
        macro_categorie = self.controller.ottieni_macro_categorie()
        if macro_categorie:
            self.menu_macro.configure(values=macro_categorie)
            self.menu_macro.set(macro_categorie[0])
            self.on_macro_cambiata(macro_categorie[0])

    def on_macro_cambiata(self, scelta):
        """Quando l'utente cambia la Macro Categoria, aggiorna la Sotto Categoria."""
        sotto_cat = self.controller.ottieni_sotto_categorie(scelta)
        if sotto_cat:
            self.menu_sotto.configure(values=sotto_cat)
            self.menu_sotto.set(sotto_cat[0])
            self.on_sotto_cambiata(sotto_cat[0])
        else:
            self.menu_sotto.configure(values=["Nessuna"])
            self.menu_sotto.set("Nessuna")

    def on_sotto_cambiata(self, scelta):
        """Quando cambia la Sotto Categoria, aggiorna la lista dei Problemi."""
        macro = self.menu_macro.get()
        self.problemi_correnti = self.controller.ottieni_problemi(macro, scelta)
        
        titoli_problemi = [p.titolo for p in self.problemi_correnti]
        if titoli_problemi:
            self.menu_problemi.configure(values=titoli_problemi)
            self.menu_problemi.set(titoli_problemi[0])
            self.on_problema_selezionato(titoli_problemi[0])
        else:
            self.menu_problemi.configure(values=["Nessun problema trovato"])
            self.menu_problemi.set("Nessun problema trovato")

    def on_problema_selezionato(self, titolo_scelto):
        """Carica tutti gli step dal DB relativi al problema cliccato."""
        problema_selezionato = next((p for p in self.problemi_correnti if p.titolo == titolo_scelto), None)
        if problema_selezionato:  # <-- Controlla che qui ci sia scritto questo
            self.lbl_titolo_problema.configure(text=problema_selezionato.titolo)
            self.steps_correnti = self.controller.ottieni_steps_problema(problema_selezionato.id_problema)
            self.indice_step_corrente = 0
            self.mostra_step()

    def mostra_step(self):
        """Visualizza i dati dello step corrente (testo, immagine, video)."""
        if not self.steps_correnti:
            self.lbl_passo_num.configure(text="")
            self.txt_guida.configure(text="Nessun passaggio inserito nel database per questo problema.")
            self.lbl_immagine.configure(image="")
            self.btn_video.pack_forget()
            return
            
        step = self.steps_correnti[self.indice_step_corrente]
        
        # Aggiorna Testo
        self.lbl_passo_num.configure(text=f"Passo {self.indice_step_corrente + 1} di {len(self.steps_correnti)}")
        self.txt_guida.configure(text=step.testo)
        
        # Gestione Immagine Dinamica
        if step.immagine_path and os.path.exists(step.immagine_path):
            try:
                img = ctk.CTkImage(light_image=Image.open(step.immagine_path), size=(250, 180))
                self.lbl_immagine.configure(image=img)
            except Exception:
                self.lbl_immagine.configure(image="", text="[Errore caricamento immagine]")
        else:
            self.lbl_immagine.configure(image="", text="") # Nessuna immagine
            
        # Gestione Pulsante Video Dinamico
        if step.video_url:
            self.btn_video.pack(pady=10)
        else:
            self.btn_video.pack_forget()

    def passo_successivo(self):
        if self.indice_step_corrente < len(self.steps_correnti) - 1:
            self.indice_step_corrente += 1
            self.mostra_step()

    def passo_precedente(self):
        if self.indice_step_corrente > 0:
            self.indice_step_corrente -= 1
            self.mostra_step()

    def apri_video_step(self):
        if self.steps_correnti:
            url = self.steps_correnti[self.indice_step_corrente].video_url
            if url:
                webbrowser.open(url)
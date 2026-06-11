import json
import os
import glob
import sys
import subprocess
import urllib.request
import customtkinter as ctk
from tkinter import messagebox 

GITHUB_RELEASE_URL = "https://api.github.com/repos/paolocam-bot/PyApp/releases/latest"

# =====================================================================
# METODI UTILITY / LOGICA AGGIORNAMENTI (Fuori dalla classe o nel controller)
# =====================================================================

def get_app_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    current_file = os.path.abspath(__file__)
    return os.path.dirname(os.path.dirname(current_file))

# =====================================================================
# CLASSE VIEW (INTERFACCIA GRAFICA AGGIORNATA)
# =====================================================================

class DriverView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Inizializziamo il riferimento al controller
        self.controller = None

        # CONFIGURAZIONE COLONNA PER ALLINEAMENTO CENTRATO E COERENTE
        self.grid_columnconfigure(0, weight=1)

        # 1. TITOLO DELLA SEZIONE
        self.label_titolo = ctk.CTkLabel(
            self, 
            text="Strumenti di Ripristino Rapido", 
            font=("Arial", 20, "bold")
        )
        self.label_titolo.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="ew")
        
        # 2. SOTTOTITOLO
        self.label_sottotitolo = ctk.CTkLabel(
            self, 
            text="Se qualcosa non funziona, clicca sul pulsante corrispondente e accetta la richiesta di Windows.", 
            font=("Arial", 12, "italic"),
            wraplength=450  # Manda a capo il testo se la finestra è stretta
        )
        self.label_sottotitolo.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Configurazione comune per i bottoni per garantire dimensioni e stile identici
        STILE_BOTTONI = {
            "font": ("Arial", 14, "bold"),
            "height": 45,
            "width": 300,
            "sticky": "ew",
            "padx": 40,
            "pady": 10
        }

        # --- BOTTONE 1: PULIZIA SPOOLER ---
        self.btn_spooler = ctk.CTkButton(
            self,
            text="Sblocca e Pulisci Spooler Stampa",
            font=STILE_BOTTONI["font"],
            height=STILE_BOTTONI["height"],
            width=STILE_BOTTONI["width"],
            command=lambda: self.controller.cmd_pulizia_spooler_stampa() if self.controller else None
        )
        self.btn_spooler.grid(row=2, column=0, padx=STILE_BOTTONI["padx"], pady=STILE_BOTTONI["pady"], sticky=STILE_BOTTONI["sticky"])

        # --- BOTTONE 2: REFRESH INTERNET ---
        self.btn_refresh_rete = ctk.CTkButton(
            self,
            text="Ripristina Connessione Internet",
            font=STILE_BOTTONI["font"],
            height=STILE_BOTTONI["height"],
            width=STILE_BOTTONI["width"],
            command=lambda: self.controller.cmd_refresh_internet_sicuro() if self.controller else None
        )
        self.btn_refresh_rete.grid(row=3, column=0, padx=STILE_BOTTONI["padx"], pady=STILE_BOTTONI["pady"], sticky=STILE_BOTTONI["sticky"])

        # --- BOTTONE 3: INPUT HARDWARE (Tastiera/Mouse) ---
        self.btn_input = ctk.CTkButton(
            self, 
            text="Sblocca Tastiera o Mouse Bloccati", 
            font=STILE_BOTTONI["font"],
            fg_color="#2b712b", 
            hover_color="#1e4e1e",
            height=STILE_BOTTONI["height"],
            width=STILE_BOTTONI["width"],
            command=lambda: self.controller.installa_driver_zebra() if self.controller else None # Cambia con la funzione hardware corretta se necessario
        )
        self.btn_input.grid(row=4, column=0, padx=STILE_BOTTONI["padx"], pady=STILE_BOTTONI["pady"], sticky=STILE_BOTTONI["sticky"])

        # --- BOTTONE 4: AGGIORNAMENTO ---
        self.btn_aggiornamento = ctk.CTkButton(
            self,
            text="🔄 Aggiornamento",
            font=STILE_BOTTONI["font"],
            fg_color="#0f766e",
            hover_color="#0b5f57",
            height=STILE_BOTTONI["height"],
            width=STILE_BOTTONI["width"],
            command=lambda: self.controller.aggiorna_app() if self.controller else None
        )
        self.btn_aggiornamento.grid(row=5, column=0, padx=STILE_BOTTONI["padx"], pady=STILE_BOTTONI["pady"], sticky=STILE_BOTTONI["sticky"])
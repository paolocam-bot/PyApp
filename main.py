import customtkinter as ctk
import sys
from views.main_view import HelpDeskView
from controllers.main_controller import HelpDeskController # Sostituisci con il nome reale se diverso

def main():
    # Inizializziamo momentaneamente un'istanza nascosta per usare i dialoghi di CustomTkinter
    app_temporanea = ctk.CTk()
    app_temporanea.withdraw() # Nasconde la finestra principale vuota

    # Impostiamo la password corretta
    PASSWORD_CORRETTA = "gdvstampanti"

    # Mostriamo il popup di richiesta password
    dialogo = ctk.CTkInputDialog(
        text="Inserisci la password di sicurezza per accedere:", 
        title="Accesso Riservato"
    )
    password_inserita = dialogo.get_input()

    # Controlliamo se la password è corretta
    if password_inserita != PASSWORD_CORRETTA:
        # Se è sbagliata o l'utente preme "Cancel", chiudiamo tutto
        print("[ACCESSO NEGATO] Password errata o non inserita.")
        app_temporanea.destroy()
        sys.exit()

    # Se la password è corretta, distruggiamo la finestra temporanea e avviamo l'app vera
    app_temporanea.destroy()

    # Avvio normale dell'applicazione
    app_view = HelpDeskView()
    app_controller = HelpDeskController(app_view) # Configura in base a come istanzi il tuo controller
    app_view.imposta_controller(app_controller)
    
    app_view.mainloop()

if __name__ == "__main__":
    main()

def controlla_aggiornamenti_silenzioso():
    print("[AGGIORNAMENTO] Controllo release GitHub all'avvio...")
    
    scaricati = scarica_asset_mancanti()
    
    if scaricati is None:
        print("[AGGIORNAMENTO] Errore di rete o GitHub. Avvio normale.")
        return

    # Se lo zip temporaneo è stato scaricato con successo
    if scaricati and "ControlloStampanti_nuovo.zip" in scaricati:
        cartella_app = get_app_base_dir()
        percorso_bat = os.path.join(cartella_app, "scripts", "aggiornamento.bat")
        
        if os.path.exists(percorso_bat):
            print("[AGGIORNAMENTO] Nuovo pacchetto trovato! Lancio lo script .bat...")
            try:
                import subprocess
                subprocess.Popen(
                    ["powershell", "-Command", f"Start-Process '{percorso_bat}' -Verb RunAs"],
                    shell=True,
                )
                # CHIUSURA IMMEDIATA: Sblocca ControlloStampanti.exe per consentire la sovrascrittura
                sys.exit(0)
            except Exception as e:
                print(f"[ERRORE AGGIORNAMENTO] Impossibile avviare il file .bat: {e}")
        else:
            print(f"[ERRORE AGGIORNAMENTO] Script .bat non trovato in: {percorso_bat}")
import subprocess
import sys

class FakeController:
    """Una classe finta per simulare il controller senza la GUI."""
    
    def esegui_singolo_comando(self, comando):
        try:
            # Usiamo capture_output per vedere se Windows risponde con degli errori
            risultato = subprocess.run(comando, shell=True, check=True, text=True, capture_output=True)
            print(f" [OK] Successo: {comando}")
            if risultato.stdout:
                print(risultato.stdout)
        except subprocess.CalledProcessError as e:
            print(f" [ERRORE] Durante l'esecuzione di: {comando}", file=sys.stderr)
            print(f"Codice errore: {e.returncode}", file=sys.stderr)
            print(f"Dettaglio errore: {e.stderr}", file=sys.stderr)

    def cmd_manutenzione_totale_driver(self):  
        print("=== INIZIO TEST DRIVER ===")
        
        # 1. RIMOZIONE DELLA STAMPANTE "GARANZIE"
        print("\nRimozione stampante GARANZIE...")
        cmd_rimuovi_garanzie = 'rundll32 printui.dll,PrintUIEntry /dl /n "GARANZIE" /q'
        self.esegui_singolo_comando(cmd_rimuovi_garanzie)

        # 2. RIMOZIONE DELLA STAMPANTE "ZEBRA"
        print("\nRimozione stampante ZEBRA...")
        cmd_rimuovi_zebra = 'rundll32 printui.dll,PrintUIEntry /dl /n "ZEBRA" /q'
        self.esegui_singolo_comando(cmd_rimuovi_zebra)

        # 3. INSTALLAZIONE DELLA STAMPANTE "GARANZIE"
        print("\nInstallazione stampante GARANZIE e relativi driver...")
        cmd_installa_garanzie = (
            'rundll32 printui.dll,PrintUIEntry /if /b "GARANZIE" '
            '/f "C:\\Users\\PaoloCa\\Desktop\\Progetti_App\\PyApp\\drivers\\ZBRN\\Win64\\ZBRN.inf" '
            '/r "USB001" /m "ZDesigner GK420d"'
        )
        self.esegui_singolo_comando(cmd_installa_garanzie)

        print("\n=== FINE TEST: Procedura completata. ===")

# Questo blocco fa partire il test quando lanci il file da CMD
if __name__ == "__main__":
    tester = FakeController()
    tester.cmd_manutenzione_totale_driver()
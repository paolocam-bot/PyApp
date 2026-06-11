import subprocess
import sys
import os

class FakeController:
    """Una classe finta per simulare il controller senza la GUI.

    def esegui_singolo_comando_sicuro(self, comando_lista, cartella_lavoro=None):
        try:
            risultato = subprocess.run(
                comando_lista,
                check=True,
                text=True,
                capture_output=True,
                creationflags=0x08000000,
                cwd=cartella_lavoro
            )
            print(f" [OK] Successo: {' '.join(comando_lista)}")
            if risultato.stdout:
                print(risultato.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f" [ERRORE] Durante l'esecuzione di: {' '.join(comando_lista)}", file=sys.stderr)
            print(f"Codice errore: {e.returncode}", file=sys.stderr)
            print(f"Dettaglio errore: {e.stderr}", file=sys.stderr)
            return False

    def _recupera_porte_usb_disponibili(self):

        import win32print
        porte_rilevate = []

        # Enumera tutte le porte del sistema con livello di dettaglio 1
        for porta_info in win32print.EnumPorts(None, 1):
            # Correggiamo 'pName' in 'Name' per evitare il KeyError
            p_name = porta_info.get('Name', '')
            if p_name.upper().startswith("USB"):
                porte_rilevate.append(p_name)

        # Ordina le porte (USB001, USB002, etc.)
        porte_rilevate.sort()

        # Se non trova porte USB attive (es. nessuna stampante USB è mai stata installata prima),
        # prepariamo un fallback standard sicuro
        if not porte_rilevate:
            porte_rilevate = ["USB001", "USB002", "USB003"]

        return porte_rilevate
    def cmd_manutenzione_totale_driver(self):
        print("=== INIZIO MANUTENZIONE E INSTALLAZIONE DRIVER ===")
        import os
        import sys

        # 1. Calcolo dinamico della cartella dei driver
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            if "controllers" in base_dir:
                base_dir = os.path.dirname(base_dir)

        cartella_win64 = os.path.join(base_dir, "drivers", "ZBRN", "Win64")
        percorso_inf = os.path.join(cartella_win64, "ZBRN.inf")

        print(f"Rilevato percorso driver: {percorso_inf}")

        if not os.path.exists(percorso_inf):
            print(f" [STOP] Il file non esiste fisicamente in questo percorso!")
            return

        # 2. Rilevamento dinamico delle porte USB
        porte_usb = self._recupera_porte_usb_disponibili()
        print(f"Porte USB di stampa rilevate nel sistema: {porte_usb}")

        # Assegniamo le porte in modo che non si sovrappongano
        porta_garanzie = porte_usb[0]
        # Se c'è una seconda porta USB usa quella, altrimenti calcola la successiva (es: USB002)
        if len(porte_usb) > 1:
            porta_zebra = porte_usb[1]
        else:
            numero_successivo = int(''.join(filter(str.isdigit, porta_garanzie))) + 1
            porta_zebra = f"USB{numero_successivo:03d}"

        print(f"-> Assegnazione dinamica: GARANZIE su {porta_garanzie} | ZEBRA su {porta_zebra}")

        # 3. PULIZIA VECCHIE INSTALLAZIONI
        print("\nRimozione vecchie istanze (se presenti)...")
        self.esegui_singolo_comando_sicuro(["rundll32", "printui.dll,PrintUIEntry", "/dl", "/n", "GARANZIE", "/q"])
        self.esegui_singolo_comando_sicuro(["rundll32", "printui.dll,PrintUIEntry", "/dl", "/n", "ZEBRA", "/q"])

        # 4. INSTALLAZIONE MULTIPLA
        # Nome del modello esatto descritto nel file .inf di Zebra
        modello_driver = "ZDesigner GK420d"

        print(f"\nInstallazione stampante 'GARANZIE' su {porta_garanzie}...")
        cmd_garanzie = [
            "rundll32", "printui.dll,PrintUIEntry", "/if",
            "/b", "GARANZIE",
            "/f", percorso_inf,
            "/r", porta_garanzie,
            "/m", modello_driver
        ]
        self.esegui_singolo_comando_sicuro(cmd_garanzie, cartella_lavoro=cartella_win64)

        print(f"\nInstallazione stampante 'ZEBRA' su {porta_zebra}...")
        cmd_zebra = [
            "rundll32", "printui.dll,PrintUIEntry", "/if",
            "/b", "ZEBRA",
            "/f", percorso_inf,
            "/r", porta_zebra,
            "/m", modello_driver
        ]
        self.esegui_singolo_comando_sicuro(cmd_zebra, cartella_lavoro=cartella_win64)

        print("\n=== CONFIGURAZIONE COMPLETATA: Entrambe le stampanti sono state configurate. ===")
# Questo blocco fa partire il test quando lanci il file da CMD
if __name__ == "__main__":
    tester = FakeController()
    tester.cmd_manutenzione_totale_driver()
    """


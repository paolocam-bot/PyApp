# HardwareHero a automatic installer driver end manual of problemsolving 

Un'applicazione desktop intuitiva e leggera sviluppata in Python utilizzando **CustomTkinter** (interfaccia grafica moderna basata su Tkinter) basata sul pattern architetturale **MVC (Model-View-Controller)**. L'app offre un manuale di risoluzione rapida per i problemi IT aziendali (stampanti, rete, ecc.), un sistema di apertura ticket locale e un pannello amministratore protetto da password per la gestione (CRUD) delle guide direttamente dall'interfaccia.

---

## Guida Rapida alla Preparazione dell'Ambiente (`.venv`)

Per garantire la massima stabilità e compatibilità con le librerie (incluso il supporto a Python 3.10+ fino alle versioni pre-rilascio), l'applicazione utilizza un ambiente virtuale isolato.

### 1. Clonare il Repository
Apri il terminale (o il Prompt dei comandi) e clona il progetto sul tuo computer:
```bash
git clone [https://github.com/IL_TUO_USERNAME/PyApp.git](https://github.com/IL_TUO_USERNAME/PyApp.git)
cd PyApp
```

### 2.1 Creazione ambiente virtuale MacOs/Linux
```bash
# Creazione dell'ambiente virtuale
python3 -m venv .venv

# Attivazione dell'ambiente
source .venv/bin/activate
```

### 2.2 Creazione ambiente virtuale Windows 
```bash
# Creazione dell'ambiente virtuale
python -m venv .venv

# Attivazione su PowerShell:
.venv\\Scripts\\Activate.ps1

# Oppure attivazione su Prompt dei Comandi (CMD):
.venv\\Scripts\\activate.bat
```

### 3 Installazione dipendenze 
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4 avvio applicativo sviluppo

```bash
# MacOs/Linux
python3 main.py
```
```bash
# Windows
python main.py
```
### 4 Conversione in un unico File Esecutivo

```bash
# Installare dento la venv
pip install pyinstaller
```
#### Compilazione su Windows Pypinstaller (Generazione del file .exe)
```bash
# Windows
pyinstaller --noconfirm --onedir --windowed --add-data "helpdesk.db;." --add-data "assets;assets" --icon="app_icon.ico" main.py
```


#### Compilazione su macOS (Generazione del file .app)
```bash
# MacOs
pyinstaller --noconfirm --onedir --windowed --add-data "helpdesk.db:." --add-data "assets:assets" main.py
```
## 📦 Compilazione Avanzata con Nuitka (Consigliata)

Nuitka compila il codice Python direttamente in C, garantendo performance elevate e una maggiore protezione del codice sorgente.

### Installazione di Nuitka
```bash
pip install nuitka
```

### compilazione nuitka
```bash
python -m nuitka --standalone --windowed --output-filename=HardwareHero --include-data-file=helpdesk.db=helpdesk.db --include-data-dir=assets=assets --include-data-dir=driver=driver --include-data-dir=scripts=scripts --windows-icon-from-ico=assets/app_icon.ico main.py
```

nuitka --standalone --onefile --windows-disable-console --include-data-dir=scripts=scripts --include-data-dir=drivers=drivers main.py
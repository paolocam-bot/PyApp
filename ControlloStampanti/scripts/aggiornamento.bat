@echo off
:: Attende 3 secondi per dare il tempo a ControlloStampanti.exe di chiudersi del tutto
timeout /t 3 /nobreak > nul

:: Sposta la linea di comando nella cartella principale (salendo da "scripts")
cd /d "%~dp0\.."

:: Controlla se esiste il file dell'aggiornamento scaricato
if exist "ControlloStampanti_nuovo.zip" (
    echo Estrazione aggiornamento di ControlloStampanti in corso...
    
    :: Forza l'estrazione sovrascrivendo i vecchi file nella cartella di installazione
    powershell -Command "Expand-Archive -Path 'ControlloStampanti_nuovo.zip' -DestinationPath '.' -Force"
    
    :: Rimuove il file zip temporaneo
    del /f /q "ControlloStampanti_nuovo.zip"
)

echo Riavvio dell'applicazione aggiornata...
:: Lancia il nuovo eseguibile principale
start "" "ControlloStampanti.exe"

exit
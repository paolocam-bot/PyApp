@echo off
:: Forza l'esecuzione come Amministratore
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :inizio
) else (
    echo Richiesti i permessi di amministratore...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:inizio
cls
echo ====================================================
echo   RIPRISTINO, CONFIGURAZIONE E TARATURA ZEBRA
echo ====================================================
echo.

:: 1. SVUOTA LA CODA DI STAMPA DI WINDOWS
echo [1/6] Arresto dello Spooler e pulizia della coda...
net stop spooler >nul 2>&1
del /Q /F /S "%systemroot%\System32\Spool\Printers\*.*" >nul 2>&1
net start spooler >nul 2>&1

:: 2. DISINSTALLAZIONE VECCHIE STAMPANTI BLOCCATE
echo [2/6] Rimozione vecchie stampanti ZEBRA e GARANZIE...
rundll32 printui.dll,PrintUIEntry /dl /n "ZEBRA" >nul 2>&1
rundll32 printui.dll,PrintUIEntry /dl /n "GARANZIE" >nul 2>&1

:: 3. INSTALLAZIONE E RINOMINA IN AUTONOMIA
echo [3/6] Installazione porte e associazione driver...

:: Installa sulla porta USB001 e rinomina in "ZEBRA"
rundll32 printui.dll,PrintUIEntry /if /b "ZEBRA" /f "%~dp0ZebraDriver.inf" /r "USB001" /m "Zebra Designer v8" >nul 2>&1

:: Installa sulla porta USB002 e rinomina in "GARANZIE"
rundll32 printui.dll,PrintUIEntry /if /b "GARANZIE" /f "%~dp0ZebraDriver.inf" /r "USB002" /m "Zebra Designer v8" >nul 2>&1

:: 4. IMPOSTAZIONE STAMPANTE PRIMARIA (PREDEFINITA)
echo [4/6] Impostazione di ZEBRA come stampante primaria...
rundll32 printui.dll,PrintUIEntry /y /n "ZEBRA"

:: 5. SETTAGGI HARDCODED TRAMITE POWERSHELL (Driver Windows)
echo [5/6] Configurazione layout geometrico hardcoded...
:: ZEBRA: 70mm altezza x 100mm larghezza, Orizzontale
powershell -Command "Set-PrintConfiguration -PrinterName 'ZEBRA' -PaperSize 'UserDefined' -LabelHeight 70mm -LabelWidth 100mm -Orientation Landscape" >nul 2>&1

:: GARANZIE: 30mm altezza x 40mm larghezza, Orizzontale
powershell -Command "Set-PrintConfiguration -PrinterName 'GARANZIE' -PaperSize 'UserDefined' -LabelHeight 30mm -LabelWidth 40mm -Orientation Landscape" >nul 2>&1

:: 6. TARATURA HARDWARE, ORIENTAMENTO INTERNO E RESET TOTALE (Comandi ZPL)
echo [6/6] Invio comandi hardware ZPL e taratura ottica...

:: Condividi temporaneamente le stampanti in locale per inviare i comandi echo
net share ZEBRA_SHARE=C:\ /grant:everyone,full >nul 2>&1
net share GAR_SHARE=C:\ /grant:everyone,full >nul 2>&1

:: --- Configurazione e Taratura Hardware per "ZEBRA" ---
(
echo ^XA
echo ^PW800
echo ^LL560
echo ^POI
echo ^~JA
echo ^~JR
echo ^XA^JUS^XZ
) > \\localhost\ZEBRA

:: --- Configurazione e Taratura Hardware per "GARANZIE" ---
(
echo ^XA
echo ^PW320
echo ^LL240
echo ^POI
echo ^~JA
echo ^~JR
echo ^XA^JUS^XZ
) > \\localhost\GARANZIE

echo.
echo ====================================================
echo   OPERAZIONE COMPLETATA! Le stampanti sono pronte.
echo ====================================================
timeout /t 3
exit
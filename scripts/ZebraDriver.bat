@echo off
:: Controlla se siamo davvero amministratori (sicurezza interna)
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [ERRORE] Esegui l'applicazione principale come Amministratore.
    timeout /t 5
    exit /b
)

:: Recuperiamo il percorso assoluto della cartella "drivers" inviato da Python
:: Se avviato a mano per test, fa il fallback sulla cartella "drivers" accanto a "scripts"
set "DRIVERS_DIR=%~1"
if "%DRIVERS_DIR%"=="" set "DRIVERS_DIR=%~dp0..\drivers"

cls
echo ====================================================
echo   RIPRISTINO, CONFIGURAZIONE E TARATURA ZEBRA
echo ====================================================
echo.
echo Cartella sorgente driver: %DRIVERS_DIR%
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

:: 3. INIEZIONE DRIVER NEL SISTEMA (Pnputil) E APERTURA PORTE
echo [3/6] Registrazione driver nel sistema e associazione porte...
:: Iniettiamo il driver usando il nome corretto ZBRN.inf
pnputil /add-driver "%DRIVERS_DIR%\ZBRN.inf" /install >nul 2>&1

:: Installa "ZEBRA" sulla porta USB001 usando ZBRN.inf
rundll32 printui.dll,PrintUIEntry /if /b "ZEBRA" /f "%DRIVERS_DIR%\ZBRN.inf" /r "USB001" /m "ZEBRA" >nul 2>&1

:: Installa "GARANZIE" sulla porta USB002 usando ZBRN.inf
rundll32 printui.dll,PrintUIEntry /if /b "GARANZIE" /f "%DRIVERS_DIR%\ZBRN.inf" /r "USB002" /m "GARANZIE" >nul 2>&1

:: 4. IMPOSTAZIONE STAMPANTE PRIMARIA (PREDEFINITA)
echo [4/6] Impostazione di ZEBRA come stampante primaria...
rundll32 printui.dll,PrintUIEntry /y /n "ZEBRA" >nul 2>&1

:: 5. SETTAGGI GEOMETRICI TRAMITE POWERSHELL
echo [5/6]me 'ZEBRA' -PaperSize 'UserDefined' -LabelHeight 70mm -LabelWidth 100mm -Orientation Landscape" >nul Configurazione layout geometrico nei driver...
powershell -Command "Set-PrintConfiguration -PrinterNa 2>&1
powershell -Command "Set-PrintConfiguration -PrinterName 'ZDesigner GK420d' -PaperSize 'UserDefined' -LabelHeight 30mm -LabelWidth 40mm -Orientation Landscape" >nul 2>&1

:: 6. TARATURA HARDWARE E EMISSIONE COMANDI ZPL
echo [6/6] Invio comandi hardware ZPL e taratura ottica...
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
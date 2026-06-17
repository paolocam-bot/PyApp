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
echo     RIPRISTINO INPUT (TASTIERA E MOUSE) - HARDWARE HERO
echo ====================================================
echo.

echo [1/2] Sveglia e scansione delle porte USB...
pnputil /scan-devices >nul 2>&1

echo [2/2] Riavvio dei servizi di input di Windows...
net stop HidServ >nul 2>&1
net start HidServ >nul 2>&1

echo.
echo ====================================================
echo   OPERAZIONE COMPLETATA! Tastiera e mouse ripristinati.
echo ====================================================
timeout /t 3
exit
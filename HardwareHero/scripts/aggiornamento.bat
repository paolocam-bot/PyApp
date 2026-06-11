@echo off
setlocal enabledelayedexpansion

REM Aggiornamento automatico dell'applicazione utilizzando il manifesto GitHub
set "SCRIPT_DIR=%~dp0"
set "APP_DIR=%SCRIPT_DIR%.."
set "APP_EXE=main.exe"
set "ALT_UPDATE_EXE=HardwareHero_update.exe"
set "MANIFEST_FILE=%SCRIPT_DIR%aggiornamento_manifesto.txt"

if not exist "%MANIFEST_FILE%" (
    echo Manifesto aggiornamento non trovato: %MANIFEST_FILE%
    pause
    exit /b 1
)

set "updated=0"
for /f "usebackq delims=" %%A in ("%MANIFEST_FILE%") do (
    set "asset=%%~A"
    if /i "!asset!"=="%APP_EXE%" (
        echo Sostituisco l'eseguibile principale con !asset!...
        tasklist /FI "IMAGENAME eq %APP_EXE%" | find /I "%APP_EXE%" >nul
        if not errorlevel 1 (
            taskkill /F /IM "%APP_EXE%" >nul 2>&1
            timeout /t 2 >nul
        )
        move /Y "%APP_DIR%\!asset!" "%APP_DIR%\%APP_EXE%" >nul 2>&1
        if errorlevel 1 (
            echo Errore durante la sostituzione di %APP_EXE%.
            pause
            exit /b 1
        )
        set "updated=1"
    ) else if /i "!asset!"=="%ALT_UPDATE_EXE%" (
        echo Sostituisco l'eseguibile principale con !asset!...
        tasklist /FI "IMAGENAME eq %APP_EXE%" | find /I "%APP_EXE%" >nul
        if not errorlevel 1 (
            taskkill /F /IM "%APP_EXE%" >nul 2>&1
            timeout /t 2 >nul
        )
        move /Y "%APP_DIR%\!asset!" "%APP_DIR%\%APP_EXE%" >nul 2>&1
        if errorlevel 1 (
            echo Errore durante la sostituzione di %APP_EXE%.
            pause
            exit /b 1
        )
        set "updated=1"
    )
)

if "%updated%"=="0" (
    echo Nessun aggiornamento automatizzato trovato nel manifesto.
    echo Gli asset sono stati scaricati, ma non e' stato identificato un exe di aggiornamento.
    pause
    exit /b 0
)

echo Avvio l'app aggiornata...
start "" "%APP_DIR%\%APP_EXE%"
exit /b 0

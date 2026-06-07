@echo off

::------------------------------------------------------------------------------
::salva le configurazioni e i nomi delle vecchie zebra
wmic printer get name, portname > stampanti_vecchie.txt
::------------------------------------------------------------------------------


:: Rinomina la stampante sulla porta USB001 in ZEBRA
runcall printui.dll,PrintUIEntry /v /n "Nome_Driver_Zebra" /b "ZEBRA"
::------------------------------------------------------------------------------
:: Rinomina la stampante sulla porta USB002 in GARANZIE
runcall printui.dll,PrintUIEntry /v /n "Nome_Driver_Zebra" /b "GARANZIE"

::------------------------------------------------------------------------------
:: Questo comando forza l'esecuzione di PowerShell come Amministratore
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& {
    Write-Host 'Rimozione vecchia Zebra...' -ForegroundColor Cyan;
    Remove-Printer -Name 'Zebra ZD420' -ErrorAction SilentlyContinue;
    
    Write-Host 'Installazione nuovo driver Zebra...' -ForegroundColor Cyan;
    Start-Process -FilePath 'C:\Percorso\zd86423827-certified.exe' -ArgumentList '/s /v\"/qn\"' -Wait;
    
    Write-Host 'Operazione Completata!' -ForegroundColor Green;
    pause
}"

::------------------------------------------------------------------------------
:: ---RESET E TARATURA PER STAMPANTE ZEBRA ---
:: ~JA (Cancella coda) | ~JR (Reset) | ^XA^JUS^XZ (Salva e taratura hardware)
echo ~JA > "\\localhost\ZEBRA"
echo ~JR > "\\localhost\ZEBRA"
echo ^XA^JUS^XZ > "\\localhost\ZEBRA"

:: --- RESET E TARATURA PER STAMPANTE GARANZIE ---
echo ~JA > "\\localhost\GARANZIE"
echo ~JR > "\\localhost\GARANZIE"
echo ^XA^JUS^XZ > "\\localhost\GARANZIE"
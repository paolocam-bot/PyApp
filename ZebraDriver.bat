@echo off
:: Questo comando forza l'esecuzione di PowerShell come Amministratore
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& {
    Write-Host 'Rimozione vecchia Zebra...' -ForegroundColor Cyan;
    Remove-Printer -Name 'Zebra ZD420' -ErrorAction SilentlyContinue;
    
    Write-Host 'Installazione nuovo driver Zebra...' -ForegroundColor Cyan;
    Start-Process -FilePath 'C:\Percorso\zd86423827-certified.exe' -ArgumentList '/s /v\"/qn\"' -Wait;
    
    Write-Host 'Operazione Completata!' -ForegroundColor Green;
    pause
}"
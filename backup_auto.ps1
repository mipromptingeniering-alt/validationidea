param(
    [string]$Mensaje = "backup automático"
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
cd C:\Users\juanj\Documents\validationidea

$fecha = Get-Date -Format "yyyy-MM-dd"

# Asegurar carpeta de backups
New-Item -ItemType Directory -Force -Path ../backups | Out-Null

# Commit ligero (solo lo importante)
git add data/ideas.json system_documentation.json
git commit -m "backup: $Mensaje $fecha" 2>$null

git pull origin main
git push origin main

# Crear ZIP del estado actual (HEAD)
$zipPath = "../backups/validationidea_$fecha.zip"
git archive --format=zip --output=$zipPath HEAD

Write-Host "✅ Backup automático completado: $zipPath" -ForegroundColor Green

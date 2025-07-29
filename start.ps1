#!/usr/bin/env pwsh
# Script PowerShell pour démarrer PadelVar
Write-Host "🎯 PadelVar - Script de démarrage" -ForegroundColor Green
Write-Host "=" * 50

# Aller dans le répertoire backend
Set-Location "c:\Users\PC\Desktop\padelvar_localV4\padelvar-backend"

Write-Host "📂 Répertoire actuel: $PWD" -ForegroundColor Yellow

# Vérifier Python
Write-Host "🐍 Vérification de Python..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   ✅ Python trouvé: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Python non trouvé" -ForegroundColor Red
    exit 1
}

# Démarrer le serveur Flask
Write-Host "🚀 Démarrage du serveur Flask..." -ForegroundColor Cyan
Write-Host "   Serveur disponible sur: http://localhost:5000" -ForegroundColor Yellow
Write-Host "   Utilisateur test: player@test.com / password123" -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 Pour arrêter: Ctrl+C" -ForegroundColor Magenta
Write-Host ""

try {
    python quick_test.py
} catch {
    Write-Host "❌ Erreur lors du démarrage: $($_.Exception.Message)" -ForegroundColor Red
}

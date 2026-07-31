#!/bin/bash
# Script para subir APanel a GitHub después de crear el repositorio manualmente

echo "========================================"
echo "🚀 Subiendo APanel a GitHub"
echo "========================================"
echo ""

# Configurar Git
cd ~/hermes-backup/apanel-repo
git remote add origin https://github.com/GerardoSandovalcabrera/apanel.git
git branch -M main

# Subir a GitHub
echo "📤 Subiendo código a GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ¡Código subido exitosamente!"
    echo ""
    echo "🔗 Repositorio: https://github.com/GerardoSandovalcabrera/apanel"
    echo ""
    echo "📋 Próximos pasos:"
    echo "1. Ve al repositorio en GitHub"
    echo "2. Configura OAuth Apps (GitHub + Google)"
    echo "3. Actualiza variables de entorno"
    echo "4. Inicia el sistema"
    echo ""
else
    echo ""
    echo "❌ Error al subir a GitHub"
    echo "Asegúrate de haber creado el repositorio 'apanel' en GitHub"
    echo ""
fi

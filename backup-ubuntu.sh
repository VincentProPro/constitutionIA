#!/bin/bash

# Script de sauvegarde pour ConstitutionIA sur Ubuntu

BACKUP_DIR="/opt/constitutionia/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="constitutionia_backup_$DATE"

echo "🔄 Création de la sauvegarde: $BACKUP_NAME"

# Créer le dossier de sauvegarde
mkdir -p "$BACKUP_DIR"

# Sauvegarder la base de données
echo "📊 Sauvegarde de la base de données..."
docker cp constitutionia-optimize_backend_1:/app/constitutionia.db "$BACKUP_DIR/${BACKUP_NAME}_db.sqlite"

# Sauvegarder les fichiers PDF
echo "📄 Sauvegarde des fichiers PDF..."
docker cp constitutionia-optimize_backend_1:/app/Fichier "$BACKUP_DIR/${BACKUP_NAME}_pdfs/"

# Sauvegarder les logs
echo "📝 Sauvegarde des logs..."
if [ -d "logs" ]; then
    cp -r logs "$BACKUP_DIR/${BACKUP_NAME}_logs/"
fi

# Créer une archive
echo "📦 Création de l'archive..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" \
    "${BACKUP_NAME}_db.sqlite" \
    "${BACKUP_NAME}_pdfs" \
    "${BACKUP_NAME}_logs"

# Nettoyer les fichiers temporaires
rm -rf "${BACKUP_NAME}_db.sqlite" "${BACKUP_NAME}_pdfs" "${BACKUP_NAME}_logs"

echo "✅ Sauvegarde terminée: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"

# Supprimer les anciennes sauvegardes (garder les 7 derniers jours)
find "$BACKUP_DIR" -name "constitutionia_backup_*.tar.gz" -mtime +7 -delete

echo "🧹 Nettoyage des anciennes sauvegardes terminé" 
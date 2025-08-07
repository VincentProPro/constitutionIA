# 📁 Fichiers de déploiement Ubuntu - ConstitutionIA

## 🚀 Fichiers principaux

### 1. `docker-compose-ubuntu.yml`
- Configuration Docker Compose optimisée pour Ubuntu
- Services: backend, frontend, nginx
- Réseau dédié pour la sécurité

### 2. `nginx-ubuntu.conf`
- Configuration Nginx optimisée pour Ubuntu
- Compression gzip
- Headers de sécurité
- Proxy vers l'API backend
- Support React Router

### 3. `nginx/Dockerfile`
- Container Nginx pour Ubuntu
- Health checks
- Configuration optimisée

### 4. `env.example`
- Variables d'environnement d'exemple
- Configuration OpenAI, base de données, logs
- Sécurité et monitoring

## 🔧 Fichiers de configuration

### 5. `constitutionia.service`
- Service systemd pour Ubuntu
- Démarrage automatique
- Gestion des dépendances Docker

### 6. `ufw-rules.txt`
- Règles firewall Ubuntu
- Ports: SSH (22), HTTP (80), HTTPS (443), API (8000)
- Configuration de sécurité

## 💾 Fichiers de sauvegarde

### 7. `backup-ubuntu.sh`
- Script de sauvegarde automatique
- Base de données SQLite
- Fichiers PDF
- Logs d'application
- Rotation des sauvegardes (7 jours)

### 8. `cron-jobs.txt`
- Tâches cron pour Ubuntu
- Sauvegarde quotidienne
- Nettoyage des logs
- Monitoring automatique
- Redémarrage en cas de problème

## 📋 Instructions d'utilisation

### Installation
```bash
# Copier les fichiers sur le serveur Ubuntu
scp -r . user@server:/opt/constitutionia/

# Configurer les variables d'environnement
cp env.example .env
nano .env

# Démarrer les services
docker-compose -f docker-compose-ubuntu.yml up -d
```

### Configuration systemd
```bash
# Installer le service
sudo cp constitutionia.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable constitutionia
sudo systemctl start constitutionia
```

### Configuration firewall
```bash
# Appliquer les règles UFW
sudo bash ufw-rules.txt
```

### Configuration cron
```bash
# Ajouter les tâches cron
crontab -e
# Copier le contenu de cron-jobs.txt
```

### Sauvegarde manuelle
```bash
# Exécuter la sauvegarde
chmod +x backup-ubuntu.sh
./backup-ubuntu.sh
```

## 🔍 Monitoring

### Vérifier les services
```bash
# Statut Docker
docker-compose -f docker-compose-ubuntu.yml ps

# Logs
docker-compose -f docker-compose-ubuntu.yml logs -f

# Statut systemd
sudo systemctl status constitutionia
```

### URLs d'accès
- **Frontend**: http://votre-ip-serveur
- **API**: http://votre-ip-serveur:8000
- **Documentation**: http://votre-ip-serveur:8000/docs
- **Health check**: http://votre-ip-serveur/health

## 🛠️ Maintenance

### Mise à jour
```bash
# Arrêter les services
docker-compose -f docker-compose-ubuntu.yml down

# Mettre à jour le code
git pull

# Reconstruire et redémarrer
docker-compose -f docker-compose-ubuntu.yml up -d --build
```

### Restauration
```bash
# Restaurer une sauvegarde
tar -xzf backup_file.tar.gz
docker cp backup_db.sqlite constitutionia-optimize_backend_1:/app/constitutionia.db
docker-compose -f docker-compose-ubuntu.yml restart backend
```

## 📊 Logs et debugging

### Emplacement des logs
- **Nginx**: `/var/log/nginx/`
- **Application**: `./logs/`
- **Docker**: `docker-compose logs`

### Commandes utiles
```bash
# Voir les logs en temps réel
docker-compose -f docker-compose-ubuntu.yml logs -f

# Vérifier l'espace disque
df -h

# Vérifier la mémoire
free -h

# Vérifier les processus
ps aux | grep docker
``` 
# Guide de Déploiement - ConstitutionIA

## Prérequis

1. **Docker** installé sur votre serveur
2. **Docker Compose** installé
3. **Clé API OpenAI** valide

## Déploiement Rapide

### 1. Configuration de l'environnement

```bash
# Définir votre clé API OpenAI
export OPENAI_API_KEY="votre_clé_api_openai"

# Vérifier que la clé est définie
echo $OPENAI_API_KEY
```

### 2. Déploiement automatique

```bash
# Exécuter le script de déploiement
./deploy.sh
```

### 3. Déploiement manuel

```bash
# Construire et démarrer les services
docker-compose up -d --build

# Vérifier le statut
docker-compose ps

# Voir les logs
docker-compose logs -f
```

## Déploiement sur Serveur de Production

### 1. Préparation du serveur

```bash
# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Installer Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Configuration SSL (Optionnel)

```bash
# Créer le dossier SSL
mkdir ssl

# Générer un certificat auto-signé (pour test)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ssl/nginx.key -out ssl/nginx.crt
```

### 3. Configuration du domaine

Modifiez `frontend/nginx.conf` pour votre domaine :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;
    # ... reste de la configuration
}
```

### 4. Variables d'environnement

Créez un fichier `.env` :

```env
OPENAI_API_KEY=votre_clé_api_openai
DATABASE_URL=sqlite:///./constitutionia.db
HOST=0.0.0.0
PORT=8000
ENABLE_MONITORING=true
```

## Monitoring et Maintenance

### Vérifier les logs

```bash
# Logs du backend
docker-compose logs backend

# Logs du frontend
docker-compose logs frontend

# Logs en temps réel
docker-compose logs -f
```

### Mise à jour

```bash
# Arrêter les services
docker-compose down

# Reconstruire et redémarrer
docker-compose up -d --build
```

### Sauvegarde

```bash
# Sauvegarder la base de données
docker cp constitutionia-optimize_backend_1:/app/constitutionia.db ./backup/

# Sauvegarder les fichiers PDF
docker cp constitutionia-optimize_backend_1:/app/Fichier ./backup/
```

## Dépannage

### Problèmes courants

1. **Port déjà utilisé** :
   ```bash
   sudo lsof -ti:8000 | xargs kill -9
   ```

2. **Erreur de permissions** :
   ```bash
   sudo chown -R $USER:$USER .
   ```

3. **Problème de mémoire** :
   ```bash
   # Augmenter la mémoire Docker
   docker system prune -a
   ```

### Vérification de l'état

```bash
# Statut des conteneurs
docker-compose ps

# Utilisation des ressources
docker stats

# Test de l'API
curl http://localhost:8000/docs
```

## URLs d'accès

- **Frontend** : http://votre-domaine.com
- **Backend API** : http://votre-domaine.com:8000
- **Documentation API** : http://votre-domaine.com:8000/docs
- **Interface d'administration** : http://votre-domaine.com:8000/admin

## Support

Pour toute question ou problème :
1. Vérifiez les logs : `docker-compose logs`
2. Consultez la documentation API : `/docs`
3. Vérifiez la configuration : `docker-compose config` 
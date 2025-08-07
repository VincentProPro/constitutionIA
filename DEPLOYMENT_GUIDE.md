# 🚀 Guide de déploiement ConstitutionIA sur Ubuntu

## 📋 Prérequis

### Sur votre machine locale :
- ✅ Fichier `.env` configuré avec votre `OPENAI_API_KEY`
- ✅ Clé SSH pour accéder au serveur
- ✅ Tous les fichiers de déploiement créés

### Sur le serveur Ubuntu :
- ✅ Accès SSH
- ✅ Droits sudo
- ✅ Connexion internet

## 🔧 Étapes de déploiement

### 1. Test de connexion
```bash
# Tester la connexion SSH
./test-connection.sh IP_SERVEUR UTILISATEUR CHEMIN_CLE

# Exemple :
./test-connection.sh 192.168.1.100 ubuntu ~/.ssh/id_rsa
```

### 2. Déploiement automatique
```bash
# Déployer l'application
./deploy-to-server.sh IP_SERVEUR UTILISATEUR CHEMIN_CLE

# Exemple :
./deploy-to-server.sh 192.168.1.100 ubuntu ~/.ssh/id_rsa
```

## 📝 Configuration du fichier .env

Avant le déploiement, configurez votre fichier `.env` :

```bash
# Copier le fichier d'exemple
cp env.example .env

# Éditer le fichier
nano .env
```

**Variables importantes à configurer :**
```env
# Votre clé API OpenAI (OBLIGATOIRE)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Configuration serveur
HOST=0.0.0.0
PORT=8000

# Base de données
DATABASE_URL=sqlite:///./constitutionia.db

# Monitoring
ENABLE_MONITORING=true
```

## 🌐 URLs d'accès

Après le déploiement, votre application sera accessible sur :

- **Frontend** : `http://VOTRE_IP_SERVEUR`
- **API** : `http://VOTRE_IP_SERVEUR:8000`
- **Documentation API** : `http://VOTRE_IP_SERVEUR:8000/docs`
- **Health Check** : `http://VOTRE_IP_SERVEUR/health`

## 🛠️ Commandes de maintenance

### Voir les logs
```bash
ssh -i CHEMIN_CLE UTILISATEUR@IP_SERVEUR 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml logs -f'
```

### Redémarrer l'application
```bash
ssh -i CHEMIN_CLE UTILISATEUR@IP_SERVEUR 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml restart'
```

### Sauvegarde manuelle
```bash
ssh -i CHEMIN_CLE UTILISATEUR@IP_SERVEUR 'cd /opt/constitutionia && ./backup-ubuntu.sh'
```

### Mise à jour
```bash
ssh -i CHEMIN_CLE UTILISATEUR@IP_SERVEUR 'cd /opt/constitutionia && git pull && docker-compose -f docker-compose-ubuntu.yml up -d --build'
```

## 🔍 Monitoring

### Vérifier le statut des services
```bash
ssh -i CHEMIN_CLE UTILISATEUR@IP_SERVEUR 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml ps'
```

### Vérifier les ressources
```bash
ssh -i CHEMIN_CLE UTILISATEUR@IP_SERVEUR 'df -h && free -h && docker system df'
```

## 🚨 Dépannage

### Problème de connexion SSH
- Vérifiez l'IP du serveur
- Vérifiez le nom d'utilisateur
- Vérifiez la clé SSH
- Testez avec : `ssh -i CHEMIN_CLE UTILISATEUR@IP_SERVEUR`

### Problème de déploiement
- Vérifiez que le fichier `.env` est configuré
- Vérifiez la connexion internet du serveur
- Consultez les logs : `docker-compose -f docker-compose-ubuntu.yml logs`

### Problème d'accès à l'application
- Vérifiez le firewall : `sudo ufw status`
- Vérifiez les conteneurs : `docker ps`
- Testez localement sur le serveur : `curl http://localhost/health`

## 📊 Sauvegarde automatique

Le système configure automatiquement :
- ✅ Sauvegarde quotidienne à 2h du matin
- ✅ Nettoyage des logs hebdomadaires
- ✅ Redémarrage automatique en cas de problème
- ✅ Monitoring des conteneurs

## 🔒 Sécurité

Le déploiement configure automatiquement :
- ✅ Firewall UFW avec règles restrictives
- ✅ Headers de sécurité dans Nginx
- ✅ Service systemd pour démarrage automatique
- ✅ Isolation des conteneurs Docker

## 📞 Support

En cas de problème :
1. Consultez les logs : `docker-compose logs`
2. Vérifiez le statut : `docker-compose ps`
3. Testez la connectivité : `curl http://localhost/health`
4. Redémarrez si nécessaire : `docker-compose restart` 
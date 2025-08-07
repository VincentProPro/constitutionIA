# 🚀 Déploiement Rapide ConstitutionIA

## 📋 Prérequis

✅ **Vous avez :**
- IP du serveur Ubuntu
- Nom d'utilisateur du serveur  
- Clé privée SSH
- Clé API OpenAI

## 🔧 Étapes de déploiement

### 1. Configuration de l'environnement
```bash
# Configurer votre clé API OpenAI
./setup-env.sh
```

### 2. Déploiement automatique
```bash
# Déployer sur votre serveur
./deploy-simple.sh IP_SERVEUR UTILISATEUR CHEMIN_CLE_PRIVEE

# Exemple :
./deploy-simple.sh 192.168.1.100 ubuntu ~/.ssh/id_rsa
```

## 📝 Configuration du fichier .env

Le script `setup-env.sh` va :
1. Créer le fichier `.env` à partir de `env.example`
2. Ouvrir l'éditeur pour que vous ajoutiez votre clé API
3. Vérifier que la configuration est correcte

**Variables à configurer :**
```env
# Votre clé API OpenAI (OBLIGATOIRE)
OPENAI_API_KEY=sk-your-actual-api-key-here

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
- **Documentation** : `http://VOTRE_IP_SERVEUR:8000/docs`
- **Health Check** : `http://VOTRE_IP_SERVEUR/health`

## 🛠️ Commandes de maintenance

### Voir les logs
```bash
ssh -i CHEMIN_CLE_PRIVEE UTILISATEUR@IP_SERVEUR 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml logs -f'
```

### Redémarrer l'application
```bash
ssh -i CHEMIN_CLE_PRIVEE UTILISATEUR@IP_SERVEUR 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml restart'
```

### Sauvegarde manuelle
```bash
ssh -i CHEMIN_CLE_PRIVEE UTILISATEUR@IP_SERVEUR 'cd /opt/constitutionia && ./backup-ubuntu.sh'
```

### Vérifier le statut
```bash
ssh -i CHEMIN_CLE_PRIVEE UTILISATEUR@IP_SERVEUR 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml ps'
```

## 🚨 Dépannage

### Problème de connexion SSH
```bash
# Tester la connexion manuellement
ssh -i CHEMIN_CLE_PRIVEE UTILISATEUR@IP_SERVEUR

# Vérifier les permissions de la clé
chmod 600 CHEMIN_CLE_PRIVEE
```

### Problème de déploiement
```bash
# Vérifier les logs sur le serveur
ssh -i CHEMIN_CLE_PRIVEE UTILISATEUR@IP_SERVEUR 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml logs'

# Redémarrer les services
ssh -i CHEMIN_CLE_PRIVEE UTILISATEUR@IP_SERVEUR 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml down && docker-compose -f docker-compose-ubuntu.yml up -d'
```

### Problème d'accès à l'application
```bash
# Vérifier le firewall
ssh -i CHEMIN_CLE_PRIVEE UTILISATEUR@IP_SERVEUR 'sudo ufw status'

# Vérifier les conteneurs
ssh -i CHEMIN_CLE_PRIVEE UTILISATEUR@IP_SERVEUR 'docker ps'

# Test local sur le serveur
ssh -i CHEMIN_CLE_PRIVEE UTILISATEUR@IP_SERVEUR 'curl http://localhost/health'
```

## 🔒 Sécurité

Le déploiement configure automatiquement :
- ✅ Firewall UFW avec règles restrictives
- ✅ Headers de sécurité dans Nginx
- ✅ Service systemd pour démarrage automatique
- ✅ Isolation des conteneurs Docker

## 📊 Fonctionnalités automatiques

- ✅ Sauvegarde quotidienne à 2h du matin
- ✅ Nettoyage des logs hebdomadaires
- ✅ Redémarrage automatique en cas de problème
- ✅ Monitoring des conteneurs

## 🎯 Exemple complet

```bash
# 1. Configurer l'environnement
./setup-env.sh

# 2. Déployer (remplacez par vos vraies informations)
./deploy-simple.sh 192.168.1.100 ubuntu ~/.ssh/id_rsa

# 3. Vérifier l'accès
curl http://192.168.1.100/health
```

**Votre application sera accessible sur `http://VOTRE_IP_SERVEUR` !** 🚀 
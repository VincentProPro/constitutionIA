# 🚀 Déploiement ConstitutionIA - Version Simple

## 📋 Prérequis
- IP du serveur Ubuntu
- Nom d'utilisateur du serveur
- Clé privée SSH
- Clé API OpenAI

## 🔧 Configuration rapide

### 1. Configurer votre clé API OpenAI
```bash
# Éditer le fichier .env
nano .env

# Ajouter votre clé API :
OPENAI_API_KEY=sk-votre-cle-api-ici
```

### 2. Déployer en une commande
```bash
./deploy.sh IP UTILISATEUR CLE_SSH

# Exemple :
./deploy.sh 192.168.1.100 ubuntu ~/.ssh/id_rsa
```

## 🌐 Accès
- **Site web** : `http://VOTRE_IP`
- **API** : `http://VOTRE_IP:8000/docs`

## 🛠️ Commandes utiles

### Voir les logs
```bash
ssh -i CLE_SSH UTILISATEUR@IP 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml logs -f'
```

### Redémarrer
```bash
ssh -i CLE_SSH UTILISATEUR@IP 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml restart'
```

### Statut
```bash
ssh -i CLE_SSH UTILISATEUR@IP 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml ps'
```

## 🎯 Exemple complet
```bash
# 1. Configurer .env avec votre clé OpenAI
nano .env

# 2. Déployer
./deploy.sh 192.168.1.100 ubuntu ~/.ssh/id_rsa

# 3. Accéder
open http://192.168.1.100
```

**C'est tout !** 🎉 
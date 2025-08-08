# 🚀 Déploiement ConstitutionIA via Git

## 📋 Méthodes disponibles

### 🎯 **Méthode 1 : Script simple (Recommandée)**
```bash
# Configuration initiale
./git-deploy.sh IP UTILISATEUR CLE_SSH

# Exemple :
./git-deploy.sh 192.168.1.100 ubuntu ~/.ssh/id_rsa
```

### 🔄 **Méthode 2 : Déploiement automatique**
```bash
# Configuration avec hooks Git
./deploy-git.sh IP UTILISATEUR CLE_SSH

# Utilisation :
git deploy  # Push + déploy automatique
```

### 🤖 **Méthode 3 : GitHub Actions**
1. Configurer les secrets GitHub
2. Push automatique sur main

## 🚀 Méthode Simple (Recommandée)

### 1. Configuration initiale
```bash
./git-deploy.sh 192.168.1.100 ubuntu ~/.ssh/id_rsa
```

### 2. Déploiement manuel
```bash
# Déployer les dernières modifications
ssh -i ~/.ssh/id_rsa ubuntu@192.168.1.100 'cd /opt/constitutionia && ./deploy.sh'
```

### 3. Workflow quotidien
```bash
# 1. Modifier le code
nano frontend/src/components/Header.tsx

# 2. Commiter
git add .
git commit -m "Amélioration du header"

# 3. Pousser sur GitHub
git push origin main

# 4. Déployer sur le serveur
ssh -i ~/.ssh/id_rsa ubuntu@192.168.1.100 'cd /opt/constitutionia && ./deploy.sh'
```

## 🔄 Méthode Automatique

### 1. Configuration
```bash
./deploy-git.sh 192.168.1.100 ubuntu ~/.ssh/id_rsa
```

### 2. Utilisation
```bash
# Déployer automatiquement
git deploy

# Ou manuellement
git push origin main && ssh -i ~/.ssh/id_rsa ubuntu@192.168.1.100 'cd /opt/constitutionia && ./deploy-auto.sh'
```

## 🤖 Méthode GitHub Actions

### 1. Configurer les secrets GitHub
Allez dans votre repository GitHub → Settings → Secrets and variables → Actions

Ajoutez ces secrets :
- `HOST` : IP de votre serveur
- `USERNAME` : nom d'utilisateur du serveur
- `SSH_KEY` : votre clé privée SSH

### 2. Utilisation
```bash
# Push automatique = déploiement automatique
git push origin main
```

## 📋 Commandes utiles

### Voir les logs
```bash
ssh -i ~/.ssh/id_rsa ubuntu@192.168.1.100 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml logs -f'
```

### Vérifier le statut
```bash
ssh -i ~/.ssh/id_rsa ubuntu@192.168.1.100 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml ps'
```

### Redémarrer
```bash
ssh -i ~/.ssh/id_rsa ubuntu@192.168.1.100 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml restart'
```

### Sauvegarde
```bash
ssh -i ~/.ssh/id_rsa ubuntu@192.168.1.100 'cd /opt/constitutionia && ./backup-ubuntu.sh'
```

## 🎯 Workflow recommandé

### 1. Développement local
```bash
# Modifier le code
nano frontend/src/components/Header.tsx

# Tester localement
cd backend && source rag_env/bin/activate && python -m uvicorn app.main:app --reload
cd frontend && npm start
```

### 2. Commit et push
```bash
git add .
git commit -m "Amélioration du header"
git push origin main
```

### 3. Déploiement
```bash
# Méthode simple
ssh -i ~/.ssh/id_rsa ubuntu@192.168.1.100 'cd /opt/constitutionia && ./deploy.sh'

# Ou méthode automatique
git deploy
```

## 🔧 Configuration du serveur

Le script configure automatiquement :
- ✅ Installation de Git, Docker, Docker Compose
- ✅ Clonage du repository
- ✅ Script de déploiement automatique
- ✅ Service systemd pour redémarrage automatique

## 📊 Monitoring

### Vérifier les services
```bash
ssh -i ~/.ssh/id_rsa ubuntu@192.168.1.100 'systemctl status constitutionia-deploy'
```

### Vérifier les logs
```bash
ssh -i ~/.ssh/id_rsa ubuntu@192.168.1.100 'journalctl -u constitutionia-deploy -f'
```

## 🚨 Dépannage

### Problème de connexion SSH
```bash
# Tester la connexion
ssh -i ~/.ssh/id_rsa ubuntu@192.168.1.100

# Vérifier les permissions
chmod 600 ~/.ssh/id_rsa
```

### Problème de déploiement
```bash
# Vérifier les logs Docker
ssh -i ~/.ssh/id_rsa ubuntu@192.168.1.100 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml logs'

# Redémarrer manuellement
ssh -i ~/.ssh/id_rsa ubuntu@192.168.1.100 'cd /opt/constitutionia && docker-compose -f docker-compose-ubuntu.yml down && docker-compose -f docker-compose-ubuntu.yml up -d'
```

## 🎯 Exemple complet

```bash
# 1. Configuration initiale
./git-deploy.sh 192.168.1.100 ubuntu ~/.ssh/id_rsa

# 2. Modifier le code
nano frontend/src/components/Header.tsx

# 3. Commit et push
git add .
git commit -m "Amélioration du header"
git push origin main

# 4. Déployer
ssh -i ~/.ssh/id_rsa ubuntu@192.168.1.100 'cd /opt/constitutionia && ./deploy.sh'

# 5. Vérifier
curl http://192.168.1.100/health
```

**C'est tout ! Votre déploiement Git est configuré !** 🚀 
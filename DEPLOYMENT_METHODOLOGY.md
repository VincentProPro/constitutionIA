# 🚀 Méthodologie de Déploiement - ConstitutionIA

## 📋 **Vue d'ensemble**

Ce document décrit la méthodologie standardisée pour déployer ConstitutionIA sur le serveur de production (98.85.253.114).

---

## 🎯 **Configuration du Serveur**

### **Informations de Connexion**
- **IP** : 98.85.253.114
- **Utilisateur** : ubuntu
- **Clé SSH** : /Users/vincentps/Downloads/key/aiconstitution.pem
- **Répertoire** : /opt/constitutionia

### **Architecture du Serveur**
- **Backend** : Python avec uvicorn (nohup)
- **Frontend** : React buildé, servi par Nginx
- **Base de données** : SQLite (constitutionia.db)
- **Proxy** : Nginx (systemd)

---

## 🔄 **Processus de Déploiement**

### **Étape 1 : Préparation Locale**
```bash
# 1. Vérifier les changements
git status
git add .
git commit -m "Description des changements"
git push origin main
```

### **Étape 2 : Déploiement Automatique**
```bash
# Utiliser le script de déploiement personnalisé
./deploy-update-custom.sh 98.85.253.114 ubuntu /Users/vincentps/Downloads/key/aiconstitution.pem
```

### **Étape 3 : Vérification Post-Déploiement**
```bash
# Vérifier les services
ssh -i /Users/vincentps/Downloads/key/aiconstitution.pem ubuntu@98.85.253.114 'ps aux | grep uvicorn'
ssh -i /Users/vincentps/Downloads/key/aiconstitution.pem ubuntu@98.85.253.114 'sudo systemctl status nginx'

# Tester l'application
curl http://98.85.253.114/health
```

---

## 📁 **Structure des Services**

### **Backend (Python)**
- **Processus** : `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Logs** : `/opt/constitutionia/backend/backend.log`
- **Environnement** : venv dans `/opt/constitutionia/backend/`
- **Redémarrage** : `pkill -f uvicorn` puis relancer avec nohup

### **Frontend (React)**
- **Build** : `npm run build` dans `/opt/constitutionia/frontend/`
- **Déploiement** : Copie vers `/var/www/html/`
- **Serveur** : Nginx
- **Redémarrage** : `sudo systemctl restart nginx`

### **Nginx**
- **Configuration** : `/etc/nginx/sites-available/default`
- **Document root** : `/var/www/html/`
- **Redémarrage** : `sudo systemctl restart nginx`

---

## 🛠️ **Scripts de Déploiement**

### **Script Principal : deploy-update-custom.sh**
```bash
#!/bin/bash
# Déploiement rapide des mises à jour (configuration personnalisée)
# Usage: ./deploy-update-custom.sh IP_SERVEUR UTILISATEUR CHEMIN_CLE_SSH

# Actions effectuées :
# 1. Test de connexion SSH
# 2. Git pull des dernières modifications
# 3. npm install pour les dépendances frontend
# 4. Redémarrage du backend (kill + nohup)
# 5. Redémarrage de Nginx
```

### **Commandes de Vérification**
```bash
# Vérifier les processus
ps aux | grep uvicorn
sudo systemctl status nginx

# Vérifier les logs
tail -f /opt/constitutionia/backend/backend.log
sudo journalctl -u nginx -f

# Tester les endpoints
curl http://98.85.253.114/health
curl http://98.85.253.114:8000/health
```

---

## ⚠️ **Points d'Attention**

### **Espace Disque**
- **Surveillance** : `df -h` avant déploiement
- **Nettoyage** : `sudo apt clean && sudo apt autoremove`
- **Cache npm** : `npm cache clean --force` si nécessaire

### **Conflits Git**
- **Stash automatique** : Le script utilise `git stash` avant pull
- **Résolution manuelle** : Si conflits, se connecter en SSH et résoudre

### **Services Non-Standard**
- **Pas de systemd** pour le backend (utilise nohup)
- **Pas de PM2** pour Node.js (build statique)
- **Configuration Nginx** personnalisée

---

## 🔧 **Dépannage**

### **Backend ne démarre pas**
```bash
# Vérifier l'environnement virtuel
cd /opt/constitutionia/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Vérifier les logs
tail -f backend.log
```

### **Frontend non mis à jour**
```bash
# Reconstruire le frontend
cd /opt/constitutionia/frontend
npm run build
sudo cp -r build/* /var/www/html/
sudo systemctl restart nginx
```

### **Nginx ne fonctionne pas**
```bash
# Vérifier la configuration
sudo nginx -t
sudo systemctl status nginx
sudo journalctl -u nginx -f
```

---

## 📊 **Monitoring Post-Déploiement**

### **Vérifications Automatiques**
```bash
# Script de vérification
ssh -i /Users/vincentps/Downloads/key/aiconstitution.pem ubuntu@98.85.253.114 << 'EOF'
echo "=== Backend Status ==="
ps aux | grep uvicorn | grep -v grep
echo "=== Nginx Status ==="
sudo systemctl status nginx --no-pager
echo "=== Disk Usage ==="
df -h
echo "=== Memory Usage ==="
free -h
EOF
```

### **Tests Fonctionnels**
```bash
# Test de l'application
curl -s http://98.85.253.114 | grep -o "main\.[a-zA-Z0-9]*\.js"
curl -s http://98.85.253.114:8000/health
```

---

## 🚀 **Workflow Complet**

### **1. Développement Local**
```bash
# Modifier le code
# Tester en local (http://localhost:3000 et http://localhost:8000)
# Commiter les changements
git add .
git commit -m "Description des changements"
git push origin main
```

### **2. Déploiement**
```bash
# Déployer automatiquement
./deploy-update-custom.sh 98.85.253.114 ubuntu /Users/vincentps/Downloads/key/aiconstitution.pem
```

### **3. Vérification**
```bash
# Vérifier les services
ssh -i /Users/vincentps/Downloads/key/aiconstitution.pem ubuntu@98.85.253.114 'ps aux | grep uvicorn'
ssh -i /Users/vincentps/Downloads/key/aiconstitution.pem ubuntu@98.85.253.114 'sudo systemctl status nginx'

# Tester l'application
open http://98.85.253.114
```

---

## 📝 **Notes Importantes**

### **Sécurité**
- Clé SSH stockée localement
- Pas de mots de passe en dur
- Accès SSH uniquement

### **Performance**
- Build de production pour le frontend
- Cache Nginx activé
- Logs rotation automatique

### **Backup**
- Base de données : `/opt/constitutionia/backend/constitutionia.db`
- Configuration : `/etc/nginx/sites-available/default`
- Code source : Git repository

---

## 🎯 **Commandes Rapides**

```bash
# Déploiement complet
./deploy-update-custom.sh 98.85.253.114 ubuntu /Users/vincentps/Downloads/key/aiconstitution.pem

# Vérification rapide
ssh -i /Users/vincentps/Downloads/key/aiconstitution.pem ubuntu@98.85.253.114 'ps aux | grep uvicorn && sudo systemctl status nginx'

# Logs en temps réel
ssh -i /Users/vincentps/Downloads/key/aiconstitution.pem ubuntu@98.85.253.114 'tail -f /opt/constitutionia/backend/backend.log'

# Redémarrage d'urgence
ssh -i /Users/vincentps/Downloads/key/aiconstitution.pem ubuntu@98.85.253.114 'cd /opt/constitutionia/backend && pkill -f uvicorn && source venv/bin/activate && nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 & && sudo systemctl restart nginx'
```

---

**Dernière mise à jour** : 8 août 2025  
**Version** : 1.0  
**Auteur** : Équipe ConstitutionIA 
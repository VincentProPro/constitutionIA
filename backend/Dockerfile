FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements_production.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements_production.txt

# Copier le code de l'application
COPY . .

# Créer le dossier pour les fichiers PDF
RUN mkdir -p Fichier

# Exposer le port
EXPOSE 8000

# Commande pour démarrer l'application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 
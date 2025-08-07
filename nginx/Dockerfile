FROM nginx:alpine

# Copier la configuration nginx
COPY nginx-ubuntu.conf /etc/nginx/nginx.conf

# Créer les dossiers de logs
RUN mkdir -p /var/log/nginx

# Exposer le port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

# Démarrer nginx
CMD ["nginx", "-g", "daemon off;"] 
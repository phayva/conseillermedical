#!/bin/bash
echo "Démarrage de l'application avec Gunicorn..."
sleep 20  # Attendre 10 secondes pour s'assurer que tout est prêt
exec gunicorn main:app --bind 0.0.0.0:8000 --log-level info --timeout 120

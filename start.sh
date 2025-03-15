#!/bin/bash
echo "Démarrage de l'application avec Gunicorn..."
sleep 10  # Attendre 10 secondes pour s'assurer que tout est prêt
gunicorn main:app --bind 0.0.0.0:8000 --log-level info --timeout 120

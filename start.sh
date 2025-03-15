#!/bin/bash
echo "Démarrage de l'application avec Gunicorn..."
sleep 20  # Délai augmenté pour donner le temps au bot de démarrer
exec gunicorn main:app --bind 0.0.0.0:8000 --log-level info --timeout 120 --workers 2

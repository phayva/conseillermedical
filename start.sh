#!/bin/bash
echo "Démarrage de l'application avec Gunicorn..."
sleep 10  # Délai suffisant pour l'initialisation
exec gunicorn main:app --bind 0.0.0.0:8000 --log-level info --timeout 120 --workers 2

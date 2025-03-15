#!/bin/bash
echo "Démarrage de l'application avec Gunicorn..."
sleep 10  # Attendre 5 secondes pour laisser le bot et Flask s'initialiser
gunicorn main:app --bind 0.0.0.0:8000 --log-level info

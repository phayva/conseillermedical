#!/bin/bash
echo "Démarrage de l'application avec Gunicorn..."
sleep 10  # Réduit à 10 secondes, car le bot est maintenant géré par Gunicorn
exec gunicorn --worker-class aiohttp.GunicornWebWorker main:app --bind 0.0.0.0:8000 --log-level info --timeout 120 --workers 2

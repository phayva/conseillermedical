#!/bin/bash
sleep 10  # Attendre 5 secondes pour laisser le bot et Flask s'initialiser
gunicorn main:app --bind 0.0.0.0:8000

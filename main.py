import os
import requests
import asyncio
import multiprocessing
import time
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask

# Configurez les logs pour déboguer
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.logger.info("Flask application created.")

# Configuration globale
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/distilbert/distilbert-base-multilingual-cased"

# Fonction pour interroger Hugging Face
def query_huggingface(text):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": text}
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = f"Erreur API : {e}, Statut : {response.status_code if 'response' in locals() else 'inconnu'}, Réponse : {response.text if 'response' in locals() else 'inconnue'}"
        logger.error(error_msg)
        return {"error": "Désolé, l'API Hugging Face est temporairement indisponible. Réessayez plus tard."}
    except ValueError:
        error_msg = f"Réponse JSON invalide : {response.text if 'response' in locals() else 'inconnue'}"
        logger.error(error_msg)
        return {"error": "Erreur interne de l'API. Réessayez plus tard."}

# Commande /start pour le bot Telegram
async def start(update, context):
    await update.message.reply_text("Bienvenue ! Envoyez-moi un message en arabe, darija ou français.")

# Réponse aux messages avec Hugging Face
async def echo(update, context):
    user_message = update.message.text
    logger.info(f"Message reçu : {user_message}")
    response = query_huggingface(user_message)
    await update.message.reply_text(str(response)[:4000])

# Gestion des erreurs pour le bot Telegram
async def error_handler(update, context):
    logger.error(f"Une erreur est survenue : {context.error}")
    if update and update.message:
        await update.message.reply_text("Désolé, une erreur est survenue. Veuillez réessayer plus tard.")

# Fonction pour lancer le bot Telegram (exécutée dans un processus séparé)
def run_bot():
    logger.info("Début de la fonction run_bot()")
    if not TELEGRAM_TOKEN or not HF_TOKEN:
        logger.error("Configuration manquante ! Vérifiez les variables TELEGRAM_TOKEN et HF_TOKEN.")
        return
    logger.info(f"TELEGRAM_TOKEN utilisé : {TELEGRAM_TOKEN}")
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        application.add_error_handler(error_handler)
        logger.info("Démarrage du bot...")
        # Créer une nouvelle boucle d'événements pour ce processus
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.run_polling(timeout=20))
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot : {e}")
    finally:
        loop.close()

# Endpoint Flask pour health check
app.logger.info("Flask prêt à répondre aux requêtes sur le port 8000.")
@app.route('/health')
def health_check():
    app.logger.info("Health check reçu !")
    return "OK", 200

# Endpoint Flask pour la page d'accueil (pour déboguer)
@app.route('/')
def home():
    app.logger.info("Route / appelée")
    return "Flask is running!", 200

# Log pour confirmer que Flask est prêt
logger.info("Flask initialisé et prêt à être démarré par Gunicorn.")

# Lancer le bot dans un processus séparé (pour tests locaux)
if __name__ == "__main__":
    logger.info("Mode local : démarrage du bot et de Flask pour le test.")
    # Lancer le bot Telegram dans un processus séparé
    bot_process = multiprocessing.Process(target=run_bot, daemon=True)
    bot_process.start()
    # Lancer Flask localement pour tester (sera ignoré par Koyeb)
    app.run(host="0.0.0.0", port=8000)

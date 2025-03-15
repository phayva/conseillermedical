import os
import requests
import asyncio
import threading
import time
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask

# Configurez les logs pour déboguer
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation contrôlée de Flask pour éviter les logs dupliqués
initialized = False

def init_app():
    global initialized
    if not initialized:
        app.logger.info("Flask application created.")
        app.logger.info("Flask prêt à répondre aux requêtes sur le port 8000.")
        initialized = True

app = Flask(__name__)
init_app()

# Configuration globale
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/nlptown/bert-base-multilingual-uncased-sentiment"

# Fonction pour interroger Hugging Face
def query_huggingface(text):
    logger.info(f"Interrogation de l'API Hugging Face avec le texte : {text}")
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": text}
    for attempt in range(3):  # Réessayer jusqu'à 3 fois
        try:
            response = requests.post(HF_API_URL, headers=headers, json=payload)
            logger.info(f"Requête envoyée à {HF_API_URL}, statut : {response.status_code}")
            if response.status_code == 429:  # Limite de requêtes atteinte
                logger.warning("Limite de requêtes atteinte, attente avant réessai...")
                time.sleep(10)
                continue
            if response.status_code == 503:  # Service indisponible
                logger.warning("Service Hugging Face indisponible, attente avant réessai...")
                time.sleep(15)
                continue
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
    return {"error": "Trop de tentatives échouées. Réessayez plus tard."}

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

# Fonction pour lancer le bot Telegram (exécutée dans un thread séparé)
def run_bot():
    logger.info("Début de la fonction run_bot()")
    if not TELEGRAM_TOKEN or not HF_TOKEN:
        logger.error("Configuration manquante ! Vérifiez les variables TELEGRAM_TOKEN et HF_TOKEN.")
        return
    logger.info(f"TELEGRAM_TOKEN utilisé : {TELEGRAM_TOKEN}")
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        # Créer une seule boucle d'événements pour ce processus
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Supprimer tout webhook existant
        logger.info("Suppression du webhook...")
        loop.run_until_complete(application.bot.delete_webhook(drop_pending_updates=True))
        # Ajouter les handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        application.add_error_handler(error_handler)
        logger.info("Démarrage du bot...")
        # Lancer le polling avec la même boucle
        loop.run_until_complete(application.run_polling(timeout=20))
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot : {e}")
    finally:
        loop.close()

# Endpoint Flask pour health check
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

# Lancer le bot dans un thread séparé
if __name__ == "__main__":
    logger.info("Mode local : démarrage du bot et de Flask pour le test.")
    # Lancer le bot Telegram dans un thread séparé
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    # Lancer Flask localement pour tester (sera ignoré par Koyeb si Gunicorn est utilisé)
    if os.getenv("FLASK_ENV") == "development":
        app.run(host="0.0.0.0", port=8000)
    else:
        logger.info("Mode production : Gunicorn doit être utilisé (via Procfile).")
        # Garder le processus principal actif jusqu'à ce que Gunicorn soit confirmé
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Arrêt manuel détecté.")

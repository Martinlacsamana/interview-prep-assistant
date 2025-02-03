import asyncio
import logging
import os
from telegram.ext import Application
import helpers.telegram
from server import create_flask_app, create_server

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
PORT = int(os.environ.get('PORT', '8080'))

# Validate required environment variables
if TELEGRAM_BOT_TOKEN is None:
    logger.error("TELEGRAM_BOT_TOKEN environment variable is not set.")
    exit(1)

if WEBHOOK_URL is None:
    logger.error("WEBHOOK_URL environment variable is not set.")
    exit(1)

async def main():
    '''Initializes and runs the Telegram bot with webhook support'''
    logger.info("Starting RUBY Interview Prep Assistant...")
    
    # Initialize bot application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).updater(None).build()
    
    # Setup telegram handlers
    helpers.telegram.setup_handlers(application)
    
    # Setup webhook
    await helpers.telegram.setup_webhook(application, WEBHOOK_URL)
    
    # Create and configure Flask app
    flask_app = create_flask_app(application)
    
    # Create server
    webserver = create_server(flask_app, PORT)
    
    # Run application and webserver together
    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()

if __name__ == '__main__':
    asyncio.run(main())
import asyncio
import logging
import os
import uvicorn
from http import HTTPStatus
from asgiref.wsgi import WsgiToAsgi
from flask import Flask, Response, make_response, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import helpers.openai

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
PORT = int(os.environ.get('PORT', '8080'))

if TELEGRAM_BOT_TOKEN is None:
    logger.error("TELEGRAM_BOT_TOKEN environment variable is not set.")
    exit(1)

if WEBHOOK_URL is None:
    logger.error("WEBHOOK_URL environment variable is not set.")
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Simple welcome message when user starts the bot'''
    welcome_message = (
        f"Hey {update.effective_user.first_name}! I'm RUBY, your interview prep assistant. "
        "Let's get you ready for those technical interviews! What would you like to work on?"
    )
    await update.message.reply_text(welcome_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Handles all incoming messages by passing them to OpenAI and returning the response'''
    try:
        # Start typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        prompt = update.message.text
        assistant_response = await helpers.openai.generate_response(prompt)
        
        await update.message.reply_text(assistant_response)
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("Sorry, I ran into an error. Could you try again?")

async def main():
    '''Initializes and runs the Telegram bot with webhook support'''
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).updater(None).build()

    # Simplified handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Enhanced webhook setup logging
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/telegram"
        logger.info(f"Attempting to set webhook with URL: {webhook_url}")
        
        try:
            # Get current webhook info for debugging
            webhook_info = await application.bot.get_webhook_info()
            logger.info(f"Current webhook status: {webhook_info.to_dict()}")
            
            # Try to set the webhook
            await application.bot.set_webhook(
                url=webhook_url,
                allowed_updates=Update.ALL_TYPES
            )
            logger.info(f"Successfully set webhook to: {webhook_url}")
            
            # Verify webhook was set correctly
            new_webhook_info = await application.bot.get_webhook_info()
            logger.info(f"New webhook status: {new_webhook_info.to_dict()}")
            
        except Exception as e:
            logger.error(f"Failed to set webhook: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            # Don't raise the error, let the app continue
    else:
        logger.warning("No WEBHOOK_URL provided or it's empty")
        logger.warning(f"WEBHOOK_URL value: '{WEBHOOK_URL}'")

    # Set up the Flask app
    flask_app = Flask(__name__)

    # Add logging to webhook endpoint
    @flask_app.route('/telegram', methods=['POST'])
    async def telegram_webhook():
        """Handle incoming Telegram updates with enhanced logging"""
        logger.info("Received webhook call")
        try:
            json_data = request.get_json()
            logger.info(f"Webhook payload: {json_data}")
            
            update = Update.de_json(json_data, application.bot)
            logger.info(f"Processed update object: {update}")
            
            await application.update_queue.put(update)
            return Response(status=HTTPStatus.OK)
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR)

    @flask_app.route('/healthcheck', methods=['GET'])
    async def health():
        '''Simple health check endpoint to verify the bot is running.'''
        response = make_response("The bot is still running fine :)", HTTPStatus.OK)
        response.mimetype = "text/plain"
        return response

    @flask_app.route('/webhook-debug', methods=['GET'])
    async def webhook_debug():
        '''Debug endpoint to check webhook status'''
        try:
            webhook_info = await application.bot.get_webhook_info()
            response = {
                'webhook_url': webhook_info.url,
                'has_custom_certificate': webhook_info.has_custom_certificate,
                'pending_update_count': webhook_info.pending_update_count,
                'last_error_message': webhook_info.last_error_message,
                'last_error_date': webhook_info.last_error_date,
                'max_connections': webhook_info.max_connections
            }
            return make_response(str(response), HTTPStatus.OK)
        except Exception as e:
            return make_response(f"Error getting webhook info: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR)

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=WsgiToAsgi(flask_app),
            port=PORT,
            use_colors=False,
            host="0.0.0.0",  # Listen on all interfaces
            timeout_keep_alive=70,
            timeout_graceful_shutdown=10
        )
    )

    # Run application and webserver together
    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()

if __name__ == '__main__':
    asyncio.run(main())
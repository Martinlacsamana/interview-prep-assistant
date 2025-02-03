import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import helpers.openai

logger = logging.getLogger(__name__)

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

def setup_handlers(application: Application):
    '''Setup all telegram bot handlers'''
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

async def setup_webhook(application: Application, webhook_url: str):
    '''Setup webhook for telegram bot'''
    if not webhook_url:
        logger.warning("No WEBHOOK_URL provided or it's empty")
        logger.warning(f"WEBHOOK_URL value: '{webhook_url}'")
        return

    webhook_path = f"{webhook_url}/telegram"
    logger.info(f"Attempting to set webhook with URL: {webhook_path}")
    
    try:
        # Get current webhook info for debugging
        webhook_info = await application.bot.get_webhook_info()
        logger.info(f"Current webhook status: {webhook_info.to_dict()}")
        
        # Try to set the webhook
        await application.bot.set_webhook(
            url=webhook_path,
            allowed_updates=Update.ALL_TYPES
        )
        logger.info(f"Successfully set webhook to: {webhook_path}")
        
        # Verify webhook was set correctly
        new_webhook_info = await application.bot.get_webhook_info()
        logger.info(f"New webhook status: {new_webhook_info.to_dict()}")
        
    except Exception as e:
        logger.error(f"Failed to set webhook: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")

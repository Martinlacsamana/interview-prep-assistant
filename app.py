import asyncio
import logging
import os
import uvicorn
from http import HTTPStatus
from asgiref.wsgi import WsgiToAsgi
from flask import Flask, Response, make_response, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
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
OPENAI_ASSISTANT_ID = None  # Global to store assistant ID
GLOBAL_THREAD_ID = None


if TELEGRAM_BOT_TOKEN is None:
    logger.error("TELEGRAM_BOT_TOKEN environment variable is not set.")
    exit(1)

if WEBHOOK_URL is None:
    logger.error("WEBHOOK_URL environment variable is not set.")
    exit(1)

async def initialize_openai():
    """Pre-initialize both OpenAI assistant and thread"""
    global OPENAI_ASSISTANT_ID, GLOBAL_THREAD_ID
    try:
        thread_id, assistant_id = await helpers.openai.initialize_conversation()
        OPENAI_ASSISTANT_ID = assistant_id
        GLOBAL_THREAD_ID = thread_id
        return assistant_id, thread_id
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI: {e}")
        raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Entry point for the bot, triggered by /start command. Displays the initial button interface.'''
    keyboard = [
        [InlineKeyboardButton("Create Tweet", callback_data='create_prompt')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_message = (
        f"Hey {update.effective_user.first_name}! What do you wanna cook up?"
    )
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Handles the "Create Prompt" button click and sets the state to await user input.'''
    query = update.callback_query
    await query.answer()
    if query.data == 'create_prompt':
        await query.message.reply_text("🎯 What would you like your tweet to be about?\n\n")
        context.user_data['state'] = 'awaiting_prompt'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Processes user's prompt message, generates a tweet, and asks for user confirmation.'''
    if context.user_data.get('state') == 'awaiting_prompt':
        prompt = update.message.text
        logging.info(f"Received prompt from user {update.effective_user.id}: {prompt}")

        try:
            # Use global thread ID
            tweet = await helpers.openai.generate_tweet(
                prompt, 
                GLOBAL_THREAD_ID,  # Use global thread
                OPENAI_ASSISTANT_ID
            )
            
            # Store the generated tweet in context for later use
            context.user_data['pending_tweet'] = tweet
            
            # Create confirmation buttons
            keyboard = [
                [
                    InlineKeyboardButton("Post Tweet", callback_data='post_tweet'),
                    InlineKeyboardButton("Revise Tweet", callback_data='regenerate')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"Here's your generated tweet:\n\n{tweet}\n\nWould you like to post or revise it?",
                reply_markup=reply_markup
            )
            
            # Update state
            context.user_data['state'] = 'awaiting_confirmation'
            
        except Exception as e:
            logger.error(f"Error generating tweet: {e}")
            await update.message.reply_text("Sorry, there was an error generating your tweet. Please try again.")
            context.user_data['state'] = None
    else:
        await update.message.reply_text("Please use /start to begin.")

async def handle_tweet_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GLOBAL_THREAD_ID
    query = update.callback_query
    await query.answer()
    
    if query.data == 'post_tweet':
        tweet = context.user_data.get('pending_tweet')
        if tweet:
            try:
                # Post to Twitter
                # helpers.twitter.post_tweet(tweet) UNCOMMENT WHEN READY
                await query.message.reply_text("Your tweet is live! 🎉")

                # Cleanup should return new thread ID
                try:
                    new_thread_id = await helpers.openai.cleanup_thread(
                        GLOBAL_THREAD_ID, 
                        OPENAI_ASSISTANT_ID
                    )
                    GLOBAL_THREAD_ID = new_thread_id  # Update global with new thread
                except Exception as e:
                    logger.error(f"Error cleaning up thread: {e}")
                    
                context.user_data.clear()

            except Exception as e:
                logger.error(f"Error posting tweet: {e}")
                await query.message.reply_text("Sorry, there was an error posting your tweet.")
        else:
            await query.message.reply_text("Sorry, something went wrong. Please try again.")
        
    elif query.data == 'regenerate':
        # Set state back to awaiting prompt
        context.user_data['state'] = 'awaiting_prompt'
        await query.message.reply_text("🎯 How should we adjust your tweet?")

async def main():
    '''Initializes and runs the Telegram bot with webhook support'''
    
    
    # Initialize OpenAI first, before any user connections
    assistant_id, thread_id = await initialize_openai()
    if not assistant_id or not thread_id:
        logger.error("Failed to initialize OpenAI assistant. Exiting.")
        exit(1)
    
    # Build the application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).updater(None).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_click, pattern='^create_prompt$'))
    application.add_handler(CallbackQueryHandler(handle_tweet_confirmation, pattern='^(post_tweet|regenerate)$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Set the webhook with error handling
    try:
        # webhook_info = await application.bot.get_webhook_info()
        # logger.info(f"Current webhook status: {webhook_info.to_dict()}")
        
        await application.bot.set_webhook(
            url=f"{WEBHOOK_URL}/telegram",
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"Failed to set webhook: {str(e)}")
        raise

    # Set up the Flask app
    flask_app = Flask(__name__)

    # Add logging to webhook endpoint
    @flask_app.route('/telegram', methods=['POST'])
    async def telegram_webhook():
        """Handle incoming Telegram updates by putting them into the `update_queue`"""
       
        try:
            update = Update.de_json(request.get_json(), application.bot)
            
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
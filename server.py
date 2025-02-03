import logging
from http import HTTPStatus
from flask import Flask, Response, make_response, request
from asgiref.wsgi import WsgiToAsgi
import uvicorn
from telegram import Update

logger = logging.getLogger(__name__)

def create_flask_app(application):
    '''Create and configure Flask app with all routes'''
    flask_app = Flask(__name__)

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

    return flask_app

def create_server(flask_app, port: int):
    '''Create and configure uvicorn server'''
    return uvicorn.Server(
        config=uvicorn.Config(
            app=WsgiToAsgi(flask_app),
            port=port,
            use_colors=False,
            host="0.0.0.0",  # Listen on all interfaces
            timeout_keep_alive=70,
            timeout_graceful_shutdown=10
        )
    )

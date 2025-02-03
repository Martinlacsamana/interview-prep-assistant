import logging
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

logger = logging.getLogger(__name__)

RECIPIENT_EMAIL = "martinlacsamana.dev@gmail.com"
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')

async def generate_cheatsheet(topic: str) -> bool:
    """
    Generates and emails a technical cheatsheet about a specific topic.
    
    Args:
        topic: The technical topic to create a cheatsheet for
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # 1. Generate the cheatsheet content
        content = "Your cheatsheet content here"  # I'll expand this later
        
        # 2. Create the email
        message = Mail(
            from_email="ruby@yourapp.com",
            to_emails=RECIPIENT_EMAIL,
            subject=f"Technical Cheatsheet: {topic}",
            plain_text_content=content
        )
        
        # 3. Send via SendGrid
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f"Sent cheatsheet about {topic} to {RECIPIENT_EMAIL}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending cheatsheet: {str(e)}")
        return False


TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "generate_cheatsheet",
        "description": "Generates and emails a technical cheatsheet to the user",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The technical topic for the cheatsheet"
                }
            },
            "required": ["topic"]
        }
    }
}
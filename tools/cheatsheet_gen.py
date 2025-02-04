import logging
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

RECIPIENT_EMAIL = "martinlacsamana.dev@gmail.com"
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
client = AsyncOpenAI()

async def generate_cheatsheet_content(topic: str) -> str:
    """Generate a comprehensive cheatsheet using OpenAI"""
    prompt = f"""Create a comprehensive technical cheatsheet about {topic}. Include:
    1. Key concepts and definitions
    2. Common use cases and patterns
    3. Best practices
    4. Code examples where relevant
    5. Common pitfalls to avoid
    
    Format it in a clear, organized way with markdown formatting."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a technical documentation expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        raise

async def generate_cheatsheet(topic: str) -> bool:
    """
    Generates and emails a technical cheatsheet about a specific topic.
    
    Args:
        topic: The technical topic to create a cheatsheet for
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # 1. Generate the cheatsheet content using OpenAI
        content = await generate_cheatsheet_content(topic)
        
        # 2. Create the email with markdown content
        message = Mail(
            from_email="ruby@yourapp.com",
            to_emails=RECIPIENT_EMAIL,
            subject=f"Technical Cheatsheet: {topic}",
            plain_text_content=content  # Later we could convert to HTML for better formatting
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
            "required": ["topic"],
            "additionalProperties": False
        },
        "strict": True
    }
}
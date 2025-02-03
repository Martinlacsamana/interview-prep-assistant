import re
import logging
import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import List
import aiohttp

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
client = AsyncOpenAI()

# Initialize empty list to store interactions as dictionaries
conversation_history: List[dict] = []
assistant_ID = os.environ.get('ASSISTANT_ID')
thread_ID = os.environ.get('THREAD_ID')

if not assistant_ID or not thread_ID:
    raise ValueError("ASSISTANT_ID and THREAD_ID must be set in environment variables")

async def generate_response(prompt):
    '''Generate a response using the Assistants API with conversation context'''
    try:
        # Run assistant with additional message
        run = await client.beta.threads.runs.create_and_poll(
            thread_id=thread_ID,
            assistant_id=assistant_ID,
            additional_messages=[{
                "role": "user",
                "content": prompt  
            }]
        )

        if run.status == "completed":
            messages = await client.beta.threads.messages.list(thread_id=thread_ID)
            response = messages.data[0].content[0].text.value
            
            # Store conversation history (optional now)
            conversation_history.append({
                'role': 'user',
                'content': prompt
            })
            conversation_history.append({
                'role': 'agent',
                'content': response
            })
            
            return response
        else:
            return f"Conversation failed with status: {run.status}"

    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise

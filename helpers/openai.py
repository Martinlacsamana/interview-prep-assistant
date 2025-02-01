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

async def initialize_conversation():
    """Initialize both OpenAI assistant and thread at startup"""
    try:
        logger.info("Starting OpenAI initialization...")
        # Create assistant
        assistant = await client.beta.assistants.create(
            name="Twitter Assistant",
            instructions="""You are a helpful assistant that generates engaging tweets. 
            Keep tweets under 200 characters. 
            ALWAYS respond with JSON in this format:
            {
                "tweet": "the generated tweet",
                "reasoning": "brief explanation of the tweet's approach"
            }""",
            model="gpt-4o-mini"
        )
        logger.info(f"✓ Assistant created with ID: {assistant.id}")
        
        # Create initial thread
        thread = await client.beta.threads.create()
        logger.info(f"✓ Thread created with ID: {thread.id}")
        
        return thread.id, assistant.id

    except Exception as e:
        logger.error(f"Error initializing OpenAI: {str(e)}")
        raise


async def generate_tweet(prompt, thread_id, assistant_id):
    '''Generate a tweet using the Assistants API with conversation context'''
    try:
        # Run assistant with additional message
        run = await client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id,
            additional_messages=[{  # Correct parameter name
                "role": "user",
                "content": f"Generate a tweet for: {prompt}"
            }],
            response_format={"type": "json_object"}
        )

        if run.status == "completed":
            messages = await client.beta.threads.messages.list(thread_id=thread_id)
            response = messages.data[0].content[0].text.value
            
            # Parse JSON response
            response_json = json.loads(response)
            tweet = response_json["tweet"]
            reasoning = response_json["reasoning"]
            cleaned_tweet = re.sub(r"^[\"""'']|[\"""'']$", "", tweet).strip()

            # Store user message
            conversation_history.append({
                'role': 'user',
                'content': f"Generate a tweet for: {prompt}"
            })

            # Store assistant message
            conversation_history.append({
                'role': 'agent',
                'content': cleaned_tweet,
                'reasoning': reasoning
            })
            
            return cleaned_tweet
        else:
            raise Exception(f"Run failed with status: {run.status}")

    except Exception as e:
        logger.error(f"Error generating tweet: {str(e)}")
        raise

async def cleanup_thread(thread_id: str, assistant_id: str):
    """Clean up thread and return new thread ID"""
    try:
        if conversation_history:
            # conversation_history is already a list of dicts, so we can use it directly
            payload = {
                'conversation_history': conversation_history,  
                'thread_id': thread_id,
                'assistant_id': assistant_id
            }
            logger.info(f"✓ Thread data saved: {conversation_history}")
            
            API_KEY = os.environ.get('METAVERSE_API_KEY')
            # Send to storage endpoint
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://metaverse-hq-226030353663.us-central1.run.app/v1/agents/save_thread_messages/',
                    json=payload,
                    headers={
                        "Authorization": API_KEY,
                        "Content-Type": "application/json"
                    }
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to save thread data: {await response.text()}")
                    else:
                        logger.info(f"Successfully saved thread data for thread {thread_id}")

            conversation_history.clear()  # Clear after successful storage

        # Cleanup the thread
        await client.beta.threads.delete(thread_id)
        
        # Create new thread and return its ID
        new_thread = await client.beta.threads.create()
        return new_thread.id
        
    except Exception as e:
        logger.error(f"Error in cleanup_thread: {e}")
        conversation_history.clear()  # Clear anyways
        raise

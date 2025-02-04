from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Get MongoDB URI from environment variable
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGODB_URI)
db = client.interview_prep_db  # database name

async def store_interaction(
    user_id: str,
    prompt: str,
    response: str,
    tools_used: Optional[List[str]] = None
) -> bool:
    """
    Store user interaction in MongoDB
    
    Args:
        user_id: Telegram user ID
        prompt: User's input message
        response: Assistant's response
        tools_used: List of tools used in generating the response
    Returns:
        bool: True if successful, False if failed
    """
    try:
        await db.interactions.insert_one({
            'user_id': user_id,
            'prompt': prompt,
            'response': response,
            'tools_used': tools_used or [],
            'timestamp': datetime.utcnow()
        })
        logger.info(f"Stored interaction for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error storing interaction: {str(e)}")
        return False

async def get_user_interactions(
    user_id: str,
    days: int = 30,
    limit: int = 100
) -> List[Dict]:
    """
    Retrieve user's past interactions
    
    Args:
        user_id: Telegram user ID
        days: Number of past days to look up
        limit: Maximum number of interactions to return
    Returns:
        List of interaction documents
    """
    try:
        cutoff = datetime.utcnow() - datetime.timedelta(days=days)
        cursor = db.interactions.find({
            'user_id': user_id,
            'timestamp': {'$gte': cutoff}
        }).sort('timestamp', -1).limit(limit)
        
        return await cursor.to_list(length=limit)
    except Exception as e:
        logger.error(f"Error retrieving interactions: {str(e)}")
        return []

async def check_connection() -> bool:
    """Verify MongoDB connection is working"""
    try:
        await client.admin.command('ping')
        return True
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        return False 

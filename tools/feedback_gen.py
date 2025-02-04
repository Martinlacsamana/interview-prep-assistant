import logging
from typing import Dict
from openai import AsyncOpenAI
from helpers.mongodb import db
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
client = AsyncOpenAI()

async def analyze_interactions(user_id: str, days: int = 30) -> Dict:
    """Analyze user's past interactions"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Get user's interactions
    interactions = await db.interactions.find({
        'user_id': user_id,
        'timestamp': {'$gte': cutoff}
    }).to_list(length=None)
    
    if not interactions:
        return {"error": "No interactions found"}
    
    analysis_prompt = f"""Analyze these coding interview interactions and create a feedback report. Include:
    1. Overall strengths and weaknesses
    2. Most frequently discussed topics
    3. Areas needing improvement
    4. Specific topic recommendations
    5. Study plan suggestions
    
    Interactions: {str(interactions)}"""
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing coding interview performance."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.7
        )
        return {
            "report": response.choices[0].message.content,
            "analyzed_interactions": len(interactions)
        }
    except Exception as e:
        logger.error(f"Error generating feedback: {str(e)}")
        raise

async def generate_feedback_report(days: int = 30) -> Dict:
    """Generate a feedback report for the user's recent interactions"""
    try:
        # We'll use thread_ID as user_id for now
        from helpers.openai import thread_ID
        feedback = await analyze_interactions(thread_ID, days)
        return feedback
    except Exception as e:
        logger.error(f"Error generating feedback report: {str(e)}")
        raise

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "generate_feedback_report",
        "description": "Analyzes user's interview practice history and generates a personalized feedback report",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of past days to analyze",
                    "default": 30
                }
            },
            "additionalProperties": False
        },
        "strict": True
    }
}

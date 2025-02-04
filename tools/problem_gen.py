import logging
from typing import Dict
import random
from openai import AsyncOpenAI
import os

logger = logging.getLogger(__name__)
client = AsyncOpenAI()

DIFFICULTY_LEVELS = ["easy", "medium", "hard"]
TOPICS = ["arrays", "strings", "linked lists", "trees", "dynamic programming", 
          "graphs", "sorting", "searching", "recursion", "hash tables"]

async def generate_problem_content(topic: str, difficulty: str) -> Dict:
    """Generate a coding problem using OpenAI"""
    prompt = f"""Create a coding interview problem about {topic} at {difficulty} difficulty level. Include:
    1. Problem description
    2. Input/Output examples
    3. Constraints
    4. Initial function signature
    5. Hints (optional)
    
    Format it in a clear, organized way with markdown."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at creating coding interview problems."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        return {
            "content": response.choices[0].message.content,
            "topic": topic,
            "difficulty": difficulty
        }
    except Exception as e:
        logger.error(f"Error generating problem: {str(e)}")
        raise

async def generate_practice_problem(topic: str = None, difficulty: str = None) -> Dict:
    """
    Generates a coding practice problem with specified or random parameters.
    
    Args:
        topic: Optional topic for the problem
        difficulty: Optional difficulty level
    Returns:
        Dict containing problem content and metadata
    """
    try:
        # Use provided parameters or choose random ones
        selected_topic = topic or random.choice(TOPICS)
        selected_difficulty = difficulty or random.choice(DIFFICULTY_LEVELS)
        
        return await generate_problem_content(selected_topic, selected_difficulty)
        
    except Exception as e:
        logger.error(f"Error generating practice problem: {str(e)}")
        raise

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "generate_practice_problem",
        "description": "Generates a coding practice problem with optional topic and difficulty",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The programming topic for the problem (optional)",
                    "enum": TOPICS
                },
                "difficulty": {
                    "type": "string",
                    "description": "The difficulty level of the problem (optional)",
                    "enum": DIFFICULTY_LEVELS
                }
            },
            "additionalProperties": False
        },
        "strict": True
    }
}

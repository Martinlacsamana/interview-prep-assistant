import re
import logging
import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import List
import aiohttp  
# from tools.cheatsheet_gen import generate_cheatsheet, TOOL_DEFINITION as CHEATSHEET_TOOL
# from tools.problem_gen import generate_practice_problem, TOOL_DEFINITION as PROBLEM_TOOL
# from tools.feedback_gen import generate_feedback_report, TOOL_DEFINITION as FEEDBACK_TOOL
# from helpers.mongodb import store_interaction

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
client = AsyncOpenAI()

# Tools list
# tools = [CHEATSHEET_TOOL, PROBLEM_TOOL, FEEDBACK_TOOL]

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

        # Add detailed logging here
        logger.info(f"Run status: {run.status}")
        if run.status == "failed":
            logger.info(f"Run failed with last_error: {run.last_error}")

        # Comment out tool handling section
        # if hasattr(run, 'required_action'):
        #     tool_calls = run.required_action.submit_tool_outputs.tool_calls
        #     tool_outputs = []
            
        #     for tool_call in tool_calls:
        #         if tool_call.function.name == "generate_cheatsheet":
        #             args = json.loads(tool_call.function.arguments)
        #             success = await generate_cheatsheet(args["topic"])
        #             tool_outputs.append({
        #                 "tool_call_id": tool_call.id,
        #                 "output": json.dumps({"success": success})
        #             })
        #         elif tool_call.function.name == "generate_practice_problem":
        #             args = json.loads(tool_call.function.arguments)
        #             topic = args.get("topic", None)
        #             difficulty = args.get("difficulty", None)
        #             problem = await generate_practice_problem(topic, difficulty)
        #             tool_outputs.append({
        #                 "tool_call_id": tool_call.id,
        #                 "output": json.dumps(problem)
        #             })
        #         elif tool_call.function.name == "generate_feedback_report":
        #             args = json.loads(tool_call.function.arguments)
        #             days = args.get("days", 30)
        #             feedback = await generate_feedback_report(days)
        #             tool_outputs.append({
        #                 "tool_call_id": tool_call.id,
        #                 "output": json.dumps(feedback)
        #             })
            
        #     # Submit outputs back to the assistant
        #     run = await client.beta.threads.runs.submit_tool_outputs_and_poll(
        #         thread_id=thread_ID,
        #         run_id=run.id,
        #         tool_outputs=tool_outputs
        #     )

        if run.status == "completed":
            messages = await client.beta.threads.messages.list(thread_id=thread_ID)
            response = messages.data[0].content[0].text.value
            
            # Comment out MongoDB storage
            # tools_used = [tool_call.function.name for tool_call in tool_calls] if hasattr(run, 'required_action') else []
            # await store_interaction(
            #     user_id=thread_ID,
            #     prompt=prompt,
            #     response=response,
            #     tools_used=tools_used
            # )
            
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
            # Add detailed logging for non-completed status
            logger.error(f"Run failed with status: {run.status}")
            logger.error(f"Run details: {run}")  # log full run object
            logger.error(f"Last error: {getattr(run, 'last_error', 'No error details available')}")
            return f"Conversation failed with status: {run.status}"

    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise

# ./backend/app/ai/service.py
"""
AI Service layer orchestrating chat interactions, tool use, and memory.
Implements the hybrid LangChain/Instructor approach.
"""
import instructor
import litellm # To interact with Ollama's OpenAI-compatible endpoint
import logging
import json
from typing import List, Dict, Optional, Tuple, Literal, Union, Any
from uuid import UUID

from pydantic import BaseModel, Field
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings
# Import memory interaction functions
from app.ai.memory import search_relevant_memories, store_memory
# Import tool execution function
from app.tools.client import execute_tool
# Import registry function (if needed for descriptions, though Pydantic models define structure now)
# from app.tools.registry import get_tool_details

# Placeholder for User Info dictionary structure
UserInfo = Dict[str, Any]

logger = logging.getLogger(__name__)

# --- Pydantic Models for Instructor Tool Calling ---

# Define Pydantic models for the *arguments* each tool expects
class GetChoreStatusArgs(BaseModel):
    chore_id: str = Field(..., description="The unique identifier (UUID) of the chore.")

class ScheduleScreenTimeArgs(BaseModel):
    user_id: str = Field(..., description="The UUID of the user whose screen time is being scheduled.")
    date: str = Field(..., description="The date for the schedule block in YYYY-MM-DD format.")
    start_time: str = Field(..., description="The start time for the block in HH:MM (24-hour) format.")
    end_time: str = Field(..., description="The end time for the block in HH:MM (24-hour) format.")
    reason: Optional[str] = Field(None, description="An optional reason for scheduling this block.")

# Add other argument models for your different tools...

# Define models representing the *call* to a specific tool, including its arguments
class GetChoreStatusCall(BaseModel):
    tool_name: Literal["get_chore_status"] = "get_chore_status" # Literal forces this value
    arguments: GetChoreStatusArgs = Field(..., description="Arguments for the get_chore_status tool.")

class ScheduleScreenTimeCall(BaseModel):
    tool_name: Literal["schedule_screen_time_block"] = "schedule_screen_time_block"
    arguments: ScheduleScreenTimeArgs = Field(..., description="Arguments for the schedule_screen_time_block tool.")

# Add other Call models for different tools...

# Define a model representing the case where NO tool is needed
class NoToolCall(BaseModel):
    tool_name: Literal["no_tool_needed"] = "no_tool_needed"
    arguments: Optional[Dict] = Field(None, description="No arguments needed when no tool is called.") # Keep structure consistent

# Create a Union of all possible ToolCall models + NoToolCall
# This is the response_model Instructor will try to populate.
# The LLM MUST choose one of these structures.
ToolCallDecision = Union[
    GetChoreStatusCall,
    ScheduleScreenTimeCall,
    # Add other ToolCall models here...
    NoToolCall
]

# --- Configure Instructor with Ollama via LiteLLM ---
# Patch litellm's acompletion function to add Instructor's capabilities
# Point it to your Ollama service URL using LiteLLM's format
# Use TOOLS mode for function calling / structured output based on Pydantic models
try:
    aclient_instructor = instructor.patch(
        litellm.acompletion,
        mode=instructor.Mode.TOOLS # Use TOOLS mode
    )
    logger.info("Instructor patched with LiteLLM acompletion successfully.")
except Exception as e:
    logger.error(f"Failed to patch LiteLLM with Instructor: {e}", exc_info=True)
    aclient_instructor = None # Fallback or raise error

# --- Main Chat Processing Function ---
async def process_chat_message_hybrid(
    pool: AsyncConnectionPool,
    user_info: UserInfo,
    message: str,
    chat_history: Optional[List[Tuple[str, str]]] = None # List of (HumanInput, AIOutput)
) -> str:
    """
    Processes a user chat message using a hybrid Instructor/LLM approach.

    1. Retrieves relevant memories using vector search.
    2. Uses Instructor + LiteLLM + Pydantic models to determine if a tool call is needed
       and extracts structured arguments if so.
    3. Executes the chosen tool via app.tools.client.execute_tool.
    4. Generates a final conversational response using a standard LLM call,
       incorporating context and any tool results.
    5. Stores relevant conversation turns in memory.
    """
    user_id = user_info.get('id')
    family_id = user_info.get('family_id')
    user_name = user_info.get('name', 'User') # Get user name if available

    if not user_id or not family_id:
         logger.error("User ID or Family ID missing in user_info for chat processing.")
         return "I'm sorry, I'm missing some information needed to process your request."

    if aclient_instructor is None:
         logger.error("Instructor client is not available. Cannot process chat with tool capability.")
         return "I'm sorry, my tool processing capability is currently unavailable."

    logger.info(f"Processing message for user {user_id}: '{message[:100]}...'")
    final_ai_response = "I'm sorry, something went wrong while processing your message." # Default error response

    try:
        # 1. Retrieve Memory Context (RAG)
        relevant_memories = await search_relevant_memories(message, user_id, family_id, k=3)
        context_text = "\n".join([f"- {mem['text']} (Score: {mem['score']:.2f})" for mem in relevant_memories]) if relevant_memories else "No specific relevant history found."
        logger.debug(f"Retrieved context:\n{context_text}")

        # 2. Determine Tool Call using Instructor
        # Prepare descriptions of tools for the LLM's choice prompt
        tool_descriptions = """
        Available tools:
        - get_chore_status: Retrieves the current status of a specific chore by its ID. Requires 'chore_id'.
        - schedule_screen_time_block: Schedules a specific block of screen time for a user on a given date. Requires 'user_id', 'date', 'start_time', 'end_time'.
        - no_tool_needed: Use this if the user query is conversational or does not require calling a specific function.
        """
        # Construct prompt for Instructor
        tool_selection_prompt = f"""
        User Name: {user_name}
        User Query: "{message}"

        Relevant Context from Memory:
        {context_text}

        Based on the user query and context, which SINGLE tool from the list below is the most appropriate to use?
        {tool_descriptions}

        If a tool is chosen, determine the necessary arguments based ONLY on the information available in the query and context.
        If no tool is appropriate, choose 'no_tool_needed'.
        """

        logger.debug("Attempting tool selection with Instructor...")
        tool_call_decision: Optional[ToolCallDecision] = None
        try:
            tool_call_decision = await aclient_instructor(
                model=f"ollama/{settings.OLLAMA_CHAT_MODEL}", # Ensure model supports function calling/tool use well
                messages=[{"role": "user", "content": tool_selection_prompt}],
                response_model=ToolCallDecision, # The Union[] model
                max_retries=1, # Retry once if validation fails
            )
            if tool_call_decision:
                logger.info(f"Instructor decision: Tool='{tool_call_decision.tool_name}' Args='{getattr(tool_call_decision, 'arguments', None)}'")
            else:
                logger.warning("Instructor returned None for tool decision.")
                tool_call_decision = NoToolCall(tool_name="no_tool_needed")

        except Exception as instructor_err:
            logger.error(f"Instructor failed to determine tool call: {instructor_err}", exc_info=True)
            tool_call_decision = NoToolCall(tool_name="no_tool_needed") # Default to no tool on error


        # 3. Execute Tool if Chosen
        tool_result_str = "" # Initialize as empty string
        if tool_call_decision and not isinstance(tool_call_decision, NoToolCall):
            # Ensure arguments exist and convert Pydantic model to dict
            tool_args = tool_call_decision.arguments.model_dump() if tool_call_decision.arguments else {}
            try:
                tool_result = await execute_tool(
                    tool_name=tool_call_decision.tool_name,
                    arguments=tool_args
                )
                # Format result for inclusion in the next LLM prompt
                tool_result_str = f"Tool '{tool_call_decision.tool_name}' executed successfully. Result: {json.dumps(tool_result)}"
                logger.info(tool_result_str)
            except Exception as tool_exec_err:
                # Handle errors from execute_tool (includes HTTPExceptions)
                logger.error(f"Failed to execute tool '{tool_call_decision.tool_name}': {tool_exec_err}", exc_info=True)
                detail = getattr(tool_exec_err, 'detail', str(tool_exec_err)) # Get detail if HTTPException
                tool_result_str = f"Error: Could not execute tool '{tool_call_decision.tool_name}'. Reason: {detail}"


        # 4. Generate Final Conversational Response
        # Combine context, history, query, and tool result (if any) for the final LLM call
        # Use a simpler prompt structure for the final chat response generation
        system_prompt_final = f"You are a helpful family assistant. Relevant context:\n{context_text}"
        # Format chat history simply
        history_formatted = "\n".join([f"Human: {h}\nAI: {a}" for h, a in (chat_history or [])])

        final_llm_messages = [{"role": "system", "content": system_prompt_final}]
        if history_formatted:
             # Simplified history injection
            final_llm_messages.append({"role": "system", "content": f"Previous conversation turns:\n{history_formatted}"})

        # Add user message
        final_llm_messages.append({"role": "user", "content": message})

        # Add tool result as context if it exists
        if tool_result_str:
            final_llm_messages.append({"role": "system", "content": f"Tool execution information: {tool_result_str}"})
            final_llm_messages.append({"role": "system", "content": "Now, provide a concise and helpful response to the user based on their original query and the tool result."})


        logger.debug("Generating final chat response...")
        final_response_completion = await litellm.acompletion(
             model=f"ollama/{settings.OLLAMA_CHAT_MODEL}",
             messages=final_llm_messages,
        )
        final_ai_response = final_response_completion.choices[0].message.content.strip()
        logger.info("Final AI response generated.")

        # 5. Store Memories
        await store_memory(pool, user_id, family_id, message, memory_type="conversation", source="user_chat")
        if final_ai_response:
            await store_memory(pool, user_id, family_id, final_ai_response, memory_type="conversation", source="ai_chat")
        # Optionally store structured memory about the tool call itself
        if tool_call_decision and not isinstance(tool_call_decision, NoToolCall):
             tool_memory_text = f"Attempted tool call '{tool_call_decision.tool_name}' with args {getattr(tool_call_decision, 'arguments', None)}. Result info: {tool_result_str}"
             await store_memory(pool, user_id, family_id, tool_memory_text, memory_type="conversation", source="system_tool_interaction")

        return final_ai_response

    except Exception as e:
        logger.error(f"Critical error in process_chat_message for user {user_id}: {e}", exc_info=True)
        # Fallback generic error message
        return "I encountered an unexpected issue while processing your request. Please try again later."
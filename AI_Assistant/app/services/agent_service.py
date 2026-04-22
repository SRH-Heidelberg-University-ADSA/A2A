"""
Assistant + A2A Coordinator
Uses LangChain Core to serve as both a personal assistant (calendar/email)
and an A2A coordinator (routing requests to specialized agents).
"""
import os
import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from app.config import Settings

# Import local tools
from app.tools.calendar_tools import (
    list_calendar_events,
    schedule_calendar_event,
    delete_calendar_event,
    find_and_delete_event,
    get_available_slots
)
from app.tools.email_tools import summarize_unread_emails

# Import A2A delegation tool
from app.tools.delegation_tools import delegate_task

logger = logging.getLogger("app.Agent_Service")
settings = Settings()

if not settings.openrouter_api_key:
    raise ValueError("OPENROUTER_API_KEY missing from environment.")

# Initialize OpenRouter LLM (using OpenAI-compatible interface)
llm = ChatOpenAI(
    model=settings.openrouter_model,
    temperature=0,
    max_tokens=4096,
    openai_api_key=settings.openrouter_api_key,
    base_url=settings.openrouter_base_url,
    default_headers={
        "HTTP-Referer": "https://github.com/Smainos-A2A", # Optional, but recommended by OpenRouter
        "X-Title": "Smainos AI Assistant"
    }
)

# Combine all tools
tools = [
    list_calendar_events,
    schedule_calendar_event,
    delete_calendar_event,
    find_and_delete_event,
    get_available_slots,
    summarize_unread_emails,
    delegate_task
]

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)
tool_map = {tool.name: tool for tool in tools}

# Define the base prompt
BASE_SYSTEM_PROMPT = """You are an AI Assistant and A2A Coordinator.

You have LOCAL tools for Calendar and Email. For everything else, you delegate to specialized agents using `delegate_task`.

STEP 1: Read the user's request.
STEP 2: Decide which action to take based on these rules:

IF the request is about calendar (events, schedule, free slots, meetings) → use your calendar tools
IF the request is about email (unread, inbox, summarize emails) → use summarize_unread_emails tool
IF the request is about fitness, workout, exercise, gym, muscle building, weight loss, diet plan, nutrition plan, protein intake, meal plan for fitness, training program, bodybuilding, cardio → delegate to Fitness_Agent
IF the request is about data, dataset, CSV, analyze data, statistics, trends, insights, spreadsheet → delegate to Data_Analyst
IF the request is about weather, forecast, soil, agriculture, farming, crop, harvest, irrigation, planting → delegate to Agriculture_Agent
IF the request is about football, soccer, match event, goal, red card, penalty, offside, tweet about football → delegate to Football_Reporter
OTHERWISE → Do NOT delegate. Say: "I don't have a specialized agent for that task." and list your capabilities.

IMPORTANT BOUNDARIES:
- General cooking, recipes, or food preparation questions (e.g. "how to make a sandwich", "recipe for pasta") are NOT fitness. Do NOT delegate these.
- Only delegate to Fitness_Agent when the query is specifically about fitness goals, workout plans, exercise routines, or nutrition for fitness/health goals.

DELEGATION FORMAT:
- target_agent_name must be exactly: "Fitness_Agent", "Data_Analyst", "Agriculture_Agent", or "Football_Reporter"
- task_query must contain the user's full original question

FORMATTING:
- Format responses in markdown.
"""



def build_system_prompt():
    """Dynamically builds the system prompt with the current agent registry."""
    try:
        from app.services.discovery import get_all_agents, fetch_agent_card, format_agent_card_for_llm
        agents = get_all_agents()
        if not agents:
            return BASE_SYSTEM_PROMPT + "\n\nACTIVE AGENTS in Registry:\nNone discovered."
            
        registry_text = "\n\nACTIVE AGENTS in Registry:\n"
        for idx, agent in enumerate(agents):
            name = agent.get('name', 'Unknown')
            # Use the local card data to provide capabilities context
            card = fetch_agent_card(name)
            if card:
                registry_text += f"\n--- Agent {idx+1} ---\n"
                registry_text += format_agent_card_for_llm(card)
            else:
                registry_text += f"\n- {name}: (No capabilities fetched)\n"
                
        return BASE_SYSTEM_PROMPT + registry_text
    except Exception as e:
        logger.error(f"Failed to build dynamic prompt: {str(e)}")
        return BASE_SYSTEM_PROMPT + "\n\n[Warning: Failed to load agent registry]"

def query_assistant(user_query: str, trace_log: list, file_info: dict = None) -> str:
    """
    Main loop for handling user queries, tool execution, and delegation.
    """
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        
        tz = ZoneInfo(settings.calendar_timezone)
        now = datetime.now(tz)
        current_time_str = now.strftime("%A, %Y-%m-%d %H:%M:%S %Z")
        
        # Build prompt: Include time, file context, and dynamic agent registry
        dynamic_prompt = build_system_prompt()
        context = f"\n\nCurrent Date and Time: {current_time_str}"
        if file_info:
            context += f"\n[FILE ATTACHED: '{file_info['filename']}'] - The file data has been stored. If delegating to a Data Analyst, mention the file is attached."

        system_prompt_complete = dynamic_prompt + context

        messages = [
            SystemMessage(content=system_prompt_complete),
            HumanMessage(content=user_query)
        ]
        
        # Token tracking
        total_input_tokens = 0
        total_output_tokens = 0
        
        # Run loop (max 5 iterations)
        for _ in range(5):
            response = llm_with_tools.invoke(messages)
            messages.append(response)
            
            # Track token usage from response metadata
            usage_meta = response.response_metadata.get("token_usage", {}) if hasattr(response, "response_metadata") else {}
            if not usage_meta:
                usage_meta = response.response_metadata.get("usage", {}) if hasattr(response, "response_metadata") else {}
            total_input_tokens += usage_meta.get("prompt_tokens", 0)
            total_output_tokens += usage_meta.get("completion_tokens", 0)
            
            if not response.tool_calls:
                content = response.content
                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, str):
                            text_parts.append(block)
                        elif isinstance(block, dict) and "text" in block:
                            text_parts.append(block["text"])
                        else:
                            text_parts.append(str(block))
                    final_text = "\n".join(text_parts)
                else:
                    final_text = str(content)
                
                # Return text + token usage as dict
                return {"text": final_text, "input_tokens": total_input_tokens, "output_tokens": total_output_tokens}
            
            # Execute tools
            delegation_result = None  # Track delegation output
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]
                
                is_delegation = (tool_name == "delegate_task")
                if is_delegation:
                    agent_name = tool_args.get("target_agent_name", "unknown")
                    logger.info(f"Delegating to {agent_name}...")
                    trace_log.append(f"**LLM Decision**: Matched `{agent_name}` for request")
                else:
                    logger.info(f"Executing local tool: {tool_name}")
                    trace_log.append(f"**Local Assistant Tool**: `{tool_name}`")
                
                trace_log.append(f"**Tool Call ({tool_name})**: Arguments: {json.dumps(tool_args)}")
                
                tool = tool_map.get(tool_name)
                if tool:
                    try:
                        tool_result = tool.invoke(tool_args)
                        
                        # Add a snippet of the result to trace
                        snippet = str(tool_result)[:100] + "..." if len(str(tool_result)) > 100 else str(tool_result)
                        trace_log.append(f"**Tool Call ({tool_name}) Result**: {snippet}")
                        
                        # If this was a delegation, capture the full result
                        if is_delegation:
                            delegation_result = str(tool_result)
                        
                    except Exception as e:
                        tool_result = f"Error executing tool: {str(e)}"
                        trace_log.append(f"**Error** in {tool_name}: {str(e)}")
                else:
                    tool_result = f"Error: Tool {tool_name} not found."
                
                messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_id))
            
            # If delegation happened, return the FULL result directly
            # instead of letting the LLM summarize/truncate it
            if delegation_result is not None:
                return {"text": delegation_result, "input_tokens": total_input_tokens, "output_tokens": total_output_tokens}

        
        return {"text": "I'm sorry, I couldn't complete your request after multiple tool calls.", "input_tokens": total_input_tokens, "output_tokens": total_output_tokens}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"text": f"Sorry, I encountered an issue: {str(e)}", "input_tokens": 0, "output_tokens": 0}


def query_llm(user_query: str, user_id: str = "default", trace_log: list = None, file_info: dict = None) -> dict:
    """Wrapper for the router."""
    if trace_log is None:
        trace_log = []
    
    try:
        result = query_assistant(user_query, trace_log, file_info)
        return {
            "type": "response",
            "content": result["text"],
            "enhanced": True,
            "fallback": False,
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0)
        }
    except Exception as e:
        trace_log.append(f"**Error** in query_llm: {str(e)}")
        return {
            "type": "error",
            "content": f"Coordinator error: {str(e)}"
        }

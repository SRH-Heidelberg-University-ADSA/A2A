from langchain_core.tools import tool
from app.services.discovery import find_agent
from app.services.rpc_client import call_agent_unified
from app.utils.parsing_utils import extract_text_from_response
import threading

# Simple thread-local file context for delegation
_file_context = threading.local()

def set_file_context(file_content_base64: str, filename: str = None):
    _file_context.data = file_content_base64
    _file_context.filename = filename

def get_file_context():
    return {
        "file_content_base64": getattr(_file_context, "data", None),
        "filename": getattr(_file_context, "filename", None)
    }

def clear_file_context():
    _file_context.data = None
    _file_context.filename = None

@tool
def delegate_task(target_agent_name: str, task_query: str) -> str:
    """
    Delegates a task to a specialized agent.
    Use this tool when the user's request matches the description of a discovered agent.
    
    Args:
        target_agent_name: The name of the agent to delegate to (e.g., "Fitness_Agent", "Data_Analyst").
        task_query: The specific query or instruction for that agent.
    """
    # 1. Discover the Agent
    agent = find_agent(target_agent_name)
    if not agent:
        return f"Error: Agent '{target_agent_name}' not found in the registry."
        
    call_config = agent["call_config"]
    
    # 2. Build params — check if the agent needs custom param mapping
    param_mapping = call_config.get("param_mapping")
    
    if param_mapping:
        query_field = param_mapping.get("query_field", "query")
        params = {query_field: task_query}
        defaults = param_mapping.get("defaults", {})
        params.update(defaults)
    else:
        params = {"query": task_query}
    
    # 3. Check for file context — if a file was uploaded, include it in params
    file_ctx = get_file_context()
    if file_ctx["file_content_base64"]:
        params["data_payload"] = file_ctx["file_content_base64"]
        print(f"Delegation: Including uploaded file data ({file_ctx['filename']})")
    
    # 4. Call the agent through the unified dispatcher (protocol-agnostic)
    try:
        print(f"Delegation: Calling '{target_agent_name}' via {call_config['protocol']} at {call_config['url']}")
        print(f"Delegation: Params keys: {list(params.keys())}")
        response = call_agent_unified(call_config, params)
        
        if response["status"] == "success":
            result = response["result"]
            
            # Use centralized parsing utility
            return extract_text_from_response(result)
            
        else:
            return f"Error from Agent '{target_agent_name}': {response.get('error')}"
            
    except Exception as e:
        return f"Error delegating to '{target_agent_name}': {str(e)}"

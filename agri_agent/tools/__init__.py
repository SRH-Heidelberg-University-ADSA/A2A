# tools/__init__.py
# Import the actual tool objects (functions decorated with @tool)

from .search import search_web as search_web_tool
from .soil import get_soil_data as get_soil_data_tool
from .weather import get_current_weather as get_current_weather_tool

# --- 1. The Unified List for the Model ---
AGENT_TOOLS = [
    search_web_tool,
    get_soil_data_tool,
    get_current_weather_tool,
]

# 
#  2. The Execution Map for Python ---
# We map the model's requested name (tool.name) to the function's executable body (tool.func)
TOOL_FUNCTION_MAP = {
    func.name: func.func 
    for func in AGENT_TOOLS
}
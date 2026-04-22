from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

from langchain_tavily import TavilySearch
from langchain.tools import tool

# Initialize the Tavily tool with your API key
tavily_wrapper = TavilySearch(
    k=5,
    tavily_api_key=os.getenv("TAVILY_API_KEY")
)

@tool  # agent .py calls automatically 
def search_web(query: str) -> str:  # takes query as string and it tells the result should be in string    
    """Useful for searching the internet for current events, agricultural news, scientific facts, market prices, or recent developments not found in the local knowledge base."""
    try:
        results = tavily_wrapper.invoke(query)   # this is where actuall query is sent to server and get the op 
        return results
    except Exception as e:
        return f"Error performing web search: {e}"

# Define the final tool object
search_tool = search_web

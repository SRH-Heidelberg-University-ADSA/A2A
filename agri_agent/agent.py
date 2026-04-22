import os
from dotenv import load_dotenv

# Modern LangChain & LangGraph Imports
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# Tools from the tools/ package
from tools import AGENT_TOOLS

# RAG Tool
from rag_client import load_rag_client
from langchain_core.tools.retriever import create_retriever_tool

load_dotenv()

# ==========================================
# 1. TOOL SETUP
# ==========================================

try:
    retriever = load_rag_client()
    rag_tool = create_retriever_tool(
        retriever,
        "pdf_knowledge_base",

        # ✅ FIX 3 — Better description so agent
        # uses RAG for ALL farming questions
        "Search this tool FIRST for ANY questions "
        "about farming, agriculture, vegetables, "
        "fruits, organic methods, food preservation, "
        "drying, composting, soil health, crop care, "
        "or pest control. This contains expert "
        "PDF knowledge from agricultural guides."
    )
    tools = AGENT_TOOLS + [rag_tool]
    print(" RAG tool loaded successfully from ChromaDB.")
except Exception as e:
    print(f" Could not load RAG tool (run ingestion.py first): {e}")
    tools = AGENT_TOOLS

print(f"  Agent loaded with {len(tools)} tools: {[t.name for t in tools]}")

# ==========================================
# 2. LLM SETUP
# ==========================================

# ✅ FIX 2 — Using Gemini which supports tool calling
llm = ChatOpenAI(
    model="google/gemini-2.0-flash-001",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    max_tokens=2048  # ← add this line
)

# ==========================================
# 3. SYSTEM PROMPT
# ==========================================

system_prompt = """You are Krishi-Intel Pro, an expert agricultural AI assistant.
Your goal is to help farmers with agronomy, weather, soil, and crop management.

You have access to the following tools:
- get_current_weather: Get real-time weather for any location.
- get_soil_data: Get real-time soil temperature and moisture data.
- search_web: Search the internet for agricultural news, prices, or research.
- pdf_knowledge_base: Search private agricultural PDF documents (if loaded).

STRICT GUARDRAILS:
- You must ONLY answer questions related to agriculture, farming, weather, soil, and botany.
- If a user asks you to write code (like Python), scrape websites, or asks about non-agricultural topics, you MUST politely refuse and state that you are an agricultural assistant.
- Always use pdf_knowledge_base FIRST for any farming or agriculture question.
- Always use the most relevant tool before answering — do not guess.

Use your tools when necessary to find the most accurate and up-to-date information."""

# ==========================================
# 4. AGENT SETUP
# ==========================================

agent_executor = create_react_agent(llm, tools, prompt=system_prompt)

# ==========================================
# 5. MAIN FUNCTION EXPORT
# ==========================================

async def answer_question(user_input: str) -> dict:
    """Passes the input to the LangGraph agent and formats the output for FastAPI."""
    try:
        response = await agent_executor.ainvoke(
            {"messages": [("user", user_input)]}
        )

        messages = response.get("messages", [])
        final_output = messages[-1].content if messages else "No response generated."  

        # Extract tool usage steps for frontend display
        formatted_steps = []
        for msg in messages:
            if msg.type == "tool":
                formatted_steps.append([msg.name, msg.content])

        return {
            "output": final_output,
            "intermediate_steps": formatted_steps
        }
    except Exception as e:
        return {
            "output": f"I encountered an error while processing your request: {e}",
            "intermediate_steps": []
        }
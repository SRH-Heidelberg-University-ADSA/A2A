import os
import requests
import logging

logger = logging.getLogger("Discovery")


def get_cloud_registry():
    """
    Central source of truth for Cloud Agents.
    Each entry is a full Agent Card with capabilities and schemas,
    mirroring what an agent.json would contain.

    SCALABILITY: To add a new agent, simply add a new entry with the same
    structure. The call_config block tells the system HOW to invoke the agent.
    Supported protocols: "jsonrpc", "rest".
    """
    da_url = os.getenv("REMOTE_DATA_ANALYST_URL", "https://da-agent-2h3hgdmahq-uc.a.run.app/jsonrpc")

    return {
        "Data_Analyst": {
            "name": "Data_Analyst",
            "description": "An agent capable of performing deep data analysis on datasets.",
            "call_config": {
                "protocol": "jsonrpc",
                "url": da_url,
                "method": "analyze_dataset",
                "auth": {
                    "type": "bearer",
                    "env_var": "DS_AGENT_BEARER_TOKEN"
                },
            },
            "capabilities": [
                {
                    "name": "analyze_dataset",
                    "description": "Analyzes a given dataset and returns natural language insights.",
                    "input_schema": {
                        "properties": {
                            "data_payload": {"type": "string", "description": "Base64 encoded CSV data."},
                            "query": {"type": "string", "description": "Specific question to answer about the data."}
                        },
                        "required": ["data_payload"]
                    }
                }
            ],
            "path": "remote"
        },
        "Fitness_Agent": {
            "name": "Fitness_Agent",
            "description": "A specialized agent for fitness, workouts, and nutrition advice.",
            "call_config": {
                "protocol": "rest",
                "url": "https://fitness-agent-1084313087342.us-central1.run.app",
                "path": "/query",
                "auth": {
                    "type": "bearer",
                    "env_var": "FITNESS_AGENT_BEARER_TOKEN"
                },
            },
            "capabilities": [
                {
                    "name": "ask_fitness_agent",
                    "description": "Provides personalized workout plans, exercise routines, and nutrition guidance.",
                    "input_schema": {
                        "properties": {
                            "query": {"type": "string", "description": "The fitness-related question or request."}
                        },
                        "required": ["query"]
                    }
                }
            ],
            "path": "remote"
        },
        # ─────────────────────────────────────────────────────────────────
        # AGRICULTURE AGENT
        # ─────────────────────────────────────────────────────────────────
        # KEY: "Agriculture_Agent"
        #   → This is the LOOKUP KEY. The LLM uses this name to call
        #     delegate_task(target_agent_name="Agriculture_Agent", ...).
        #     It MUST match the dict key exactly.
        #
        # name: "Agriculture_Agent"
        #   → Display name. Must match the key so find_agent() works.
        #
        # call_config.url: The BASE URL of the agent (no endpoint path).
        #   → The path is specified SEPARATELY in call_config.path.
        #   → Final URL = url + path → "https://krishi-bot.../chat"
        #
        # call_config.path: "/chat"
        #   → The endpoint path appended to the base URL.
        #   → This agent's endpoint is /chat, NOT /query.
        #
        # capabilities: Must use "name" + "description" fields (not "tool"/"purpose")
        #   → These fields are what format_agent_card_for_llm() reads.
        #   → If you use wrong field names, the LLM won't see the capabilities.
        # ─────────────────────────────────────────────────────────────────
        "Agriculture_Agent": {
            "name": "Agriculture_Agent",
            "description": "A specialized agent for agriculture, weather forecasts, and soil data analysis (Krishi-Intel).",
            "call_config": {
                "protocol": "rest",
                "url": "https://krishi-bot-868711946656.us-central1.run.app",
                "path": "/chat",
                "auth": {
                    "type": "bearer",
                    "env_var": "AGRICULTURE_AGENT_BEARER_TOKEN"
                },
            },
            "capabilities": [
                {
                    "name": "check_weather",
                    "description": "Checks real-time weather conditions for agricultural planning.",
                    "input_schema": {
                        "properties": {
                            "query": {"type": "string", "description": "Weather-related question, e.g. 'What is the weather in Mumbai?'"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "check_soil",
                    "description": "Retrieves soil moisture and temperature data for farming decisions.",
                    "input_schema": {
                        "properties": {
                            "query": {"type": "string", "description": "Soil-related question, e.g. 'What is the soil moisture in Karnataka?'"}
                        },
                        "required": ["query"]
                    }
                }
            ],
            "path": "remote"
        },
        # ─────────────────────────────────────────────────────────────────
        # FOOTBALL REPORTER AGENT
        # ─────────────────────────────────────────────────────────────────
        # This agent has a DIFFERENT param format — it expects
        # "event_description" and "persona" instead of "query".
        #
        # call_config.param_mapping:
        #   → Tells delegate_task HOW to transform the task_query.
        #   → "query_field": "event_description" means the user's query
        #     gets sent as the "event_description" param.
        #   → "defaults": Static params always included (like persona).
        #
        # call_config.path: "" (empty string)
        #   → Because the full endpoint path is already in the URL.
        #   → url = "https://.../generate-tweet" — no extra path needed.
        # ─────────────────────────────────────────────────────────────────
        "Football_Reporter": {
            "name": "Football_Reporter",
            "description": "Analyzes football match events against official IFAB laws and generates viral social media posts.",
            "call_config": {
                "protocol": "rest",
                "url": "https://football-agent-qma0.onrender.com",
                "path": "/generate-tweet",
                "auth": {
                    "type": "header",
                    "header_name": "x-auth-token",
                    "env_var": "FOOTBALL_REPORTER_AUTH_TOKEN"
                },
                "param_mapping": {
                    "query_field": "event_description",
                    "defaults": {
                        "persona": "hype_man"
                    }
                }
            },
            "capabilities": [
                {
                    "name": "generate_tweet",
                    "description": "Takes a football match event description and generates a viral tweet with the official ruling. Supports personas: hype_man, angry_fan, analyst, gen_z.",
                    "input_schema": {
                        "properties": {
                            "event_description": {"type": "string", "description": "Description of the football event, e.g. 'The goalkeeper handled the ball outside the box.'"},
                            "persona": {"type": "string", "description": "Tweet persona style: hype_man, angry_fan, analyst, or gen_z."}
                        },
                        "required": ["event_description"]
                    }
                }
            ],
            "path": "remote"
        }
    }


def find_agent(target_agent_name: str, start_path: str = "."):
    """
    Search for an agent by name.
    1. Checks the Cloud Registry (always has full metadata).
    2. If an env var override exists, uses that URL but keeps registry metadata.
    """
    registry = get_cloud_registry()

    # Check registry first (has full metadata)
    agent = registry.get(target_agent_name)

    if agent:
        # Check for env var URL override — keeps all metadata, just swaps the endpoint
        env_var_name = f"REMOTE_{target_agent_name.upper()}_URL"
        remote_url = os.getenv(env_var_name)
        if remote_url:
            logger.info(f"Discovery: Using env override URL for '{target_agent_name}': {remote_url}")
            agent["call_config"]["url"] = remote_url

        logger.info(f"Discovery: Found '{target_agent_name}' in Cloud Registry.")
        return agent

    logger.warning(f"Discovery: Could not find agent '{target_agent_name}' in Cloud Registry.")
    return None


def get_all_agents(start_path: str = "."):
    """
    Returns a list of all available Cloud Agents (with full card data).
    """
    registry = get_cloud_registry()
    return list(registry.values())


def fetch_agent_card(agent_name: str) -> dict:
    """
    Fetches the full Agent Card for a given agent.
    1. Tries to fetch /agent.json from the agent's base URL (live discovery).
    2. Falls back to the embedded registry card if live fetch fails.
    Returns the full card with capabilities.
    """
    registry = get_cloud_registry()
    agent = registry.get(agent_name)

    if not agent:
        return None

    # Determine base URL (strip /jsonrpc or similar suffixes)
    base_url = agent["call_config"]["url"].rstrip("/")
    if base_url.endswith("/jsonrpc"):
        base_url = base_url[:-len("/jsonrpc")]

    # Try live fetch
    try:
        card_url = f"{base_url}/agent.json"
        logger.info(f"Discovery: Attempting live fetch of agent card from {card_url}")
        resp = requests.get(card_url, timeout=5)
        if resp.status_code == 200:
            live_card = resp.json()
            logger.info(f"Discovery: Live agent card fetched for '{agent_name}'")
            # Merge: keep registry call_config but use live capabilities
            # Ensure we keep the name if the live card doesn't provide it
            live_capabilities = live_card.get("capabilities", [])
            for i, cap in enumerate(live_capabilities):
                if not cap.get("name") and i < len(agent.get("capabilities", [])):
                    cap["name"] = agent["capabilities"][i].get("name")
                if not cap.get("description") and i < len(agent.get("capabilities", [])):
                    cap["description"] = agent["capabilities"][i].get("description")

            agent["capabilities"] = live_capabilities if live_capabilities else agent.get("capabilities", [])
            agent["description"] = live_card.get("description", agent.get("description", ""))
            return agent
    except Exception as e:
        logger.info(f"Discovery: Live fetch failed for '{agent_name}': {e}")

    # Fallback to embedded registry
    logger.info(f"Discovery: Using embedded agent card for '{agent_name}'")
    return agent


def format_agent_card_for_llm(agent: dict) -> str:
    """
    Formats an agent card into a readable string for the LLM prompt and trace.
    Shows capabilities with descriptions and input schemas.
    """
    lines = []
    lines.append(f"📋 **Agent: {agent['name']}**")
    lines.append(f"   Description: {agent.get('description', 'No description')}")

    capabilities = agent.get("capabilities", [])
    if capabilities:
        lines.append(f"   Capabilities ({len(capabilities)}):")
        for cap in capabilities:
            cap_name = cap.get('name') or cap.get('title') or 'unknown_action'
            cap_desc = cap.get('description') or cap.get('purpose') or 'No description available'
            lines.append(f"   - `{cap_name}`: {cap_desc}")
            schema = cap.get("input_schema", {})
            props = schema.get("properties", {})
            if props:
                required = schema.get("required", [])
                param_strs = []
                for pname, pinfo in props.items():
                    req_marker = " (required)" if pname in required else " (optional)"
                    param_strs.append(f"`{pname}` ({pinfo.get('type', '?')}){req_marker}: {pinfo.get('description', '')}")
                lines.append(f"     Input: {', '.join(param_strs)}")
    else:
        lines.append("   Capabilities: None listed")

    return "\n".join(lines)

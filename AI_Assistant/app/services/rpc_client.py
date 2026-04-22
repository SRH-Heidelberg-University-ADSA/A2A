import requests
import uuid
import logging
import os

logger = logging.getLogger("RPC_Client")

def call_agent(url: str, method: str, params: dict, auth_config: dict = None):
    """
    Make a JSON-RPC 2.0 call to a remote agent.
    Supports optional bearer token authentication via auth_config.
    """
    req_id = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": req_id
    }
    
    # Build auth headers if configured
    headers = {"Content-Type": "application/json"}
    if auth_config and auth_config.get("type") == "bearer":
        env_var = auth_config["env_var"]
        token = os.getenv(env_var, "")
        print(f"Auth DEBUG: env_var='{env_var}', token_found={bool(token)}, token_len={len(token)}")
        if token:
            headers["Authorization"] = f"Bearer {token}"
            logger.info(f"Auth: Including Bearer token from env var '{env_var}'")
            print(f"Auth: Bearer token included from '{env_var}'")
        else:
            logger.warning(f"Auth: env var '{env_var}' is not set — request may fail with 401!")
            print(f"Auth WARNING: env var '{env_var}' is NOT SET!")
    else:
        print(f"Auth DEBUG: No bearer auth config found. auth_config={auth_config}")
    
    logger.info(f"Sending RPC Request to {url} | Method={method} | ID={req_id}")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=300)
        response.raise_for_status()
        
        data = response.json()
        
        if "error" in data:
            logger.error(f"Remote error from {url}: {data['error']}")
            return {"status": "error", "error": data["error"]}
            
        logger.info(f"RPC Success | ID={req_id}")
        return {"status": "success", "result": data.get("result", {}).get("result")}
        
    except requests.exceptions.HTTPError as e:
        error_body = e.response.text if e.response is not None else ""
        logger.error(f"RPC HTTP Error {e.response.status_code if e.response is not None else ''} while contacting {url}: {e} | Body: {error_body}")
        return {"status": "error", "error": f"{str(e)} | Details: {error_body}"}
    except Exception as e:
        logger.error(f"RPC Exception while contacting {url}: {e}")
        return {"status": "error", "error": str(e)}

def call_agent_rest(base_url: str, path: str, params: dict, auth_config: dict = None):
    """
    Make a REST API call to a remote agent.
    Used for agents that expose REST endpoints instead of JSON-RPC.
    Supports optional header-based authentication via auth_config.
    """
    # Build URL
    url = base_url.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    url = url + path
    
    # Build auth headers if configured
    headers = {}
    if auth_config:
        auth_type = auth_config.get("type")
        if auth_type == "bearer":
            token = os.getenv(auth_config["env_var"], "")
            if token:
                headers["Authorization"] = f"Bearer {token}"
                logger.info(f"Auth: Including Bearer token from env var '{auth_config['env_var']}'")
            else:
                logger.warning(f"Auth: env var '{auth_config['env_var']}' is not set — request may fail with 401!")
        elif auth_type == "header":
            token = os.getenv(auth_config["env_var"], "")
            if token:
                headers[auth_config["header_name"]] = token
                logger.info(f"Auth: Including '{auth_config['header_name']}' header from env var '{auth_config['env_var']}'")
            else:
                logger.warning(f"Auth: env var '{auth_config['env_var']}' is not set — request may fail with 401!")
    
    logger.info(f"Sending REST Request to {url} | Params={list(params.keys())}")
    try:
        response = requests.post(url, json=params, headers=headers, timeout=300)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"REST Success from {url}")
        
        # REST agents typically return the result directly
        # Common patterns: {"response": "..."} or {"result": "..."}
        return {"status": "success", "result": data}
        
    except requests.exceptions.HTTPError as e:
        error_body = e.response.text if e.response is not None else ""
        logger.error(f"REST HTTP Error {e.response.status_code if e.response is not None else ''} while contacting {url}: {e} | Body: {error_body}")
        return {"status": "error", "error": f"{str(e)} | Details: {error_body}"}
    except Exception as e:
        logger.error(f"REST Exception while contacting {url}: {e}")
        return {"status": "error", "error": str(e)}

def call_agent_unified(call_config: dict, params: dict) -> dict:
    """
    Unified dispatcher: reads the agent's call_config and routes
    to the correct protocol handler (JSON-RPC or REST).
    This is the single entry point for all agent calls.
    """
    protocol = call_config.get("protocol", "jsonrpc")

    if protocol == "rest":
        url = call_config["url"]
        path = call_config.get("path", "/query")
        auth_config = call_config.get("auth")
        logger.info(f"Unified call: REST → {url}{path}")
        return call_agent_rest(url, path, params, auth_config)
    else:
        url = call_config["url"]
        method = call_config.get("method", "process_request")
        auth_config = call_config.get("auth")
        logger.info(f"Unified call: JSON-RPC → {url} method={method}")
        return call_agent(url, method, params, auth_config)

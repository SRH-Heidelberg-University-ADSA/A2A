import json
import ast

def extract_text_from_response(result) -> str:
    """
    Robustly parses and extracts text from an agent response, handling:
    - JSON strings
    - Python literal strings (single quotes)
    - Nested string encoding (double encoding)
    - List/Dict structures with various key patterns
    - Deduplication of repeated list items (Gemini quirk)
    """
    # RECURSIVE PARSE: Handle potential double-encoding (string inside string)
    # We loop max 3 times to prevent infinite loops
    for _ in range(3):
        if isinstance(result, str):
            result = result.strip()
            # If it's a simple string that doesn't look like JSON/List, stop
            if not (result.startswith("{") or result.startswith("[")):
                break
                
            try:
                # Try JSON
                result = json.loads(result)
                continue 
            except (json.JSONDecodeError, TypeError):
                pass
                
            try:
                # Try Python Literal
                result = ast.literal_eval(result)
                continue
            except (ValueError, SyntaxError, Exception):
                pass
        
        # If we get here, it's either not a string anymore, or we couldn't parse it further
        break
    
    # Handle list responses — deduplicate and extract
    if isinstance(result, list) and len(result) > 0:
        # Deduplicate: remove consecutive identical items (Gemini sometimes echoes)
        seen = []
        for item in result:
            item_str = str(item).strip()
            if item_str not in [str(s).strip() for s in seen]:
                seen.append(item)
        result = seen
        
        if len(result) == 1:
            # Single unique item — unwrap
            result = result[0]
        else:
            # Multiple unique items — join them
            parts = [_extract_from_single(item) for item in result]
            return "\n\n".join(parts)
    
    return _extract_from_single(result)


def _extract_from_single(result) -> str:
    """
    Extract readable text from a single dict or string result.
    Handles known response patterns from various agents.
    """
    output_text = result
    
    try:
        if isinstance(result, dict):
            # --- Pattern: Football Agent {ruling, tweet, persona_used} ---
            if "ruling" in result or "tweet" in result:
                parts = []
                if result.get("ruling"):
                    parts.append(result["ruling"])
                if result.get("tweet"):
                    parts.append(f"\nTWEET: {result['tweet']}")
                if result.get("persona_used"):
                    parts.append(f"PERSONA USED: {result['persona_used']}")
                return "\n".join(parts)
            
            # --- Common patterns: text, content, response, result ---
            for key in ("text", "content", "response", "result"):
                if key in result:
                    val = result[key]
                    # Skip if the value is just a status echo like "success"
                    if isinstance(val, str) and val.strip().lower() in ("success", "ok", ""):
                        continue
                    output_text = val
                    break
            else:
                # No known key matched — format dict as readable key-value pairs
                # Skip metadata keys like "status" 
                skip_keys = {"status", "status_code"}
                meaningful = {k: v for k, v in result.items() if k not in skip_keys and v}
                if meaningful:
                    parts = []
                    for k, v in meaningful.items():
                        label = k.upper().replace("_", " ")
                        parts.append(f"{label}: {v}")
                    return "\n".join(parts)
                    
    except Exception as e:
        print(f"Extraction error: {e}")
        
    # Final cleanup
    if not isinstance(output_text, str):
        output_text = str(output_text)
        
    return output_text


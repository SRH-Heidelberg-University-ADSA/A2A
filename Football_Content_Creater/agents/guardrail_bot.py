import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def validate_topic(user_query: str):
    """
    Acts as a security guard. 
    Returns: (is_allowed: bool, reason: str)
    """
    model = genai.GenerativeModel("gemini-2.5-flash") 
    

    prompt = f"""
    You are a Topic Validator for a Football (Soccer) App.
    
    USER QUERY: "{user_query}"
    
    TASK:
    Determine if this query is related to Football/Soccer, players, matches, or rules.
    - "How to make a burger" -> REJECT
    - "Who is Messi?" -> ALLOW
    - "Offside rule explanation" -> ALLOW
    - "Weather in London" -> REJECT
    
    OUTPUT FORMAT:
    Just one word: ALLOW or REJECT
    """
    
    try:
        response = model.generate_content(prompt)
        result = response.text.strip().upper()
        
        if "ALLOW" in result:
            return True, "Topic Validated."
        else:
            return False, "⚠️ Topic is not related to Football."
            
    except Exception as e:
       
        return False, f"Guardrail Error: {e}"

# Test Block
if __name__ == "__main__":
    print(validate_topic("How do I cook pasta?")) # Should be False
    print(validate_topic("Ronaldo penalty kick")) # Should be True
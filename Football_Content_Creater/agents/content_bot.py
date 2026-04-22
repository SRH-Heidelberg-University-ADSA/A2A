import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def load_personas():
    """
    Loads the personas from the JSON file in the main folder.
    """
    try:
        with open("personas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Emergency fallback if JSON is missing
        return {"default": {"name": "Default", "instructions": "Be professional and engaging."}}

def create_social_post(event: str, ruling_text: str, persona_key: str = "hype_man"):
    """
    Generates a tweet based on the event, the ruling, and the chosen persona.
    """
    # 1. Load the Persona Data
    personas = load_personas()
    
    # 2. Find the specific instructions (Safely handle missing keys)
    if persona_key in personas:
        persona_data = personas[persona_key]
    else:
        # If something goes wrong, pick the first one available
        persona_data = list(personas.values())[0]
    
    name = persona_data.get("name", "Bot")
    instructions = persona_data.get("instructions", "Write a viral tweet.")

    # 3. Generate Content
    model = genai.GenerativeModel("gemini-2.5-flash") 
    
    prompt = f"""
    You are a Social Media Manager for a top Sports Channel.
    
    CURRENT PERSONA: {name}
    STYLE INSTRUCTIONS: {instructions}
    
    THE EVENT: "{event}"
    THE OFFICIAL RULING: 
    {ruling_text}
    
    TASK:
    Write a short, viral tweet (max 280 chars) strictly following the STYLE INSTRUCTIONS above.
    """
    
    response = model.generate_content(prompt)
    return response.text
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_official_ruling(query: str):
    """
    Uses Google's File API to find the answer and citations.
    """
    file_uri = os.getenv("RULE_FILE_URI")
    
    # Retrieve the file object using the URI
    rule_book_file = genai.get_file(file_uri)

    
    model = genai.GenerativeModel("gemini-2.5-flash")

    print(f"\n🔎 RULES BOT: Searching PDF for '{query}'...")

    # Prompt with the File

    response = model.generate_content(
        [
            rule_book_file, 
            f"""
            You are a Football Referee Assistant.
            
            USER QUERY: {query}
            
            INSTRUCTIONS:
            1. Search the attached document for the answer.
            2. Extract the EXACT QUOTE and the specific LAW NUMBER/SECTION.
            3. If the event is an offence, state exactly why.
            
            OUTPUT FORMAT:
            VERDICT: [Goal/No Goal/Foul/Play On]
            REASONING: [Clear explanation]
            CITATION: [Exact Law Name & Section]
            QUOTE: "[Exact text from the book]"
            """
        ]
    )
    
    # Print citations to terminal as requested
    print("-" * 30)
    print("📜 TERMINAL CITATION OUTPUT:")
    print(response.text)
    print("-" * 30)
    
    return response.text

if __name__ == "__main__":
    print("\n🤖 RULES BOT: Interactive Mode Active")
    print("Type 'exit' to quit.\n")
    
    while True:
        # This line makes the terminal wait for you to type!
        user_input = input("⚽ Enter a match scenario: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting...")
            break
            
        if not user_input.strip():
            continue
            
        # Call the function with your input
        get_official_ruling(user_input)
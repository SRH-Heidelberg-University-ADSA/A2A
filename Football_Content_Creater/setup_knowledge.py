import os
import time
from dotenv import load_dotenv
import google.generativeai as genai

# 1. Setup
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def upload_pdf():
    pdf_path = "football_rules.pdf" 
    
    if not os.path.exists(pdf_path):
        print(f"❌ ERROR: Could not find {pdf_path}")
        return

    print(f"📤 Uploading {pdf_path} to Google AI Studio...")
    
    # Upload the file
    my_file = genai.upload_file(pdf_path, mime_type="application/pdf")
    
    # Wait for processing
    print(f"⏳ Processing '{my_file.display_name}'...")
    while my_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(2)
        my_file = genai.get_file(my_file.name)

    if my_file.state.name == "FAILED":
        print("❌ Upload failed.")
        return

    print("\n✅ SUCCESS! File is ready.")
    print("="*50)
    print(f"FILE NAME (URI): {my_file.name}")
    print("="*50)
    print("⚠️  COPY the 'FILE NAME' above (e.g., files/xxxxx)!")
    print("    You will paste it into your .env file as 'RULE_FILE_URI'.")

if __name__ == "__main__":
    upload_pdf()
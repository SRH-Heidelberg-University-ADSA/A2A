import os
import shutil
import pdfplumber
# Import core Document class
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
# --- NEW IMPORT: Hugging Face Local Embeddings ---
from langchain_huggingface import HuggingFaceEmbeddings
# Import ChromaDB vector database
from langchain_chroma import Chroma
# We don't need dotenv for embeddings anymore, as this runs locally!

# Define paths
PDF_FOLDER_PATH = "pdfs"
CHROMA_DB_PATH = "chroma_db"

# --- Metadata Definitions ---
FILE_METADATA = {
    "general_veg_guide_commercial.pdf": {
        "source": "Commercial Veg Guide",
        "type": "guidelines",
        "topics": ["vegetables", "commercial", "farming"]
    },
    "fruit_and_berry_guide.pdf": {
        "source": "Fruit & Berry Guide",
        "type": "guidelines",
        "topics": ["fruits", "berries", "orchard"]
    },
    "organic_production_manual.pdf": {
        "source": "Organic Manual",
        "type": "methodology",
        "topics": ["organic", "sustainable", "compost", "pests"]
    },
    "food_preservation_and_drying_guide.pdf": {
        "source": "Preservation Guide",
        "type": "processing",
        "topics": ["drying", "canning", "safety", "post-harvest"]
    }
}


def clean_metadata(metadata_dict):  #messy form 
    """
    ChromaDB cannot store lists in metadata.
    This function converts list values into comma-separated strings.
    """
    cleaned_metadata = {}
    for key, value in metadata_dict.items():
        if isinstance(value, list):
            # Convert list to "item1, item2, item3" string
            cleaned_metadata[key] = ", ".join(value)
        else:
            cleaned_metadata[key] = value
    return cleaned_metadata


def extract_text_from_pdf(pdf_path):
    """Helper function to open a PDF and pull out all the text page by page."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return None
    return text


def main():
    print("--- Starting Ingestion Process (Using Local Hugging Face) ---")
    print("Keep this terminal open.")

    
    if os.path.exists(CHROMA_DB_PATH):
        shutil.rmtree(CHROMA_DB_PATH)
        print(f"Cleared old database folder: {CHROMA_DB_PATH}")

    # 1. Setup Text Splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len, #  counts each character as 1 an dif it goes more than that it stops 
    
    )

    documents_to_embed = []

    # 2. Iterate through files in the pdfs folder
    if not os.path.exists(PDF_FOLDER_PATH): 
        print(f"ERROR: The folder '{PDF_FOLDER_PATH}' does not exist.")
        return

    print(f"\nSearching for PDFs in '{PDF_FOLDER_PATH}'...")
    files_found = [f for f in os.listdir(PDF_FOLDER_PATH) if f.endswith('.pdf')]  

    if not files_found:
         print("\nERROR: No .pdf files found.")
         return

    print(f"Found {len(files_found)} PDF files. Beginning processing...")

    for filename in files_found:
        file_path = os.path.join(PDF_FOLDER_PATH, filename) # giving the adress pdfs/organic.pdf
        print(f"\nReading file: {filename}")
        

        raw_text = extract_text_from_pdf(file_path)
        if not raw_text:
            print(f"Warning: Skipping {filename}...")
            continue

        # Determine metadata for this specific file from our dictionary
        raw_metadata = FILE_METADATA.get(filename, {"source": filename, "type": "general"})
        # --- FIX: Clean the metadata to remove lists ---
        this_file_metadata = clean_metadata(raw_metadata)

        texts = text_splitter.split_text(raw_text)
        print(f" - Split into {len(texts)} smaller knowledge chunks.")

        for text_chunk in texts:
            doc = Document(
                page_content=text_chunk,
                metadata=this_file_metadata
            )
            documents_to_embed.append(doc)

    if not documents_to_embed:
        print("\n No documents processed. Exiting.")
        return

    total_chunks = len(documents_to_embed)
    print(f"\n--- Embedding Process ---")
    print(f"Total distinct knowledge chunks to convert to vectors: {total_chunks}")

    # 3. Initialize Hugging Face Embeddings engine
    print("Initializing local embedding model (this may download the model first)...")
    try:
        # We use a specific, standard, high-quality small model.
        
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    except Exception as e:
        print(f"\nERROR: Could not initialize Hugging Face Embeddings. Error: {e}")
        return

    # 4. Create and save the Chroma database to disk
    print("Creating database. This happens locally on your CPU and may take a few minutes...")
    try:
        db = Chroma.from_documents(
            documents=documents_to_embed,
            embedding=embeddings,
            persist_directory=CHROMA_DB_PATH
        )
        print(f"\n--- SUCCESS ---")
        print(f"Knowledge base built and saved successfully to new folder: '/{CHROMA_DB_PATH}/'")
        print("Your PDFs are now ready for the AI agent using free local embeddings.")
    except Exception as e:
        print(f"\nERROR during database creation: {e}")


if __name__ == "__main__":
    main()
# rag_client.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

CHROMA_DB_PATH = "chroma_db"

def load_rag_client():
    # The dot means "look in the current folder"
    embeddings = HuggingFaceEmbeddings(
    model_name="./my_model")
    db = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embeddings)  # OPENING CHROMADB   it tis basicvally search engine that takes u r question 
    return db.as_retriever(search_kwargs={"k": 5})


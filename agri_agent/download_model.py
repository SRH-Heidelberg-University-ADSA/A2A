from sentence_transformers import SentenceTransformer
import os

# Create the folder if it doesn't exist
model_path = './my_model'
if not os.path.exists(model_path):
    os.makedirs(model_path) # Check if my_model/ folder exists — if it does not exist then create it — so the model has a place to be saved.

print("Downloading model... please wait.")
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save(model_path)
print(f"Model saved successfully to {model_path}") 
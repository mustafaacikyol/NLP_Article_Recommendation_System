from transformers import AutoTokenizer, AutoModel
import torch
import pymongo
import numpy as np

# Load the SciBERT pre-trained model and tokenizer
model_name = "allenai/scibert_scivocab_uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["article_recommendation"]
collection = db["user"]

# Function to generate SciBERT vector embeddings for a list of interests
def generate_scibert_embeddings(interests):
    embeddings = []
    for interest in interests:
        # Tokenize the interest and convert it to input IDs
        input_ids = tokenizer.encode(interest, add_special_tokens=True, truncation=True, max_length=128, return_tensors="pt")
        with torch.no_grad():
            # Get the model output for the input IDs
            outputs = model(input_ids)
            # Extract the output embeddings
            embeddings.append(torch.mean(outputs.last_hidden_state, dim=1).squeeze().numpy())
    return np.mean(embeddings, axis=0)

# Iterate through each document in the collection
for user in collection.find():
    academic_interests = user.get('academic_interests', [])
    if academic_interests:
        # Generate SciBERT vector embeddings for academic interests and calculate the average
        vector_embedding = generate_scibert_embeddings(academic_interests)
        
        # Update the document in the collection with the vector embeddings
        collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"scibert_vector_embedding": vector_embedding.tolist()}}
        )

print("Vector embeddings have been generated and inserted into the MongoDB collection.")

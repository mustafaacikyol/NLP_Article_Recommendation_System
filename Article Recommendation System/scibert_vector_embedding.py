import torch
from transformers import AutoTokenizer, AutoModel
from pymongo import MongoClient

# Load the SciBERT tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("allenai/scibert_scivocab_uncased")
model = AutoModel.from_pretrained("allenai/scibert_scivocab_uncased")

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['article_recommendation']
collection = db['article']

# Define a function to generate vector embeddings for a given text
def generate_embeddings(text):
    if not text.strip():  # Check if the text is empty or contains only whitespace
        return []  # Return an empty list if the text is empty
    
    # Tokenize the text
    tokens = tokenizer.tokenize(text)
    indexed_tokens = tokenizer.convert_tokens_to_ids(tokens)
    tokens_tensor = torch.tensor([indexed_tokens]).long()  # Convert to LongTensor
    
    # Get the output from the SciBERT model
    with torch.no_grad():
        outputs = model(tokens_tensor)
        hidden_states = outputs[0]  # Get the hidden states
        if hidden_states.size(1) == 0:  # Check if hidden states are empty
            return []  # Return an empty list if hidden states are empty
        pooled_output = hidden_states.mean(dim=1)  # Average pooling over all token embeddings
        flattened_embedding = pooled_output.flatten()  # Flatten the tensor
        
    return flattened_embedding.tolist()




# Iterate over each document in the collection and update it with vector embeddings
for document in collection.find():
    preprocessed_abstract = document['preprocessed_abstract']
    vector_embedding = generate_embeddings(preprocessed_abstract)
    collection.update_one({'_id': document['_id']}, {'$set': {'scibert_vector_embedding': vector_embedding}})

print("Finished!")
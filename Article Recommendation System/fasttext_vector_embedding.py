import spacy
from pymongo import MongoClient

# Load spaCy with FastText model
nlp = spacy.load("en_core_web_sm")  # or any other language model containing FastText embeddings

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['article_recommendation']
collection = db['article']

# Define a function to generate vector embeddings for a given text
def generate_embeddings(text):
    doc = nlp(text)
    return doc.vector.tolist()  # Convert spaCy's vector to a list

# Iterate over each document in the collection and update it with vector embeddings
for document in collection.find():
    preprocessed_abstract = document['preprocessed_abstract']
    vector_embedding = generate_embeddings(preprocessed_abstract)
    collection.update_one({'_id': document['_id']}, {'$set': {'vector_embedding': vector_embedding}})

import fasttext
import spacy
from pymongo import MongoClient

# Load the FastText model
fasttext_model_path = '../../cc.en.300.bin'  # Update this path with the path to your FastText model
fasttext_model = fasttext.load_model(fasttext_model_path)

# Load spaCy
nlp = spacy.blank("en")

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['article_recommendation']
collection = db['article']

# Define a function to generate vector embeddings for a given text
def generate_embeddings(text):
    # Tokenize the text
    tokens = nlp(text)
    # Get the vector for each token and average them to get the document vector
    vectors = [fasttext_model.get_word_vector(token.text) for token in tokens]
    if vectors:
        return [sum(col) / len(col) for col in zip(*vectors)]
    else:
        return []

# Iterate over each document in the collection and update it with vector embeddings
for document in collection.find():
    preprocessed_abstract = document['preprocessed_abstract']
    vector_embedding = generate_embeddings(preprocessed_abstract)
    collection.update_one({'_id': document['_id']}, {'$set': {'fasttext_vector_embedding': vector_embedding}})

print("Finished!")

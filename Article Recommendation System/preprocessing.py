import spacy
from spacy.lang.en.stop_words import STOP_WORDS
import string
from pymongo import MongoClient

# Load English tokenizer, tagger, parser, NER, and word vectors
nlp = spacy.load("en_core_web_sm")

# Function to preprocess the abstract
def preprocess_abstract(abstract):
    # Tokenize the abstract
    tokens = nlp(abstract.lower())
    
    # Remove stopwords and punctuation, and lemmatize the tokens
    processed_tokens = [token.lemma_ for token in tokens if token.text not in STOP_WORDS and token.text not in string.punctuation]
    
    # Join the processed tokens back into a string
    preprocessed_abstract = ' '.join(processed_tokens)
    
    return preprocessed_abstract

# Connect to MongoDB
client = MongoClient()  # Update with your MongoDB connection URI
db = client["article_recommendation"]  # Update with your database name
articles_collection = db["article"]  # Update with your collection name

# Retrieve articles from MongoDB
articles = articles_collection.find()

# Process each article
for article in articles:
    # Preprocess the abstract
    preprocessed_abstract = preprocess_abstract(article["abstract"])
    
    # Update the article in the collection with the preprocessed abstract
    articles_collection.update_one({"_id": article["_id"]}, {"$set": {"preprocessed_abstract": preprocessed_abstract}})

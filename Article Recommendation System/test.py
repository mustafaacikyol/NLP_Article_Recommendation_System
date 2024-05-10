import numpy as np
import pymongo
from bson import ObjectId

# Function to compute cosine similarity
def cosine_similarity(vector_a, vector_b):
    dot_product = np.dot(vector_a, vector_b)
    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)
    similarity = dot_product / (norm_a * norm_b)
    return similarity

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["article_recommendation"] 
user_collection = db["user"]
article_collection = db["article"]

    
# Function to find most similar articles
def find_most_similar_articles(user_embedding, collection_name, embedding_field):
    similar_articles = []
    for article in collection_name.find():
        article_embedding = np.array(article.get(embedding_field, []))
        if len(article_embedding) > 0:
            similarity = cosine_similarity(user_embedding, article_embedding)
            similar_articles.append((article, similarity))
    similar_articles.sort(key=lambda x: x[1], reverse=True)
    return similar_articles[:5]

# Function to recommend articles to user based on FastText vector
def recommend_articles_fasttext(user_id):
    user = user_collection.find_one({"_id": user_id})
    if user:
        user_embedding = np.array(user.get("fasttext_vector_embedding", []))
        if len(user_embedding) > 0:
            similar_articles = find_most_similar_articles(user_embedding, article_collection, "fasttext_vector_embedding")
            return similar_articles
    else:
        print("no user")
    return []

# Function to recommend articles to user based on SciBERT vector
def recommend_articles_scibert(user_id):
    user = user_collection.find_one({"_id": user_id})
    if user:
        user_embedding = np.array(user.get("scibert_vector_embedding", []))
        if len(user_embedding) > 0:
            similar_articles = find_most_similar_articles(user_embedding, article_collection, "scibert_vector_embedding")
            return similar_articles
    return []

# Example usage:
user_id = ObjectId("6632437ce21a8011d08ecb2c")  # Replace "user_id_here" with the actual user ID
similar_articles_fasttext = recommend_articles_fasttext(user_id)
similar_articles_scibert = recommend_articles_scibert(user_id)
print("Top 5 similar articles based on FastText vector:")
for article, similarity in similar_articles_fasttext:
    print(article["_id"], article["title"], similarity)
print("Top 5 similar articles based on SciBERT vector:")
for article, similarity in similar_articles_scibert:
    print(article["_id"], article["title"], similarity)

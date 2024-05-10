import fasttext
import pymongo
import numpy as np
import time

start_time = time.time()

model = fasttext.load_model('../../cc.en.300.bin')

end_time = time.time()
loading_time = end_time - start_time
print(loading_time)

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["article_recommendation"]
collection = db["user"]

# Function to generate FastText vector embeddings for a list of interests
def generate_fasttext_embeddings(interests):
    embeddings = []
    for interest in interests:
        embeddings.append(model.get_sentence_vector(interest))
    return np.mean(embeddings, axis=0)

# Iterate through each document in the collection
for user in collection.find():
    academic_interests = user.get('academic_interests', [])
    if academic_interests:
        # Generate FastText vector embeddings for academic interests and calculate the average
        vector_embedding = generate_fasttext_embeddings(academic_interests)
        
        # Update the document in the collection with the vector embeddings
        collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"fasttext_vector_embedding": vector_embedding.tolist()}}
        )

print("Vector embeddings have been generated and inserted into the MongoDB collection.")

from collections import Counter
import pymongo

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["article_recommendation"]
article_collection = db["article"]

# Function to find top 10 most occurring keywords
def top_20_keywords():
    # Initialize Counter to store keyword counts
    keyword_counter = Counter()

    # Iterate through each article in the collection
    for article in article_collection.find():
        # Get keywords from the article
        keywords = article.get('keywords', [])
        
        # Update counter with keywords
        keyword_counter.update(keywords)

    # Get top 10 most common keywords
    top_20 = keyword_counter.most_common(20)
    return top_20

# Get top 10 keywords
top_keywords = top_20_keywords()

# Print the results
print("Top 20 most occurring keywords:")
for keyword, count in top_keywords:
    print(f"{keyword}: {count}")

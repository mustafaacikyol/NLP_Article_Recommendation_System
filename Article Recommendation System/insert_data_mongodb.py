import json
from pymongo import MongoClient
import os

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['article_recommendation']
collection = db['article']

# Define the directory where the JSON files are located
directory = 'dataset/'

# Function to insert data from a JSON file
def insert_data_from_json(file_path):
    with open(file_path, 'r') as file:
        # Iterate over each line in the file
        for line in file:
            # Load each line as JSON
            entry = json.loads(line)

            # Extract required fields
            title = entry.get('title', '')
            abstract = entry.get('abstract', '')
            keywords_str = entry.get('keywords', '')

            # Split keywords string into a list of keywords
            keywords = keywords_str.split(';') if keywords_str else []

            # Prepare document to insert into MongoDB
            document = {
                'title': title,
                'abstract': abstract,
                'keywords': keywords
            }

            # Insert document into MongoDB
            collection.insert_one(document)

# Insert data from valid.json
valid_file_path = os.path.join(directory, 'valid.json')
insert_data_from_json(valid_file_path)
print("Data from valid.json inserted into MongoDB.")

# Insert data from test.json
test_file_path = os.path.join(directory, 'test.json')
insert_data_from_json(test_file_path)
print("Data from test.json inserted into MongoDB.")

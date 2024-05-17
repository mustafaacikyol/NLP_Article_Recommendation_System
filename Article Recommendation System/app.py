from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import numpy as np
from math import ceil
import re  # Import the re module for regular expressions
from bson.regex import Regex
import fasttext
from transformers import AutoTokenizer, AutoModel
import torch

app = Flask(__name__)
app.secret_key = '123456789'  # Set a secret key for session management

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['article_recommendation']
user_collection = db['user']
article_collection = db["article"]

fasttext_model = fasttext.load_model('../../cc.en.300.bin')

# Load the SciBERT pre-trained model and tokenizer
model_name = "allenai/scibert_scivocab_uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
scibert_model = AutoModel.from_pretrained(model_name)

@app.route('/login', methods=['GET', 'POST'])
def login():
    feedback = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Query MongoDB for user with provided username and password
        user = user_collection.find_one({'username': username, 'password': password})
        
        if user:
            # Store user information in session
            session['id'] = str(user["_id"])  # Convert ObjectId to string
            session['username'] = user['username']
            # session['name'] = user['name']
            # session['surname'] = user['surname']

            # Redirect user to a protected page after login
            return redirect('/dashboard')  # Example: Redirect to dashboard after login
        else:
            feedback = "Wrong username or password!"
    return render_template('login.html', feedback = feedback)

@app.route('/signup', methods=['GET','POST'])
def signup():
    feedback = ""
    if request.method == 'POST':
        # Parse form data
        name = request.form['name']
        surname = request.form['surname']
        gender = request.form['gender']
        birth_date = request.form['birth-date']
        education_level = request.form['education-level']
        academic_interests = request.form.getlist('academic-interest[]')
        email = request.form["email"]
        username = request.form['username']
        password = request.form['password']

        # Generate FastText vector embeddings for academic interests and calculate the average
        fasttext_vector_embedding = generate_fasttext_embeddings(academic_interests)
        scibert_vector_embedding = generate_scibert_embeddings(academic_interests)

        # Create a new user document
        new_user = {
            'name': name,
            'surname': surname,
            'gender': gender,
            'birth_date': birth_date,
            'education_level': education_level,
            'academic_interests': academic_interests,
            'email' : email,
            'username': username,
            'password': password,
            'fasttext_vector_embedding': fasttext_vector_embedding.tolist(),
            'scibert_vector_embedding' : scibert_vector_embedding.tolist()
        }

        # Insert the user document into MongoDB
        result = user_collection.insert_one(new_user)

        if result.inserted_id:
            return redirect('/login')
        else:
            feedback = "Failed to register user!"

    return render_template('signup.html', feedback = feedback)

def generate_fasttext_embeddings(interests):
    embeddings = []
    for interest in interests:
        embeddings.append(fasttext_model.get_sentence_vector(interest))
    return np.mean(embeddings, axis=0)

# Function to generate SciBERT vector embeddings for a list of interests
def generate_scibert_embeddings(interests):
    embeddings = []
    for interest in interests:
        # Tokenize the interest and convert it to input IDs
        input_ids = tokenizer.encode(interest, add_special_tokens=True, truncation=True, max_length=128, return_tensors="pt")
        with torch.no_grad():
            # Get the model output for the input IDs
            outputs = scibert_model(input_ids)
            # Extract the output embeddings
            embeddings.append(torch.mean(outputs.last_hidden_state, dim=1).squeeze().numpy())
    return np.mean(embeddings, axis=0)

@app.route('/update_fasttext_liked_articles', methods=['POST'])
def update_fasttext_liked_articles():
    fasttext_liked_article_ids = request.json.get('liked_articles')
    fasttext_vector_embeddings = []

    user_id = session.get('id')
    user = user_collection.find_one({'_id': ObjectId(user_id)})

    for article_id in fasttext_liked_article_ids:
        article = article_collection.find_one({'_id': ObjectId(article_id)})
        if article and 'fasttext_vector_embedding' in article:
            fasttext_vector_embeddings.append(article['fasttext_vector_embedding'])

    # Calculate the average fasttext_vector_embedding using NumPy
    if fasttext_vector_embeddings:
        average_embedding = np.mean(fasttext_vector_embeddings, axis=0)

        # Update the user's fasttext_vector_embedding
        user_embedding = np.array(user['fasttext_vector_embedding'])
        new_user_embedding = (user_embedding + average_embedding) / 2  # Calculate the average
        user_collection.update_one({'_id': user['_id']}, {'$set': {'fasttext_vector_embedding': new_user_embedding.tolist()}})

        return jsonify({"message": "FastText liked articles processed successfully"})
    else:
        return jsonify({"message": "No FastText liked articles found"})

@app.route('/update_scibert_liked_articles', methods=['POST'])
def update_scibert_liked_articles():
    scibert_liked_article_ids = request.json.get('liked_articles')
    scibert_vector_embeddings = []

    user_id = session.get('id')
    user = user_collection.find_one({'_id': ObjectId(user_id)})

    for article_id in scibert_liked_article_ids:
        article = article_collection.find_one({'_id': ObjectId(article_id)})
        if article and 'scibert_vector_embedding' in article:
            scibert_vector_embeddings.append(article['scibert_vector_embedding'])

    # Calculate the average fasttext_vector_embedding using NumPy
    if scibert_vector_embeddings:
        average_embedding = np.mean(scibert_vector_embeddings, axis=0)

        # Update the user's fasttext_vector_embedding
        user_embedding = np.array(user['scibert_vector_embedding'])
        new_user_embedding = (user_embedding + average_embedding) / 2  # Calculate the average
        user_collection.update_one({'_id': user['_id']}, {'$set': {'scibert_vector_embedding': new_user_embedding.tolist()}})

        return jsonify({"message": "FastText liked articles processed successfully"})
    else:
        return jsonify({"message": "No FastText liked articles found"})

similar_articles_fasttext = []
similar_articles_scibert = []

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    flag = request.args.get('flag')
    # Check if user is logged in
    if 'username' in session:
        # Retrieve user ID from session
        user_id = session.get('id')
        # Query MongoDB for user data using the user ID
        user = user_collection.find_one({'_id': ObjectId(user_id)})
        global similar_articles_fasttext
        global similar_articles_scibert
        if(flag == None):
            similar_articles_fasttext = recommend_articles_fasttext(ObjectId(user_id))
            similar_articles_scibert = recommend_articles_scibert(ObjectId(user_id))

            # Get article IDs from the similar articles lists
            fasttext_article_ids = [str(article[0]['_id']) for article in similar_articles_fasttext]
            scibert_article_ids = [str(article[0]['_id']) for article in similar_articles_scibert]

            # Update user_collection with the new article IDs by adding them to the existing lists
            user_collection.update_one({'_id': ObjectId(user_id)}, {'$addToSet': {'fasttext_displayed_articles': {'$each': fasttext_article_ids}, 'scibert_displayed_articles': {'$each': scibert_article_ids}}})

            return render_template('dashboard.html', user=user, similar_articles_fasttext=similar_articles_fasttext, similar_articles_scibert=similar_articles_scibert)
        elif(flag == 'fasttext'):
            similar_articles_fasttext = recommend_articles_fasttext(ObjectId(user_id))
            fasttext_article_ids = [str(article[0]['_id']) for article in similar_articles_fasttext]
            user_collection.update_one({'_id': ObjectId(user_id)}, {'$addToSet': {'fasttext_displayed_articles': {'$each': fasttext_article_ids}}})
            return render_template('dashboard.html', user=user, similar_articles_fasttext=similar_articles_fasttext, similar_articles_scibert=similar_articles_scibert)
        elif(flag == 'scibert'):
            similar_articles_scibert = recommend_articles_scibert(ObjectId(user_id))
            scibert_article_ids = [str(article[0]['_id']) for article in similar_articles_scibert]
            user_collection.update_one({'_id': ObjectId(user_id)}, {'$addToSet': {'scibert_displayed_articles': {'$each': scibert_article_ids}}})
            return render_template('dashboard.html', user=user, similar_articles_fasttext=similar_articles_fasttext, similar_articles_scibert=similar_articles_scibert)
    # User is not logged in, redirect to login page
    return redirect('/login')

# Function to compute cosine similarity
def cosine_similarity(vector_a, vector_b):
    dot_product = np.dot(vector_a, vector_b)
    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)
    similarity = dot_product / (norm_a * norm_b)
    return similarity

# Function to find most similar articles that haven't been displayed to the user before
def find_most_similar_articles(user_embedding, collection_name, embedding_field, displayed_articles):
    similar_articles = []
    for article in collection_name.find():
        article_id = str(article['_id'])
        # Check if the article has been displayed to the user before
        if article_id in displayed_articles:
            continue  # Skip this article if it has been displayed before
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
        displayed_articles = user.get("fasttext_displayed_articles", [])
        if len(user_embedding) > 0:
            similar_articles = find_most_similar_articles(user_embedding, article_collection, "fasttext_vector_embedding", displayed_articles)
            return similar_articles
    return []

# Function to recommend articles to user based on SciBERT vector
def recommend_articles_scibert(user_id):
    user = user_collection.find_one({"_id": user_id})
    if user:
        user_embedding = np.array(user.get("scibert_vector_embedding", []))
        displayed_articles = user.get("scibert_displayed_articles", [])
        if len(user_embedding) > 0:
            similar_articles = find_most_similar_articles(user_embedding, article_collection, "scibert_vector_embedding", displayed_articles)
            return similar_articles
    return []

@app.route('/profile-information', methods=['GET','POST'])
def profile_information():
    # Check if user is logged in
    if 'username' in session:
        # Retrieve user ID from session
        user_id = session.get('id')

        # Query MongoDB for user data using the user ID
        user = user_collection.find_one({'_id': ObjectId(user_id)})

        if user:
            # Parse birthdate from MongoDB document
            birthdate_str = user['birth_date']
            birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").strftime("%d/%m/%Y")
            user['birth_date'] = birthdate

            # Convert academic interests list to comma-separated string
            academic_interests = user.get('academic_interests', [])
            academic_interests_str = ', '.join(academic_interests)
           
            user['academic_interests'] = academic_interests_str

            # If user data is found, render profile information page
            return render_template('/profile-information.html', user=user)
    else:
        # User is not logged in, redirect to login page
        return redirect('/login')
  
@app.route('/update-profile', methods=['GET', 'POST'])
def update_profile():
    # Check if user is logged in
    if 'username' in session:
        # Retrieve user ID from session
        user_id = session.get('id')

        # Query MongoDB for user data using the user ID
        user = user_collection.find_one({'_id': ObjectId(user_id)})

        if user:
            if request.method == 'POST':
                # Update user data based on the submitted form
                user['name'] = request.form['name']
                user['surname'] = request.form['surname']
                user['gender'] = request.form['gender']
                user['birth_date'] = request.form['birth-date']
                user['education_level'] = request.form['education-level']
                user['academic_interests'] = request.form.getlist('academic-interest[]')
                user['email'] = request.form['email']
                user['username'] = request.form['username']

                # Update user data in the MongoDB database
                user_collection.update_one({'_id': ObjectId(user_id)}, {'$set': user})

                # Redirect to the profile information page after update
                return redirect(url_for('profile_information'))

            # Render the update-profile page with user's data pre-filled in the form fields
            return render_template('update-profile.html', user=user)
    else:
        # User is not logged in, redirect to login page
        return redirect('/login')
    
@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    # Check if user is logged in
    if 'username' in session:
        # Retrieve user ID from session
        user_id = session.get('id')

        # Query MongoDB for user data using the user ID
        user = user_collection.find_one({'_id': ObjectId(user_id)})

        if user:
            if request.method == 'POST':
                # Update user data based on the submitted form
                user['password'] = request.form['password']

                # Update user data in the MongoDB database
                user_collection.update_one({'_id': ObjectId(user_id)}, {'$set': user})

                # Redirect to the profile information page after update
                return redirect(url_for('profile_information'))

            # Render the update-profile page with user's data pre-filled in the form fields
            return render_template('change-password.html', user=user)
    else:
        # User is not logged in, redirect to login page
        return redirect('/login')
    
@app.route('/articles', methods=['GET', 'POST'])
def articles():
    # Check if user is logged in
    if 'username' in session:
        # Retrieve user ID from session
        user_id = session.get('id')

        # Query MongoDB for user data using the user ID
        user = user_collection.find_one({'_id': ObjectId(user_id)})

        # Retrieve articles from MongoDB including _id
        articles = article_collection.find({}, {'_id': 1, 'title': 1, 'abstract': 1})

        # Pagination
        total_articles = articles.count()
        articles_per_page = 100
        total_pages = ceil(total_articles / articles_per_page)
        page = int(request.args.get('page', 1))
        articles = articles.skip((page - 1) * articles_per_page).limit(articles_per_page)

        # User is logged in, render articles page with user data and articles
        return render_template('articles.html', user=user, articles=articles, page=page, total_pages=total_pages)
    else:
        # User is not logged in, redirect to login page
        return redirect('/login')

@app.route('/article-detail', methods=['GET', 'POST'])
def article_detail():
    # Check if user is logged in
    if 'username' in session:
        # Retrieve user ID from session
        user_id = session.get('id')
        article_id = request.args.get('id')

        # Query MongoDB for user data using the user ID
        user = user_collection.find_one({'_id': ObjectId(user_id)})

        # Retrieve the article details based on the provided article_id
        article = article_collection.find_one({'_id': ObjectId(article_id)})

        # Convert academic interests list to comma-separated string
        keywords = article.get('keywords', [])
        keywords_str = ', '.join(keywords)
        
        article['keywords'] = keywords_str

        # User is logged in, render articles page with user data and articles
        return render_template('article-detail.html', user=user, article=article)
    else:
        # User is not logged in, redirect to login page
        return redirect('/login')

@app.route('/search', methods=['GET', 'POST'])
def search():
    # Check if user is logged in
    if 'username' in session:
        # Retrieve user ID from session
        user_id = session.get('id')
        
        # Query MongoDB for user data using the user ID
        user = user_collection.find_one({'_id': ObjectId(user_id)})

        if request.method == 'POST':
            query = request.form["query"]

            # Ensure query is a string
            query = str(query)

            # Construct regex pattern for case-insensitive search
            regex_pattern = Regex("^" + re.escape(query), "i")

            # Query MongoDB for articles that match the search query
            articles = article_collection.find({'keywords': {'$regex': regex_pattern}})

            # Count the number of articles found
            num_articles = articles.count()

            # Render the search results page with matching articles
            return render_template('search.html', user=user, articles=articles, num_articles=num_articles, query=query)
        else:
            return render_template('search.html', user=user)
        
    else:
        # User is not logged in, redirect to login page
        return redirect('/login')

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    # Redirect to the login page
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
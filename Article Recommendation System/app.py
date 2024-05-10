from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import numpy as np

app = Flask(__name__)
app.secret_key = '123456789'  # Set a secret key for session management

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['article_recommendation']
user_collection = db['user']
article_collection = db["article"]


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
            'password': password
        }

        # Insert the user document into MongoDB
        result = user_collection.insert_one(new_user)

        if result.inserted_id:
            return redirect('/login')
        else:
            feedback = "Failed to register user!"

    return render_template('signup.html', feedback = feedback)

@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    # Check if user is logged in
    if 'username' in session:
        # Retrieve user ID from session
        user_id = session.get('id')

        similar_articles_fasttext = recommend_articles_fasttext(ObjectId(user_id))
        similar_articles_scibert = recommend_articles_scibert(ObjectId(user_id))

        # Query MongoDB for user data using the user ID
        user = user_collection.find_one({'_id': ObjectId(user_id)})

        # User is logged in, render dashboard
        return render_template('dashboard.html', user=user, similar_articles_fasttext=similar_articles_fasttext, similar_articles_scibert=similar_articles_scibert)
    else:
        # User is not logged in, redirect to login page
        return redirect('/login')
    
# Function to compute cosine similarity
def cosine_similarity(vector_a, vector_b):
    dot_product = np.dot(vector_a, vector_b)
    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)
    similarity = dot_product / (norm_a * norm_b)
    return similarity

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
    
@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    # Redirect to the login page
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
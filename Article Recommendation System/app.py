from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = '123456789'  # Set a secret key for session management

# Connect to MongoDB
client = MongoClient()
db = client['article_recommendation']
users_collection = db['user']

@app.route('/login', methods=['GET', 'POST'])
def login():
    feedback = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Query MongoDB for user with provided username and password
        user = users_collection.find_one({'username': username, 'password': password})
        
        if user:
            # Store user information in session
            session['id'] = str(user["_id"])  # Convert ObjectId to string
            # session['username'] = user['username']
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
        result = users_collection.insert_one(new_user)

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

        # Query MongoDB for user data using the user ID
        user = users_collection.find_one({'_id': ObjectId(user_id)})

        # User is logged in, render dashboard
        return render_template('dashboard.html', user=user)
    else:
        # User is not logged in, redirect to login page
        return redirect('/login')
    
@app.route('/profile-information', methods=['GET','POST'])
def profile_information():
    # Check if user is logged in
    if 'username' in session:
        # Retrieve user ID from session
        user_id = session.get('id')

        # Query MongoDB for user data using the user ID
        user = users_collection.find_one({'_id': ObjectId(user_id)})

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
        user = users_collection.find_one({'_id': ObjectId(user_id)})

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
                users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': user})

                # Redirect to the profile information page after update
                return redirect(url_for('profile_information'))

            # Render the update-profile page with user's data pre-filled in the form fields
            return render_template('update-profile.html', user=user)
    else:
        # User is not logged in, redirect to login page
        return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
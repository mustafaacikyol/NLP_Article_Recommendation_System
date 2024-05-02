from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient

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
            session['username'] = user['username']
            session['name'] = user['name']
            session['surname'] = user['surname']
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
        # User is logged in, render dashboard
        return render_template('dashboard.html', username=session['username'], name=session['name'], surname=session['surname'])
    else:
        # User is not logged in, redirect to login page
        return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
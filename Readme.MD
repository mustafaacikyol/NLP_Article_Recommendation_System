## Article Recommendation System
The project is a system that provides personalized article recommendations based on users' interests and reading history. The main goal of the project is to direct users to the right articles of their interest.  
#### Project Requirements
1. Data Source
A ready-made article dataset will be used. Example ready-made dataset: Inspec and Krapivin2009.  
2. Preprocessing and Data Analysis
Pre-processing of articles with NLP (Natural Language Processing) techniques.  
Text preprocessing with NLP tools: It will be done in Python using either NLTK or spaCy libraries.  
Pre-processing methods to be done: Cleaning English stopwords (ready-made stop words lists will be used for this), removing punctuation marks, finding word roots.  
Creation of vector embeddings for articles and user profile using FastText and SCIBERT models.  
The vector representation for the user profile should be created by averaging the vector representations of all the interests of a user.  
The vectors of interest are evaluated for similarity and 5 proposals are expected to be submitted separately for FastText and SCIBERT vector representations.  
Article-user similarity will be calculated with the Cosine Similarity metric.  
Performance evaluation of the suggestions made: Precision should be calculated. Evaluation results should be shown in the interface.  
3. Creating and Managing User Profiles
User Login: An interface should be designed for users to register to the system.  
In the interface, first of all, the membership process must be done to log in to the system.  
The user's demographic information as well as the user's academic interests should be obtained through the membership form.  
Profile Management: Creating, updating and managing user profiles.  
4. Recommendation Engine
Starter Suggestions: These should be based on the interests the user has indicated when creating a membership. Subsequent recommendations should be dynamically updated based on the user's interests and reading history.  
Personalized Recommendations: Recommendations should be dynamically updated based on the user's past interactions.  
Feedback System: Collecting user feedback and updating the model accordingly: The user is expected to give feedback to the system as appropriate or not for each of the 5 suggestions presented to the user with FastText and SCIBERT.  
The next recommendation should be determined by including the article(s) that the user has marked as being of interest.  
5. User Interface
Frontend Development: There are no language restrictions for a user-friendly web interface.  
Search Functions: A search bar should be created where users can easily find the articles they are looking for(keywords).  
6. Technologies to be used
Since the application will be a web project, you need to use a suitable database to synchronize the data and run the algorithms. The example database is MongoDB.  
Artificial Intelligence and Machine Learning: Python

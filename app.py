from flask import Flask, render_template, request, redirect, url_for, flash, session
import numpy as np
from tensorflow.keras.preprocessing import image
import json
import tensorflow as tf
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load your trained model
model = tf.keras.models.load_model('skin_disease_model.keras')

# Load user data from a JSON file
def load_users():
    try:
        with open('users.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Save user data to a JSON file
def save_users(users):
    with open('users.json', 'w') as file:
        json.dump(users, file)

# Preprocess image to match the model input
def preprocess_image(file):
    # Read the file into a bytes object
    img_bytes = file.read()
    # Use io.BytesIO to convert bytes into a file-like object
    img_file = io.BytesIO(img_bytes)
    # Load the image using the file-like object
    img = image.load_img(img_file, target_size=(128, 128))  # Ensure the image is resized correctly
    img_array = image.img_to_array(img)  # Convert image to array
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
    img_array /= 255.0  # Normalize
    return img_array

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user-login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        for user in users:
            if user['username'] == username and user['password'] == password:
                session['username'] = username  # Store username in session
                return redirect(url_for('upload_image'))
        flash('Invalid username or password!')
    return render_template('user-login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        users = load_users()
        users.append({'username': username, 'email': email, 'password': password, 'disease': None})  # Added disease field
        save_users(users)
        flash('Registration successful! Please log in.')
        return redirect(url_for('user_login'))
    return render_template('user-registration.html')

@app.route('/upload-image', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        # Retrieve the uploaded image
        file = request.files['file']
        
        # Preprocess the image for model prediction
        img = preprocess_image(file)
        
        # Make prediction
        predictions = model.predict(img)
        predicted_class = np.argmax(predictions, axis=1)[0]  # Get the index of the highest prediction
        
        # Calculate accuracy (confidence)
        accuracy = np.max(predictions) * 100  # Convert to percentage
        
        # Define class labels (same order as in your model's training)
        class_labels = [
            'Acne and Rosacea Photos',
            'Actinic Keratosis Basal Cell Carcinoma and other Malignant Lesions',
            'Atopic Dermatitis Photos',
            'Bullous Disease Photos',
            'Eczema Photos',
            'Melanoma Skin Cancer Nevi and Moles',
            'Urticaria Hives'
        ]
        
        # Get the predicted disease name
        disease = class_labels[predicted_class]
        
        # Update the user's disease in the JSON file
        update_user_disease(session['username'], disease)
        
        # Render the result page with the predicted disease and accuracy
        return render_template('result.html', disease=disease, accuracy=accuracy)
    
    return render_template('upload-image.html')

def update_user_disease(username, disease):
    users = load_users()
    for user in users:
        if user['username'] == username:
            user['disease'] = disease  # Update the disease field
            break
    save_users(users)

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'Prathmesh' and password == '098765':
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials!')
    return render_template('admin-login.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    users = load_users()
    return render_template('admin-dashboard.html', users=users)

@app.route('/delete-user/<username>', methods=['POST'])
def delete_user(username):
    users = load_users()
    users = [user for user in users if user['username'] != username]
    save_users(users)
    return redirect(url_for('admin_dashboard'))

@app.route('/view-doctor')  # Make sure the route is correct
def view_doctors():
    # List of doctors with random names, genders, skin diseases, and contact numbers
    doctors = [
        {'name': 'Dr. John Doe', 'gender': 'Male', 'disease': 'Acne', 'contact': '(123) 456-7890'},
        {'name': 'Dr. Jane Smith', 'gender': 'Female', 'disease': 'Eczema', 'contact': '(234) 567-8901'},
        {'name': 'Dr. Alice Johnson', 'gender': 'Female', 'disease': 'Bullous Disease Photos', 'contact': '(345) 678-9012'},
        {'name': 'Dr. Bob Brown', 'gender': 'Male', 'disease': 'Atopic Dermatitis Photos', 'contact': '(456) 789-0123'},
        {'name': 'Dr. Emily Davis', 'gender': 'Female', 'disease': 'Rosacea', 'contact': '(567) 890-1234'},
        {'name': 'Dr. Michael Wilson', 'gender': 'Male', 'disease': 'Melanoma Skin Cancer Nevi', 'contact': '(678) 901-2345'},
        {'name': 'Dr. Sarah Moore', 'gender': 'Female', 'disease': 'Urticaria Hives', 'contact': '(789) 012-3456'},
    ]
    return render_template('view_doctor.html', doctors=doctors)  # Use the correct template name

if __name__ == '__main__':
    app.run(debug=True)

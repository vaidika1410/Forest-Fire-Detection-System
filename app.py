from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
import os
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from flask import redirect, session, url_for

import datetime
results_list = []  # In-memory storage of results


from functools import wraps
from flask import session, redirect, url_for, request, make_response

from functools import wraps
from flask import session, redirect, url_for, make_response

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        
        response = make_response(f(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return decorated_function



app = Flask(__name__)
app.secret_key = 'your_secret_key'

from flask import make_response

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response


# Load the model once
model = load_model('model/ForestFireDetection(2).keras')
class_names = ['No Fire', 'Fire']

# Ensure uploads directory exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Accept any username, just validate password
        if password == 'admin':
            session['username'] = username  # Save typed username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')





@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))


    prediction_result = None
    uploaded_filename = None

    if request.method == 'POST':
        file = request.files['image']
        if file:
            uploaded_filename = file.filename
            filepath = os.path.join(UPLOAD_FOLDER, uploaded_filename)
            file.save(filepath)

            # Prepare image
            img = image.load_img(filepath, target_size=(150, 150))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array /= 255.0

            # Predict
            prediction = model.predict(img_array)
            prob = prediction[0][0]
            predicted_class = class_names[int(prob > 0.5)]
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            prediction_result = f"Prediction: {predicted_class}"

            # Save to results list
            results_list.append({
                'filename': file.filename,
                'prediction': predicted_class,
                'confidence': f"{prob:.2f}",
                'time': timestamp
            })

            print(prediction_result)
            print("Raw output:", prediction)


            # Getting all uploaded images
            uploaded_files = os.listdir('uploads')
            uploaded_files = sorted(uploaded_files, reverse=True)


    return render_template('index.html',
                           username=session.get('username'),
                           prediction=prediction_result,
                           image_path=uploaded_filename)


@app.route('/uploads-page')
@login_required
def uploads_page():
    if 'username' not in session:
        return redirect(url_for('login'))

    uploaded_files = sorted(os.listdir('uploads'), reverse=True)
    return render_template('uploads.html', username=session.get('username'), uploaded_files=uploaded_files)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))

    filepath = os.path.join('uploads', filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for('uploads_page'))


@app.route('/results')
@login_required
def results():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('results.html', username=session['username'], results=results_list)




@app.route('/logout')
def logout():
    session.pop('username', None)
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


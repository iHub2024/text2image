import os
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
import base64
from io import BytesIO
from PIL import Image
import zipfile
import datetime
import shutil

app = Flask(__name__)

UPLOAD_FOLDER = 'static/captured_images'
ZIP_FOLDER = 'static/zip_files'
TXT_FOLDER = 'static/captured_texts'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ZIP_FOLDER'] = ZIP_FOLDER
app.config['TXT_FOLDER'] = TXT_FOLDER

for folder in [UPLOAD_FOLDER, ZIP_FOLDER, TXT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload-excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'message': 'No selected file'})
    
    if file:
        df = pd.read_excel(file, engine='openpyxl')
        content_list = df.to_dict(orient='records')
        return jsonify({'message': 'File uploaded successfully', 'content': content_list})

@app.route('/capture-page', methods=['POST'])
def capture_page():
    data_url = request.json.get('imageData')
    index = request.json.get('index')
    text = request.json.get('text')

    # Save the image with a sequential filename (1.jpg, 2.jpg, etc.)
    filename = f'{index + 1}.jpg'
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Decode the base64-encoded image and save as jpg
    image_data = base64.b64decode(data_url.split(',')[1])
    image = Image.open(BytesIO(image_data)).convert('RGB')  # Ensure image is RGB for jpg
    image.save(image_path, 'JPEG')

    # Append the text content to the single text file
    txt_filename = 'all_captured_content.txt'
    txt_path = os.path.join(app.config['TXT_FOLDER'], txt_filename)
    with open(txt_path, 'a') as f:
        f.write(f'{filename} {text}\n')  # Append filename and content to the single text file
    
    return jsonify({'message': 'Image and text recorded successfully!', 'image_path': image_path})

@app.route('/create-zip', methods=['POST'])
def create_zip():
    # Generate zip filename with date and time
    current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f'captured_content_{current_time}.zip'
    zip_filepath = os.path.join(app.config['ZIP_FOLDER'], zip_filename)

    # Create a zip file of the captured images and the single text file
    with zipfile.ZipFile(zip_filepath, 'w') as zipf:
        # Add all images to the zip
        for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, app.config['UPLOAD_FOLDER']))

        # Add the single text file to the zip
        txt_path = os.path.join(app.config['TXT_FOLDER'], 'all_captured_content.txt')
        if os.path.exists(txt_path):
            zipf.write(txt_path, 'all_captured_content.txt')

    # After creating the zip, delete all captured images and text files
    try:
        shutil.rmtree(app.config['UPLOAD_FOLDER'])
        os.makedirs(app.config['UPLOAD_FOLDER'])  # Recreate empty folder
        shutil.rmtree(app.config['TXT_FOLDER'])
        os.makedirs(app.config['TXT_FOLDER'])  # Recreate empty folder
    except Exception as e:
        return jsonify({'message': f'Error deleting files: {str(e)}'})

    return jsonify({'message': 'Zip file created successfully', 'zip_path': f'/static/zip_files/{zip_filename}'})

@app.route('/download-zip', methods=['GET'])
def download_zip():
    zip_filename = request.args.get('zipfile')
    if not zip_filename:
        return jsonify({'message': 'No zip file specified'}), 400
    zip_filepath = os.path.join(app.config['ZIP_FOLDER'], zip_filename)
    if os.path.exists(zip_filepath):
        return send_file(zip_filepath, as_attachment=True)
    return jsonify({'message': 'Zip file not found'}), 404

if __name__ == "__main__":
    app.run(debug=True)
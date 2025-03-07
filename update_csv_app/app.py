import os
import csv
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = r'F:\AI-Payment-Gateway\static\uploads'
app.config['CSV_FILE'] = r'F:\AI-Payment-Gateway\data\analysis.csv'

# Ensure the upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('add_product.html')

@app.route('/add_product', methods=['POST'])
def add_product():
    category = request.form['category']
    product_name = request.form['product_name']
    discount_percentage = request.form['discount_percentage']
    current_price = request.form['current_price']
    original_price = request.form['original_price']
    
    # Handle file upload
    if 'product_image' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['product_image']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)

    if file:
        # Get the file extension (default to jpg if none)
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        # Generate a unique file name using the product name and a short UUID
        unique_filename = f"{product_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.{file_ext}"
        secure_file = secure_filename(unique_filename)
        
        # Save the file to the UPLOAD_FOLDER
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_file)
        file.save(file_path)
        
        # Create a relative path with forward slashes.
        # (Using an f-string here ensures the CSV will store: uploads/filename.jpg)
        image_path = f"uploads/{secure_file}"
    else:
        image_path = ""
    
    # Append new product data to CSV
    with open(app.config['CSV_FILE'], 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([category, product_name, discount_percentage, current_price, original_price, image_path])

    flash('Sản phẩm đã được thêm thành công!', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = 'your_secret_key'  # Configure your secret key here (see previous instructions)
    app.run(debug=True, port=1989)

import os
import uuid
import zipfile
from flask import render_template, request, jsonify, send_file, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from pdf_utils import (
    unlock_pdf_file, protect_pdf_file, merge_pdf_files, split_pdf_file,
    reorder_pdf_pages, convert_pdf_to_images as pdf_to_images_util,
    convert_images_to_pdf as images_to_pdf_util, compress_pdf_file
)
from app import app

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/unlock')
def unlock():
    return render_template('unlock.html')

@app.route('/protect')
def protect():
    return render_template('protect.html')

@app.route('/merge')
def merge():
    return render_template('merge.html')

@app.route('/split')
def split():
    return render_template('split.html')

@app.route('/reorder')
def reorder():
    return render_template('reorder.html')

@app.route('/convert')
def convert():
    return render_template('convert.html')

@app.route('/compress')
def compress():
    return render_template('compress.html')

@app.route('/api/unlock-pdf', methods=['POST'])
def unlock_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        password = request.form.get('password', '')
        
        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'Invalid file type. Expected PDF, got: {file.filename}'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename or 'document.pdf')
        unique_filename = f"{uuid.uuid4()}_{filename}"
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(input_path)
        
        # Process PDF
        output_filename = f"unlocked_{filename}"
        output_path = os.path.join(current_app.config['PROCESSED_FOLDER'], output_filename)
        
        success = unlock_pdf_file(input_path, output_path, password)
        
        # Clean up input file
        os.remove(input_path)
        
        if success:
            return jsonify({'success': True, 'filename': output_filename})
        else:
            return jsonify({'error': 'Failed to unlock PDF. Please check the password.'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error unlocking PDF: {str(e)}")
        return jsonify({'error': 'An error occurred while processing the file'}), 500

@app.route('/api/protect-pdf', methods=['POST'])
def protect_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        password = request.form.get('password', '')
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename or 'document.pdf')
        unique_filename = f"{uuid.uuid4()}_{filename}"
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(input_path)
        
        # Process PDF
        output_filename = f"protected_{filename}"
        output_path = os.path.join(current_app.config['PROCESSED_FOLDER'], output_filename)
        
        success = protect_pdf_file(input_path, output_path, password)
        
        # Clean up input file
        os.remove(input_path)
        
        if success:
            return jsonify({'success': True, 'filename': output_filename})
        else:
            return jsonify({'error': 'Failed to protect PDF'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error protecting PDF: {str(e)}")
        return jsonify({'error': 'An error occurred while processing the file'}), 500

@app.route('/api/merge-pdfs', methods=['POST'])
def merge_pdfs():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        
        if len(files) < 2:
            return jsonify({'error': 'At least 2 files are required for merging'}), 400
        
        input_paths = []
        
        # Save uploaded files
        for file in files:
            if file.filename == '' or not allowed_file(file.filename):
                continue
            
            filename = secure_filename(file.filename or 'document.pdf')
            unique_filename = f"{uuid.uuid4()}_{filename}"
            input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(input_path)
            input_paths.append(input_path)
        
        if len(input_paths) < 2:
            return jsonify({'error': 'At least 2 valid PDF files are required'}), 400
        
        # Process PDFs
        output_filename = f"merged_{uuid.uuid4()}.pdf"
        output_path = os.path.join(current_app.config['PROCESSED_FOLDER'], output_filename)
        
        success = merge_pdf_files(input_paths, output_path)
        
        # Clean up input files
        for path in input_paths:
            os.remove(path)
        
        if success:
            return jsonify({'success': True, 'filename': output_filename})
        else:
            return jsonify({'error': 'Failed to merge PDFs'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error merging PDFs: {str(e)}")
        return jsonify({'error': 'An error occurred while processing the files'}), 500

@app.route('/api/split-pdf', methods=['POST'])
def split_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        split_type = request.form.get('split_type', 'all')
        page_range = request.form.get('page_range', '')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename or 'document.pdf')
        unique_filename = f"{uuid.uuid4()}_{filename}"
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(input_path)
        
        # Process PDF
        output_dir = os.path.join(current_app.config['PROCESSED_FOLDER'], f"split_{uuid.uuid4()}")
        os.makedirs(output_dir, exist_ok=True)
        
        success, output_files = split_pdf_file(input_path, output_dir, split_type, page_range)
        
        # Clean up input file
        os.remove(input_path)
        
        if success and output_files:
            # Create a zip file if multiple files
            if len(output_files) > 1:
                zip_filename = f"split_{filename.rsplit('.', 1)[0]}.zip"
                zip_path = os.path.join(current_app.config['PROCESSED_FOLDER'], zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for file_path in output_files:
                        zipf.write(file_path, os.path.basename(file_path))
                
                # Clean up individual files
                for file_path in output_files:
                    os.remove(file_path)
                os.rmdir(output_dir)
                
                return jsonify({'success': True, 'filename': zip_filename, 'is_zip': True})
            else:
                # Single file
                single_file = output_files[0]
                final_filename = f"split_{os.path.basename(single_file)}"
                final_path = os.path.join(current_app.config['PROCESSED_FOLDER'], final_filename)
                os.rename(single_file, final_path)
                os.rmdir(output_dir)
                
                return jsonify({'success': True, 'filename': final_filename, 'is_zip': False})
        else:
            return jsonify({'error': 'Failed to split PDF'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error splitting PDF: {str(e)}")
        return jsonify({'error': 'An error occurred while processing the file'}), 500

@app.route('/api/reorder-pdf', methods=['POST'])
def reorder_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        page_order = request.form.get('page_order', '')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        if not page_order:
            return jsonify({'error': 'Page order is required'}), 400
        
        # Parse page order
        try:
            page_indices = [int(x.strip()) - 1 for x in page_order.split(',')]
        except ValueError:
            return jsonify({'error': 'Invalid page order format'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename or 'document.pdf')
        unique_filename = f"{uuid.uuid4()}_{filename}"
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(input_path)
        
        # Process PDF
        output_filename = f"reordered_{filename}"
        output_path = os.path.join(current_app.config['PROCESSED_FOLDER'], output_filename)
        
        success = reorder_pdf_pages(input_path, output_path, page_indices)
        
        # Clean up input file
        os.remove(input_path)
        
        if success:
            return jsonify({'success': True, 'filename': output_filename})
        else:
            return jsonify({'error': 'Failed to reorder PDF pages'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error reordering PDF: {str(e)}")
        return jsonify({'error': 'An error occurred while processing the file'}), 500

@app.route('/api/convert-pdf-to-images', methods=['POST'])
def convert_pdf_to_images():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        quality = int(request.form.get('quality', 95))
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename or 'document.pdf')
        unique_filename = f"{uuid.uuid4()}_{filename}"
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(input_path)
        
        # Process PDF
        output_dir = os.path.join(current_app.config['PROCESSED_FOLDER'], f"images_{uuid.uuid4()}")
        os.makedirs(output_dir, exist_ok=True)
        
        success, image_files = pdf_to_images_util(input_path, output_dir, quality)
        
        # Clean up input file
        os.remove(input_path)
        
        if success and image_files:
            # Create a zip file
            zip_filename = f"images_{filename.rsplit('.', 1)[0]}.zip"
            zip_path = os.path.join(current_app.config['PROCESSED_FOLDER'], zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file_path in image_files:
                    zipf.write(file_path, os.path.basename(file_path))
            
            # Clean up individual files
            for file_path in image_files:
                os.remove(file_path)
            os.rmdir(output_dir)
            
            return jsonify({'success': True, 'filename': zip_filename, 'is_zip': True})
        else:
            return jsonify({'error': 'Failed to convert PDF to images'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error converting PDF to images: {str(e)}")
        return jsonify({'error': 'An error occurred while processing the file'}), 500

@app.route('/api/convert-images-to-pdf', methods=['POST'])
def convert_images_to_pdf():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        quality = int(request.form.get('quality', 95))
        
        if len(files) < 1:
            return jsonify({'error': 'At least 1 image file is required'}), 400
        
        input_paths = []
        
        # Save uploaded files
        for file in files:
            if file.filename == '' or not allowed_file(file.filename):
                continue
            
            filename = secure_filename(file.filename or 'document.pdf')
            unique_filename = f"{uuid.uuid4()}_{filename}"
            input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(input_path)
            input_paths.append(input_path)
        
        if len(input_paths) < 1:
            return jsonify({'error': 'At least 1 valid image file is required'}), 400
        
        # Process images
        output_filename = f"converted_{uuid.uuid4()}.pdf"
        output_path = os.path.join(current_app.config['PROCESSED_FOLDER'], output_filename)
        
        success = images_to_pdf_util(input_paths, output_path, quality)
        
        # Clean up input files
        for path in input_paths:
            os.remove(path)
        
        if success:
            return jsonify({'success': True, 'filename': output_filename})
        else:
            return jsonify({'error': 'Failed to convert images to PDF'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error converting images to PDF: {str(e)}")
        return jsonify({'error': 'An error occurred while processing the files'}), 500

@app.route('/api/check-pdf-encryption', methods=['POST'])
def check_pdf_encryption():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'Invalid file type. Expected PDF, got: {file.filename}'}), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename or 'document.pdf')
        unique_filename = f"{uuid.uuid4()}_{filename}"
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(input_path)
        
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(input_path)
            is_encrypted = reader.is_encrypted
            page_count = len(reader.pages) if not is_encrypted else 0
            
            # Clean up temp file
            os.remove(input_path)
            
            return jsonify({
                'success': True,
                'is_encrypted': is_encrypted,
                'page_count': page_count,
                'filename': filename
            })
            
        except Exception as e:
            # Clean up temp file
            if os.path.exists(input_path):
                os.remove(input_path)
            current_app.logger.error(f"Error checking PDF encryption: {str(e)}")
            return jsonify({'error': 'Invalid PDF file or corrupted'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error in PDF encryption check: {str(e)}")
        return jsonify({'error': 'An error occurred while checking the file'}), 500

@app.route('/api/compress-pdf', methods=['POST'])
def compress_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        quality = int(request.form.get('quality', 50))
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename or 'document.pdf')
        unique_filename = f"{uuid.uuid4()}_{filename}"
        input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(input_path)
        
        # Process PDF
        output_filename = f"compressed_{filename}"
        output_path = os.path.join(current_app.config['PROCESSED_FOLDER'], output_filename)
        
        success = compress_pdf_file(input_path, output_path, quality)
        
        # Clean up input file
        os.remove(input_path)
        
        if success:
            return jsonify({'success': True, 'filename': output_filename})
        else:
            return jsonify({'error': 'Failed to compress PDF'}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error compressing PDF: {str(e)}")
        return jsonify({'error': 'An error occurred while processing the file'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(current_app.config['PROCESSED_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        current_app.logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': 'An error occurred while downloading the file'}), 500

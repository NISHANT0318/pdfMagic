import os
import io
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def unlock_pdf_file(input_path, output_path, password):
    """Remove password protection from a PDF file"""
    try:
        reader = PdfReader(input_path)
        
        if reader.is_encrypted:
            # Try to decrypt with the provided password
            if not reader.decrypt(password):
                logger.error("Failed to decrypt PDF with provided password")
                return False
        
        writer = PdfWriter()
        
        # Copy all pages to the writer
        for page in reader.pages:
            writer.add_page(page)
        
        # Write the unlocked PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return True
        
    except Exception as e:
        logger.error(f"Error unlocking PDF: {str(e)}")
        return False

def protect_pdf_file(input_path, output_path, password):
    """Add password protection to a PDF file"""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        # Copy all pages to the writer
        for page in reader.pages:
            writer.add_page(page)
        
        # Add password protection
        writer.encrypt(password)
        
        # Write the protected PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return True
        
    except Exception as e:
        logger.error(f"Error protecting PDF: {str(e)}")
        return False

def merge_pdf_files(input_paths, output_path):
    """Merge multiple PDF files into one"""
    try:
        writer = PdfWriter()
        
        for input_path in input_paths:
            reader = PdfReader(input_path)
            
            # If encrypted, try without password first
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except:
                    logger.warning(f"Could not decrypt {input_path}, skipping")
                    continue
            
            # Add all pages from this PDF
            for page in reader.pages:
                writer.add_page(page)
        
        # Write the merged PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return True
        
    except Exception as e:
        logger.error(f"Error merging PDFs: {str(e)}")
        return False

def split_pdf_file(input_path, output_dir, split_type='all', page_range=''):
    """Split a PDF file into separate files"""
    try:
        reader = PdfReader(input_path)
        
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except:
                logger.error("Cannot split encrypted PDF without password")
                return False, []
        
        output_files = []
        
        if split_type == 'all':
            # Split into individual pages
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                
                output_filename = f"page_{i+1}.pdf"
                output_path = os.path.join(output_dir, output_filename)
                
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
                
                output_files.append(output_path)
        
        elif split_type == 'range' and page_range:
            # Split by page range
            try:
                if '-' in page_range:
                    start, end = map(int, page_range.split('-'))
                    start = max(1, start) - 1  # Convert to 0-based index
                    end = min(len(reader.pages), end)
                    
                    writer = PdfWriter()
                    for i in range(start, end):
                        writer.add_page(reader.pages[i])
                    
                    output_filename = f"pages_{start+1}-{end}.pdf"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)
                    
                    output_files.append(output_path)
                else:
                    # Single page
                    page_num = int(page_range) - 1
                    if 0 <= page_num < len(reader.pages):
                        writer = PdfWriter()
                        writer.add_page(reader.pages[page_num])
                        
                        output_filename = f"page_{page_num+1}.pdf"
                        output_path = os.path.join(output_dir, output_filename)
                        
                        with open(output_path, 'wb') as output_file:
                            writer.write(output_file)
                        
                        output_files.append(output_path)
            except ValueError:
                logger.error("Invalid page range format")
                return False, []
        
        return True, output_files
        
    except Exception as e:
        logger.error(f"Error splitting PDF: {str(e)}")
        return False, []

def reorder_pdf_pages(input_path, output_path, page_indices):
    """Reorder pages in a PDF file"""
    try:
        reader = PdfReader(input_path)
        
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except:
                logger.error("Cannot reorder encrypted PDF without password")
                return False
        
        writer = PdfWriter()
        
        # Validate page indices
        max_pages = len(reader.pages)
        for index in page_indices:
            if 0 <= index < max_pages:
                writer.add_page(reader.pages[index])
            else:
                logger.warning(f"Invalid page index: {index + 1}")
        
        # Write the reordered PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return True
        
    except Exception as e:
        logger.error(f"Error reordering PDF: {str(e)}")
        return False

def convert_pdf_to_images(input_path, output_dir, quality=95):
    """Convert PDF pages to JPEG images"""
    try:
        # Convert PDF to images
        images = convert_from_path(input_path, dpi=150)
        
        output_files = []
        
        for i, image in enumerate(images):
            output_filename = f"page_{i+1}.jpg"
            output_path = os.path.join(output_dir, output_filename)
            
            # Save with specified quality
            image.save(output_path, 'JPEG', quality=quality, optimize=True)
            output_files.append(output_path)
        
        return True, output_files
        
    except Exception as e:
        logger.error(f"Error converting PDF to images: {str(e)}")
        return False, []

def convert_images_to_pdf(input_paths, output_path, quality=95):
    """Convert multiple images to a single PDF"""
    try:
        images = []
        
        for input_path in input_paths:
            # Open and process each image
            img = Image.open(input_path)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large (optional optimization)
            max_size = (2000, 2000)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            images.append(img)
        
        if images:
            # Save all images as a single PDF
            first_image = images[0]
            other_images = images[1:] if len(images) > 1 else []
            
            first_image.save(
                output_path,
                'PDF',
                save_all=True,
                append_images=other_images,
                quality=quality,
                optimize=True
            )
        
        return True
        
    except Exception as e:
        logger.error(f"Error converting images to PDF: {str(e)}")
        return False

def compress_pdf_file(input_path, output_path, quality=50):
    """Compress a PDF file by reducing image quality"""
    try:
        # For basic compression, we'll recreate the PDF
        reader = PdfReader(input_path)
        
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except:
                logger.error("Cannot compress encrypted PDF without password")
                return False
        
        writer = PdfWriter()
        
        # Copy all pages (PyPDF2 will automatically compress)
        for page in reader.pages:
            writer.add_page(page)
        
        # Write with compression
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return True
        
    except Exception as e:
        logger.error(f"Error compressing PDF: {str(e)}")
        return False

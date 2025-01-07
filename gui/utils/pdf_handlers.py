"""Module containing PDF handling utility functions."""
import logging
import io
from pathlib import Path
from typing import List, Optional

import fitz
from PIL import Image

logger = logging.getLogger(__name__)

def merge_and_compress_pdfs(pdf_paths: List[Path], output_path: Path) -> bool:
    """
    Merge PDF pairs (Document + Map), remove annotations, and then flatten/compress.
    
    Args:
        pdf_paths: List of paths to PDF files to merge
        output_path: Path where to save the merged PDF
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Step 1: Merge PDFs using PyMuPDF
        merged_doc = fitz.open()

        for pdf_path in pdf_paths:
            src_doc = fitz.open(pdf_path)
            merged_doc.insert_pdf(src_doc)
            src_doc.close()

        # Step 2: Save the Merged and Cleaned PDF Temporarily in Memory
        # Using a bytes buffer to avoid writing to disk
        merged_pdf_buffer = io.BytesIO()
        merged_doc.save(merged_pdf_buffer, deflate=True, garbage=3, incremental=False)
        merged_doc.close()

        # Step 3: Re-open the merged PDF from the buffer
        merged_pdf_buffer.seek(0)
        merged_doc = fitz.open(stream=merged_pdf_buffer, filetype="pdf")

        # Step 4: Create a New PDF for Image-Based Content
        image_based_pdf = fitz.open()

        for page_number in range(merged_doc.page_count):
            page = merged_doc.load_page(page_number)
            zoom = 2.0  # Adjust for higher/lower resolution
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Convert pixmap to bytes in a supported image format (e.g., PNG)
            img_bytes = pix.pil_tobytes(format="PNG")
            
            # Create a new PDF page with the same dimensions as the original page
            original_page = page
            original_rect = original_page.rect  # in points
            pdf_page = image_based_pdf.new_page(width=original_rect.width, height=original_rect.height)
            
            # Insert the image into the new PDF page
            # Calculate the rectangle where the image will be placed
            # To fit the image exactly on the page, use the entire page rectangle
            insert_rect = fitz.Rect(0, 0, original_rect.width, original_rect.height)
            
            # Insert the image using the stream parameter
            pdf_page.insert_image(
                insert_rect,
                stream=img_bytes,
                keep_proportion=True
            )

            logger.debug(f"Inserted image on page {page_number + 1}")

        # Step 5: Save the Image-Based Merged PDF
        image_based_pdf.save(output_path, deflate=True, garbage=3)
        image_based_pdf.close()
        merged_doc.close()
        merged_pdf_buffer.close()

        return True

    except Exception as e:
        logger.error(f"Error merging and compressing PDFs: {e}")
        return False

def merge_letters(letter_paths: List[Path], output_path: Path) -> bool:
    """
    Merge generated letters into a single PDF.
    
    Args:
        letter_paths: List of paths to letter PDFs to merge
        output_path: Path where to save the merged PDF
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        merged_doc = fitz.open()
        
        for letter_pdf in letter_paths:
            with fitz.open(letter_pdf) as src_doc:
                merged_doc.insert_pdf(src_doc)
        
        # Flatten and compress
        merged_doc.save(output_path, deflate=True, garbage=4)
        merged_doc.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error merging letters: {e}")
        return False

def get_pdf_page_count(pdf_path: Path) -> Optional[int]:
    """
    Get the number of pages in a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Optional[int]: Number of pages if successful, None otherwise
    """
    try:
        with fitz.open(pdf_path) as doc:
            return doc.page_count
    except Exception as e:
        logger.error(f"Error getting PDF page count: {e}")
        return None

def extract_pdf_text(pdf_path: Path) -> Optional[str]:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Optional[str]: Extracted text if successful, None otherwise
    """
    try:
        with fitz.open(pdf_path) as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return None
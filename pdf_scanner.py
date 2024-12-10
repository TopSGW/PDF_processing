"""Module containing PDF scanning functionality."""
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, NamedTuple
import fitz  # PyMuPDF
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from PyQt5.QtCore import QThread, pyqtSignal
import cv2
from PIL import Image
import io
import shutil
import sys
import argparse

# Try importing pytesseract, but don't fail if it's not available
try:
    import pytesseract
    TESSERACT_AVAILABLE = bool(shutil.which('tesseract'))
except ImportError:
    TESSERACT_AVAILABLE = False

from constants import PDF_EXTENSION, REQUIRED_PDF_COUNT, PROCESSED_FOLDER_MARKER

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFType:
    """Enumeration of PDF types."""
    DOCUMENT = "document"
    MAP = "map"
    UNKNOWN = "unknown"

class PDFContent:
    """Class for analyzing PDF content."""
    
    @staticmethod
    def extract_text(pdf_path: Path) -> str:
        """
        Extract text content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            text = ""
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    text += page.get_text()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""

    @staticmethod
    def extract_images_and_ocr(pdf_path: Path) -> List[str]:
        """
        Extract images from PDF and perform OCR on them if available.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of OCR text results from images
        """
        if not TESSERACT_AVAILABLE:
            logger.warning("Tesseract OCR is not available. Skipping OCR analysis.")
            return []

        try:
            ocr_texts = []
            with fitz.open(pdf_path) as doc:
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    image_list = page.get_images()
                    
                    for img_index, img in enumerate(image_list):
                        try:
                            xref = img[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            
                            # Convert to PIL Image
                            image = Image.open(io.BytesIO(image_bytes))
                            
                            # Convert to numpy array for OpenCV processing
                            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                            
                            # Image preprocessing for better OCR
                            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                            
                            # Convert back to PIL Image for OCR
                            pil_image = Image.fromarray(thresh)
                            
                            # Perform OCR
                            ocr_text = pytesseract.image_to_string(pil_image)
                            if ocr_text.strip():  # Only add non-empty results
                                ocr_texts.append(ocr_text)
                            
                        except Exception as e:
                            logger.error(f"Error processing image {img_index} on page {page_num}: {e}")
                            continue
                            
            return ocr_texts
        except Exception as e:
            logger.error(f"Error extracting images from PDF {pdf_path}: {e}")
            return []

    @staticmethod
    def analyze_image_content(pdf_path: Path) -> Tuple[bool, float]:
        """
        Analyze image content to determine if it looks like a map.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (is_map_like, confidence_score)
        """
        try:
            max_confidence = 0.0
            with fitz.open(pdf_path) as doc:
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    image_list = page.get_images()
                    
                    for img_index, img in enumerate(image_list):
                        try:
                            xref = img[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            
                            # Convert to PIL Image and then to OpenCV format
                            image = Image.open(io.BytesIO(image_bytes))
                            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                            
                            # Image analysis metrics
                            metrics = []
                            
                            # 1. Edge detection analysis
                            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                            edges = cv2.Canny(gray, 50, 150)
                            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
                            metrics.append(min(edge_density * 5, 1.0))  # Normalize to 0-1
                            
                            # 2. Color diversity analysis
                            unique_colors = len(np.unique(img_cv.reshape(-1, 3), axis=0))
                            color_score = min(unique_colors / 2000, 1.0)  # Normalize to 0-1
                            metrics.append(color_score)
                            
                            # 3. Line detection (maps often have straight lines)
                            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, 
                                                  minLineLength=100, maxLineGap=10)
                            if lines is not None:
                                line_score = min(len(lines) / 50, 1.0)  # Normalize to 0-1
                            else:
                                line_score = 0
                            metrics.append(line_score)
                            
                            # 4. Texture analysis using GLCM
                            texture_score = np.std(gray) / 128  # Simple texture measure
                            metrics.append(texture_score)
                            
                            # Calculate confidence score
                            confidence = sum(metrics) / len(metrics)
                            max_confidence = max(max_confidence, confidence)
                            
                        except Exception as e:
                            logger.error(f"Error analyzing image {img_index} on page {page_num}: {e}")
                            continue
                            
            return max_confidence >= 0.5, max_confidence
        except Exception as e:
            logger.error(f"Error analyzing images in PDF {pdf_path}: {e}")
            return False, 0.0

    @staticmethod
    def analyze_pdf_type(pdf_path: Path) -> str:
        """
        Analyze a PDF to determine its type (document, map, or unknown).
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            PDFType indicating the determined type
        """
        try:
            # Extract text content
            text = PDFContent.extract_text(pdf_path)
            text_lower = text.lower()
            
            # Document-specific keywords
            document_keywords = [
                'consent', 'agreement', 'contract', 'wayleave', 'permission',
                'terms', 'conditions', 'signature', 'signed', 'dated',
                'hereby', 'parties', 'rights', 'obligations'
            ]
            
            # Map-specific keywords
            map_keywords = [
                'map', 'scale', 'legend', 'north arrow', 'coordinates',
                'projection', 'latitude', 'longitude', 'grid', 'terrain',
                'topographic', 'elevation', 'boundary', 'region', 'km', 'miles',
                'contour', 'geographic', 'cartographic', 'spatial', 'compass',
                'route', 'area', 'location', 'distance', 'direction', 'layout',
                'site plan', 'lv', 'layout view'
            ]
            
            # Count keyword occurrences
            doc_keyword_count = sum(1 for keyword in document_keywords if keyword in text_lower)
            map_keyword_count = sum(1 for keyword in map_keywords if keyword in text_lower)
            
            # Check filename for additional clues
            filename_lower = pdf_path.name.lower()
            if any(name in filename_lower for name in ['lv.', 'layout', 'map', 'plan']):
                map_keyword_count += 2
            if any(name in filename_lower for name in ['consent', 'agreement', 'contract', 'wayleave']):
                doc_keyword_count += 2
            
            # Image analysis for map detection
            is_map_like, image_confidence = PDFContent.analyze_image_content(pdf_path)
            if is_map_like:
                map_keyword_count += 3
            
            # OCR analysis if available
            if TESSERACT_AVAILABLE:
                ocr_texts = PDFContent.extract_images_and_ocr(pdf_path)
                ocr_text = ' '.join(ocr_texts).lower()
                doc_keyword_count += sum(1 for keyword in document_keywords if keyword in ocr_text)
                map_keyword_count += sum(1 for keyword in map_keywords if keyword in ocr_text)
            
            # Word count (documents typically have more text)
            word_count = len(text.split())
            if word_count > 300:  # Typical documents have more text
                doc_keyword_count += 2
            elif word_count < 100 and is_map_like:  # Maps typically have less text
                map_keyword_count += 2
            
            logger.debug(f"PDF Analysis for {pdf_path.name}:")
            logger.debug(f"- Document keywords: {doc_keyword_count}")
            logger.debug(f"- Map keywords: {map_keyword_count}")
            logger.debug(f"- Word count: {word_count}")
            logger.debug(f"- Map-like images: {is_map_like}")
            
            # Determine type based on scores
            if map_keyword_count > doc_keyword_count and map_keyword_count >= 3:
                return PDFType.MAP
            elif doc_keyword_count > map_keyword_count and doc_keyword_count >= 3:
                return PDFType.DOCUMENT
            else:
                return PDFType.UNKNOWN
            
        except Exception as e:
            logger.error(f"Error analyzing PDF {pdf_path}: {e}")
            return PDFType.UNKNOWN

    @staticmethod
    def is_map_pdf(pdf_path: Path, verbose: bool = False) -> bool:
        """
        Determine if a PDF is likely a map based on its content.
        
        Args:
            pdf_path: Path to the PDF file
            verbose: Whether to print detailed analysis information
            
        Returns:
            True if the PDF is likely a map, False otherwise
        """
        return PDFContent.analyze_pdf_type(pdf_path) == PDFType.MAP

class PDFPair(NamedTuple):
    """Represents PDFs found in a folder."""
    document_pdf: Optional[Path]  # The document PDF (e.g., consent, agreement)
    map_pdf: Optional[Path]      # The map PDF (e.g., layout view, site plan)
    additional_pdfs: List[Path]  # Any PDFs that couldn't be clearly classified

class PDFScanner:
    """Class responsible for scanning directories for PDF files."""
    
    @staticmethod
    def is_processed_folder(folder: Path) -> bool:
        """
        Check if a folder has been processed before.
        
        Args:
            folder: Path to the folder to check
            
        Returns:
            True if the folder has been processed, False otherwise
        """
        try:
            marker = folder / PROCESSED_FOLDER_MARKER
            return marker.exists()
        except Exception as e:
            logger.error(f"Error checking processed status for folder {folder}: {e}")
            return False

    @staticmethod
    def mark_folder_as_processed(folder: Path) -> None:
        """
        Mark a folder as processed by creating a marker file.
        
        Args:
            folder: Path to the folder to mark
        """
        try:
            marker = folder / PROCESSED_FOLDER_MARKER
            marker.touch()
            logger.debug(f"Marked folder as processed: {folder}")
        except Exception as e:
            logger.error(f"Error marking folder as processed {folder}: {e}")
    
    @staticmethod
    def get_pdf_files(directory: Path) -> PDFPair:
        """
        Get all PDF files in the given directory and categorize them.
        
        Args:
            directory: Path to the directory to scan
            
        Returns:
            PDFPair containing categorized PDFs
        """
        try:
            logger.debug(f"Scanning directory for PDFs: {directory}")
            # Get all PDF files
            pdfs = []
            for pattern in [f"*{PDF_EXTENSION.lower()}", f"*{PDF_EXTENSION.upper()}"]:
                pdfs.extend(directory.glob(pattern))
            
            if not pdfs:
                logger.debug(f"No PDF files found in {directory}")
                return PDFPair(None, None, [])
            
            # Analyze each PDF to categorize it
            map_pdf = None
            document_pdf = None
            additional_pdfs = []
            
            # First pass: categorize PDFs
            for pdf in sorted(pdfs):
                pdf_type = PDFContent.analyze_pdf_type(pdf)
                
                if pdf_type == PDFType.MAP and map_pdf is None:
                    map_pdf = pdf
                elif pdf_type == PDFType.DOCUMENT and document_pdf is None:
                    document_pdf = pdf
                else:
                    additional_pdfs.append(pdf)
            
            # If we have unclassified PDFs but missing either map or document,
            # try to fill in the gaps based on filename patterns
            if additional_pdfs:
                if map_pdf is None:
                    for pdf in additional_pdfs[:]:
                        if any(pattern in pdf.name.lower() for pattern in ['lv.', 'layout', 'map', 'plan']):
                            map_pdf = pdf
                            additional_pdfs.remove(pdf)
                            break
                            
                if document_pdf is None:
                    for pdf in additional_pdfs[:]:
                        if any(pattern in pdf.name.lower() for pattern in ['consent', 'agreement', 'contract']):
                            document_pdf = pdf
                            additional_pdfs.remove(pdf)
                            break
            
            logger.info(f"Found in {directory}: "
                       f"document={document_pdf.name if document_pdf else 'None'}, "
                       f"map={map_pdf.name if map_pdf else 'None'}, "
                       f"additional={len(additional_pdfs)} PDFs")
            
            return PDFPair(document_pdf, map_pdf, additional_pdfs)
            
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
            return PDFPair(None, None, [])

    @staticmethod
    def scan_directory(root_dir: Path, current_dir: Path) -> List[Tuple[str, PDFPair]]:
        """
        Recursively scan a directory for folders containing PDF files.
        
        Args:
            root_dir: Path to the root directory where scanning started
            current_dir: Path to the current directory being scanned
            
        Returns:
            List of tuples containing (relative_path, PDFPair)
        """
        results: List[Tuple[str, PDFPair]] = []
        
        try:
            logger.debug(f"Scanning directory: {current_dir}")
            
            # Get PDF files in current directory
            pdf_pair = PDFScanner.get_pdf_files(current_dir)
            
            # If PDFs found or folder was previously processed, add to results
            if (pdf_pair.document_pdf or pdf_pair.map_pdf or 
                pdf_pair.additional_pdfs or 
                PDFScanner.is_processed_folder(current_dir)):
                
                # Calculate relative path from root directory
                try:
                    relative_path = str(current_dir.relative_to(root_dir))
                    logger.debug(f"Calculated relative path: {relative_path}")
                except ValueError:
                    relative_path = str(current_dir)
                    logger.warning(f"Using absolute path as fallback: {relative_path}")
                
                results.append((relative_path, pdf_pair))
                
                # Mark folder as processed if not already
                if not PDFScanner.is_processed_folder(current_dir):
                    PDFScanner.mark_folder_as_processed(current_dir)
            
            # Scan subdirectories
            try:
                subdirs = [d for d in current_dir.iterdir() if d.is_dir()]
                logger.debug(f"Found {len(subdirs)} subdirectories in {current_dir}")
                
                for subdir in subdirs:
                    try:
                        logger.debug(f"Scanning subdirectory: {subdir}")
                        sub_results = PDFScanner.scan_directory(root_dir, subdir)
                        if sub_results:
                            logger.debug(f"Found {len(sub_results)} results in {subdir}")
                            results.extend(sub_results)
                    except Exception as e:
                        logger.error(f"Error scanning subdirectory {subdir}: {e}")
                        continue
            except Exception as e:
                logger.error(f"Error listing subdirectories in {current_dir}: {e}")
                        
        except Exception as e:
            logger.error(f"Error accessing directory {current_dir}: {e}")
            
        return results

class ScannerThread(QThread):
    """Thread class for running PDF scanning operations."""
    
    scan_finished = pyqtSignal(list)
    
    def __init__(self, folder: str):
        """
        Initialize the scanner thread.
        
        Args:
            folder: Path to the folder to scan
        """
        super().__init__()
        self.folder = Path(folder)
        
    def run(self) -> None:
        """Run the scanning operation in a separate thread."""
        try:
            logger.info(f"Starting scan of directory: {self.folder}")
            results = PDFScanner.scan_directory(self.folder, self.folder)
            logger.info(f"Scan completed. Found {len(results)} folders with PDFs")
            self.scan_finished.emit(results)
        except Exception as e:
            logger.error(f"Error during scanning: {e}")
            self.scan_finished.emit([])

def main():
    """Command line interface for testing map detection."""
    parser = argparse.ArgumentParser(description='Test PDF map detection')
    parser.add_argument('pdf_path', type=str, help='Path to the PDF file to analyze')
    parser.add_argument('--verbose', '-v', action='store_true', help='Print detailed analysis')
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        return
    
    pdf_type = PDFContent.analyze_pdf_type(pdf_path)
    print(f"\nAnalysis Result: The PDF is classified as: {pdf_type}")
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        print("Please provide a PDF file path to analyze.")
        print("Usage: python pdf_scanner.py <pdf_path> [--verbose]")
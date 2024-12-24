"""Module containing PDF scanning functionality."""
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, NamedTuple
import fitz  # PyMuPDF
from PyQt5.QtCore import QThread, pyqtSignal
import sys
import argparse

from constants import PDF_EXTENSION, REQUIRED_PDF_COUNT, PROCESSED_FOLDER_MARKER
from document_classifier import identify_wayleave_type

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
    LETTER = "letter"  # Added new type for letters
    UNKNOWN = "unknown"

class PDFContent:
    """Class for analyzing PDF content."""
    
    @staticmethod
    def get_page_count(pdf_path: Path) -> int:
        """
        Get the number of pages in a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Number of pages in the PDF
        """
        try:
            with fitz.open(pdf_path) as doc:
                return len(doc)
        except Exception as e:
            logger.error(f"Error getting page count from PDF {pdf_path}: {e}")
            return 0

    @staticmethod
    def extract_text_content(pdf_path: Path) -> str:
        """
        Extract text content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content as string
        """
        try:
            with fitz.open(pdf_path) as doc:
                text = ""
                for page in doc:
                    text += page.get_text()
                return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""

    @staticmethod
    def analyze_wayleave_type(pdf_path: Path) -> str:
        """
        Analyze a PDF to determine its wayleave type (annual or 15-year).
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            String indicating the wayleave type ('annual', '15-year', or 'unknown')
        """
        try:
            text_content = PDFContent.extract_text_content(pdf_path)
            return identify_wayleave_type(text_content)
        except Exception as e:
            logger.error(f"Error analyzing wayleave type for PDF {pdf_path}: {e}")
            return "unknown"

    @staticmethod
    def is_letter_content(text_content: str) -> bool:
        """
        Check if the content appears to be a letter.
        
        Args:
            text_content: The text content to analyze
            
        Returns:
            True if the content appears to be a letter, False otherwise
        """
        letter_indicators = [
            "Yours sincerely",
            "Re: Electrical Equipment",
            "Paul Wakeford",
            "Partner",
            "DARLANDS"
        ]
        return any(indicator in text_content for indicator in letter_indicators)

    @staticmethod
    def analyze_pdf_type(pdf_path: Path) -> str:
        """
        Analyze a PDF to determine its type based on content and structure.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            PDFType indicating the determined type
        """
        try:
            page_count = PDFContent.get_page_count(pdf_path)
            text_content = PDFContent.extract_text_content(pdf_path)
            filename_lower = pdf_path.name.lower()
            
            # First check if it's a letter
            if PDFContent.is_letter_content(text_content):
                return PDFType.LETTER
            
            # Then check for map-specific indicators
            map_indicators = ['lv.', 'layout', 'map', 'plan', 'site']
            if page_count == 1 and any(indicator in filename_lower for indicator in map_indicators):
                return PDFType.MAP
                
            # Check for document-specific indicators
            doc_indicators = ['consent', 'agreement', 'contract', 'wayleave']
            if page_count > 1 or any(indicator in filename_lower for indicator in doc_indicators):
                return PDFType.DOCUMENT
            
            # If single page but no clear indicators, default to map
            if page_count == 1:
                return PDFType.MAP
                
            return PDFType.UNKNOWN
            
        except Exception as e:
            logger.error(f"Error analyzing PDF {pdf_path}: {e}")
            return PDFType.UNKNOWN

    @staticmethod
    def is_map_pdf(pdf_path: Path, verbose: bool = False) -> bool:
        """
        Determine if a PDF is likely a map.
        
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
    wayleave_type: str = "unknown"  # The type of wayleave document (annual, 15-year, or unknown)

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
            
            excluded_files = {"Print.pdf", "Print 2.pdf"}  # Filenames we do NOT want to include
            pdfs = []
            
            # Get all PDF files while excluding certain files
            for pattern in [f"*{PDF_EXTENSION.lower()}", f"*{PDF_EXTENSION.upper()}"]:
                logger.info(f"Using pattern: {pattern}")
                pdfs.extend(
                    pdf
                    for pdf in directory.glob(pattern)
                    if pdf.name not in excluded_files
                )
            
            if not pdfs:
                logger.debug(f"No PDF files found in {directory}")
                return PDFPair(None, None, [], "unknown")
            
            # Analyze each PDF to categorize it
            map_pdf = None
            document_pdf = None
            additional_pdfs = []
            wayleave_type = "unknown"
            
            # First pass: categorize PDFs
            for pdf in sorted(pdfs):
                pdf_type = PDFContent.analyze_pdf_type(pdf)
                
                if pdf_type == PDFType.MAP and map_pdf is None:
                    map_pdf = pdf
                elif pdf_type == PDFType.DOCUMENT and document_pdf is None:
                    document_pdf = pdf
                    # Analyze wayleave type for document PDFs
                    wayleave_type = PDFContent.analyze_wayleave_type(pdf)
                elif pdf_type != PDFType.LETTER:  # Ignore letters in classification
                    additional_pdfs.append(pdf)
            
            logger.info(
                f"Found in {directory}: "
                f"document={document_pdf.name if document_pdf else 'None'}, "
                f"map={map_pdf.name if map_pdf else 'None'}, "
                f"wayleave_type={wayleave_type}, "
                f"additional={len(additional_pdfs)} PDFs"
            )
            
            return PDFPair(document_pdf, map_pdf, additional_pdfs, wayleave_type)
            
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
            return PDFPair(None, None, [], "unknown")

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

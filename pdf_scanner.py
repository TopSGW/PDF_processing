"""Module containing PDF scanning functionality."""
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, NamedTuple
import fitz  # PyMuPDF
from PyQt5.QtCore import QThread, pyqtSignal
import sys
import argparse

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
    def analyze_pdf_type(pdf_path: Path) -> str:
        """
        Analyze a PDF to determine its type based on page count.
        Map PDFs have 1 page, documents have more pages.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            PDFType indicating the determined type
        """
        try:
            page_count = PDFContent.get_page_count(pdf_path)
            
            # Check filename for additional clues
            filename_lower = pdf_path.name.lower()
            
            # If filename contains map-related keywords, prioritize that for single-page PDFs
            if page_count == 1 and any(name in filename_lower for name in ['lv.', 'layout', 'map', 'plan']):
                return PDFType.MAP
                
            # If filename contains document-related keywords, prioritize that for multi-page PDFs
            if page_count > 1 and any(name in filename_lower for name in ['consent', 'agreement', 'contract', 'wayleave']):
                return PDFType.DOCUMENT
            
            # Otherwise, use page count as the primary determinant
            if page_count == 1:
                return PDFType.MAP
            elif page_count > 1:
                return PDFType.DOCUMENT
            else:
                return PDFType.UNKNOWN
            
        except Exception as e:
            logger.error(f"Error analyzing PDF {pdf_path}: {e}")
            return PDFType.UNKNOWN

    @staticmethod
    def is_map_pdf(pdf_path: Path, verbose: bool = False) -> bool:
        """
        Determine if a PDF is likely a map based on page count.
        
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
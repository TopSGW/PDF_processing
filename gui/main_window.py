"""Module containing the main window of the application."""
import logging
from pathlib import Path
from typing import List, Tuple, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QPushButton,
    QStyle
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from constants import WINDOW_TITLE, MERGE_AND_COMPRESS_PDFS
from letter_generator import (
    generate_letter,
    generate_second_letter,
    create_word_letter,
    convert_pdf_letter,
    extract_names_and_address_annual,
    extract_names_and_address_fifteen_year,
    GenerationError
)
from pdf_scanner import ScannerThread, PDFPair, PDFContent
from gui.components.header_section import HeaderSection
from gui.components.progress_section import ProgressSection
from gui.components.results_section import ResultsSection
from gui.components.control_buttons import ControlButtons
from gui.components.letter_section import LetterSection, StyledButton
from gui.utils.pdf_handlers import merge_and_compress_pdfs

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MainWindow(QWidget):
    """Main window of the application."""
    
    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        self.scanner_thread: Optional[ScannerThread] = None
        self.selected_folder: Optional[Path] = None
        
        # Initialize components
        self.header_section = HeaderSection(self.on_folder_selected)
        self.progress_section = ProgressSection()
        self.results_section = ResultsSection(self.update_button_states)
        self.control_buttons = ControlButtons(
            self.move_item_up,
            self.move_item_down,
            self.remove_selected,
            self.add_pdf_pair
        )
        
        # Initialize Print button
        self.merge_btn: Optional[StyledButton] = None
        
        # Initialize letter section with progress callback
        self.letter_section = LetterSection(
            self.update_progress,
            self.handle_letter_generation_error
        )
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(800, 600)
        
        # Set window style
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f6f7;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add header section
        main_layout.addWidget(self.header_section)
        
        # Add progress section
        main_layout.addWidget(self.progress_section)
        
        # Create main content area with controls
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)
        content_layout.addWidget(self.results_section)
        content_layout.addWidget(self.control_buttons)
        main_layout.addLayout(content_layout)
        
        # Add letter section
        main_layout.addWidget(self.letter_section)
        
        # Add Print button at bottom with modern styling
        self.merge_btn = StyledButton(
            MERGE_AND_COMPRESS_PDFS,
            QStyle.SP_DialogSaveButton,
            primary=True
        )
        self.merge_btn.setEnabled(False)
        self.merge_btn.clicked.connect(self.merge_and_compress_pdfs)
        
        # Create a container for the print button with proper spacing
        button_container = QHBoxLayout()
        button_container.addStretch()
        button_container.addWidget(self.merge_btn)
        main_layout.addLayout(button_container)
        
        self.setLayout(main_layout)
        
        # Connect components
        self.letter_section.set_tree_widget(self.results_section.result_tree)
        self.letter_section.set_merge_button(self.merge_btn)
        
    def update_progress(self, current: int, total: int, message: str) -> None:
        """Update progress bar and status label."""
        if total > 0:
            self.progress_section.show_progress(True)
            self.progress_section.show_status(True)
            self.progress_section.set_progress_range(0, total)
            self.progress_section.set_progress_value(current)
            self.progress_section.set_status_text(message)
        else:
            self.progress_section.show_progress(False)
            self.progress_section.show_status(False)
        
    def on_folder_selected(self, folder: str) -> None:
        """Handle folder selection."""
        try:
            self.selected_folder = Path(folder)
            self.results_section.set_selected_folder(self.selected_folder)
            self.control_buttons.set_selected_folder(self.selected_folder)
            self.letter_section.set_selected_folder(self.selected_folder)
            self.scan_folder(folder)
        except Exception as e:
            logger.error(f"Error handling folder selection: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error handling folder selection: {str(e)}"
            )
            
    def scan_folder(self, home_folder: str) -> None:
        """Start scanning the selected folder."""
        try:
            logger.debug(f"Starting scan of folder: {home_folder}")
            
            # Clear previous results
            self.results_section.clear_results()
            
            # Show progress
            self.progress_section.show_progress(True)
            self.progress_section.set_indeterminate()
            self.progress_section.set_status_text("Scanning folder...")
            self.progress_section.show_status(True)
            
            # Disable controls
            self.header_section.set_button_enabled(False)
            
            # Create and start scanning thread
            self.scanner_thread = ScannerThread(home_folder)
            self.scanner_thread.scan_finished.connect(self.handle_scan_results)
            self.scanner_thread.start()
            
        except Exception as e:
            logger.error(f"Error starting scan: {e}")
            self.progress_section.show_progress(False)
            self.progress_section.show_status(False)
            self.header_section.set_button_enabled(True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error starting scan: {str(e)}"
            )
            
    def handle_scan_results(self, results: List[Tuple[str, PDFPair]]) -> None:
        """Handle the results from the scanner thread."""
        try:
            logger.debug(f"Handling scan results: {len(results)} folders found")
            
            # Hide progress
            self.progress_section.show_progress(False)
            self.progress_section.show_status(False)
            self.header_section.set_button_enabled(True)
            
            # Display results
            self.results_section.display_results(results)
            
            # Update button states
            self.update_button_states()
            
        except Exception as e:
            logger.error(f"Error handling scan results: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error displaying results: {str(e)}"
            )
            
    def update_button_states(self) -> None:
        """Update the enabled state of control buttons based on selection."""
        if not self.results_section.result_tree:
            return
            
        selected = self.results_section.result_tree.selectedItems()
        has_selection = bool(selected)
        is_folder = has_selection and selected[0].childCount() > 0
        
        # Get the selected item's index if it's a folder
        current_index = -1
        if is_folder:
            current_index = self.results_section.result_tree.indexOfTopLevelItem(selected[0])
            
        total_items = self.results_section.result_tree.topLevelItemCount()
        
        # Update control buttons
        self.control_buttons.update_button_states(has_selection, is_folder, current_index, total_items)
        
        # Update letter section
        self.letter_section.set_button_enabled(total_items > 0)
        
        # Update merge button
        if self.merge_btn:
            self.merge_btn.setEnabled(total_items > 0)
        
    def move_item_up(self) -> None:
        """Move the selected folder item up in the list."""
        self.results_section.move_item_up()
        self.update_button_states()
        
    def move_item_down(self) -> None:
        """Move the selected folder item down in the list."""
        self.results_section.move_item_down()
        self.update_button_states()
        
    def remove_selected(self) -> None:
        """Remove the selected folder item."""
        self.results_section.remove_selected_item()
        self.update_button_states()
        
    def add_pdf_pair(self, files: list) -> None:
        """Add a new PDF pair to the list."""
        try:
            # Convert to Path objects
            pdfs = [Path(f) for f in files]
            
            # Analyze PDFs to determine which is the map
            map_pdf = None
            doc_pdf = None
            wayleave_type = "unknown"
            
            for pdf in pdfs:
                if PDFContent.is_map_pdf(pdf):
                    map_pdf = pdf
                else:
                    doc_pdf = pdf
                    # Analyze wayleave type for document PDF
                    wayleave_type = PDFContent.analyze_wayleave_type(pdf)
                    
            if not map_pdf or not doc_pdf:
                QMessageBox.warning(
                    self,
                    "Invalid PDFs",
                    "Could not identify a map PDF and a document PDF in the selection."
                )
                return
                
            # Create new folder item
            try:
                folder_path = map_pdf.parent.resolve()
            except ValueError:
                # If the PDF is not in a subfolder of selected_folder,
                # use just the parent folder name
                folder_path = map_pdf.parent.name
                
            pdf_pair = PDFPair(doc_pdf, map_pdf, [], wayleave_type)
            self.results_section.add_pdf_pair(str(folder_path), pdf_pair)
            self.update_button_states()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error adding PDF pair: {str(e)}"
            )
            
    def merge_and_compress_pdfs(self) -> None:
        """Merge and compress PDFs."""
        try:
            if not self.selected_folder:
                return
                
            # Get all PDF paths from the results tree
            pdf_paths = []
            for i in range(self.results_section.result_tree.topLevelItemCount()):
                item = self.results_section.result_tree.topLevelItem(i)
                for j in range(item.childCount()):
                    child = item.child(j)
                    pdf_path = Path(child.toolTip(0).replace("Full path: ", "").split("\n")[0])
                    pdf_paths.append(pdf_path)
                    
            if not pdf_paths:
                QMessageBox.warning(self, "No PDFs", "No PDFs found to merge.")
                return
                
            output_path = self.selected_folder / "Print.pdf"
            if merge_and_compress_pdfs(pdf_paths, output_path):
                QMessageBox.information(self, "Success", "Successfully merged and compressed PDFs!")
            else:
                QMessageBox.critical(self, "Error", "Failed to merge and compress PDFs.")
                
        except Exception as e:
            logger.error(f"Error merging PDFs: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error merging PDFs: {str(e)}"
            )
    
    def handle_letter_generation_error(self, error: Exception, details: dict) -> None:
        """Handle errors during letter generation."""
        error_message = str(error)
        if isinstance(error, GenerationError):
            # Handle specific GenerationError with more details
            retry_count = details.get('retry_count', 0)
            fallback_used = details.get('fallback_used', False)
            
            error_details = (
                f"An error occurred during letter generation:\n\n{error_message}\n\n"
                f"Conversion attempts: {retry_count}\n"
                f"Fallback method used: {'Yes' if fallback_used else 'No'}\n\n"
                "Please check the following:\n"
                "1. Ensure you have write permissions for the output directory.\n"
                "2. Verify that Microsoft Word is properly installed and accessible.\n"
                "3. Check if there are any issues with the input PDF files.\n"
                "4. Restart the application and try again.\n"
                "5. If the problem persists, please contact support."
            )
            
            QMessageBox.critical(
                self,
                "Letter Generation Error",
                error_details
            )
        else:
            # Handle other general errors
            QMessageBox.critical(
                self,
                "Error",
                f"An unexpected error occurred during letter generation:\n\n{error_message}"
            )
        logger.error(f"Letter generation error: {error_message}")
        logger.error(f"Error details: {details}")
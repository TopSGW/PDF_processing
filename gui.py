"""Module containing the GUI components of the application."""
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QLabel, QProgressBar, QMessageBox,
    QHBoxLayout, QFrame, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from constants import (
    WINDOW_TITLE, DEFAULT_FOLDER_LABEL, SELECT_FOLDER_BUTTON_TEXT,
    NO_RESULTS_MESSAGE, FOLDER_DIALOG_TITLE, PROCESSED_FOLDER_MARKER
)
from pdf_scanner import ScannerThread, PDFPair

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
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(800, 600)  # Set a reasonable default size
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create header section
        self.create_header_section(main_layout)
        
        # Create progress section
        self.create_progress_section(main_layout)
        
        # Create results section
        self.create_results_section(main_layout)
        
        self.setLayout(main_layout)
        
    def create_header_section(self, parent_layout: QVBoxLayout) -> None:
        """Create the header section of the UI."""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        
        header_layout = QVBoxLayout()
        
        # Folder selection label
        self.folder_label = QLabel(DEFAULT_FOLDER_LABEL)
        self.folder_label.setWordWrap(True)
        header_layout.addWidget(self.folder_label)
        
        # Select folder button
        self.select_button = QPushButton(SELECT_FOLDER_BUTTON_TEXT)
        self.select_button.clicked.connect(self.select_home_folder)
        self.select_button.setFixedWidth(200)
        header_layout.addWidget(self.select_button, alignment=Qt.AlignLeft)
        
        header_frame.setLayout(header_layout)
        parent_layout.addWidget(header_frame)
        
    def create_progress_section(self, parent_layout: QVBoxLayout) -> None:
        """Create the progress section of the UI."""
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate state
        self.progress.setVisible(False)
        parent_layout.addWidget(self.progress)
        
    def create_results_section(self, parent_layout: QVBoxLayout) -> None:
        """Create the results section of the UI."""
        results_frame = QFrame()
        results_frame.setFrameStyle(QFrame.StyledPanel)
        
        results_layout = QVBoxLayout()
        
        # Results tree
        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderLabels(["Folders and PDFs"])
        self.result_tree.setAlternatingRowColors(True)
        self.result_tree.setIndentation(20)
        results_layout.addWidget(self.result_tree)
        
        results_frame.setLayout(results_layout)
        parent_layout.addWidget(results_frame)
        
    def select_home_folder(self) -> None:
        """Handle the folder selection dialog."""
        try:
            folder = QFileDialog.getExistingDirectory(
                self,
                FOLDER_DIALOG_TITLE,
            )
            
            if folder:
                logger.debug(f"Selected folder: {folder}")
                self.selected_folder = Path(folder)
                self.folder_label.setText(f"Selected Folder: {folder}")
                self.scan_folder(folder)
                
        except Exception as e:
            logger.error(f"Error selecting folder: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error selecting folder: {str(e)}"
            )
            
    def scan_folder(self, home_folder: str) -> None:
        """
        Start scanning the selected folder.
        
        Args:
            home_folder: Path to the folder to scan
        """
        try:
            logger.debug(f"Starting scan of folder: {home_folder}")
            # Clear previous results
            self.result_tree.clear()
            
            # Show the progress bar
            self.progress.setVisible(True)
            self.select_button.setEnabled(False)
            
            # Create and start scanning thread
            self.scanner_thread = ScannerThread(home_folder)
            self.scanner_thread.scan_finished.connect(self.handle_scan_results)
            self.scanner_thread.start()
            
        except Exception as e:
            logger.error(f"Error starting scan: {e}")
            self.progress.setVisible(False)
            self.select_button.setEnabled(True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error starting scan: {str(e)}"
            )
            
    def create_folder_item(self, folder_path: str, pdf_pair: PDFPair, is_processed: bool) -> QTreeWidgetItem:
        """
        Create a folder item for the tree widget.
        
        Args:
            folder_path: Path to the folder
            pdf_pair: PDFPair containing the folder's PDFs
            is_processed: Whether the folder has been processed before
            
        Returns:
            QTreeWidgetItem for the folder
        """
        item = QTreeWidgetItem()
        status = "✓" if is_processed else ""
        
        # Count PDFs
        total_pdfs = sum(1 for pdf in [pdf_pair.document_pdf, pdf_pair.map_pdf] if pdf is not None)
        
        item.setText(0, f"📁 {folder_path} ({total_pdfs} PDFs) {status}")
        
        if self.selected_folder:
            full_path = str(self.selected_folder / folder_path)
            tooltip = f"Full path: {full_path}\n"
            tooltip += f"Document PDF: {'Yes' if pdf_pair.document_pdf else 'No'}\n"
            tooltip += f"Map PDF: {'Yes' if pdf_pair.map_pdf else 'No'}"
            item.setToolTip(0, tooltip)
        
        # Set background color for processed folders
        if is_processed:
            item.setBackground(0, QColor("#E8F5E9"))  # Light green
            
        return item
            
    def create_pdf_item(self, pdf_path: Path, pdf_type: str = "") -> QTreeWidgetItem:
        """
        Create a PDF item for the tree widget.
        
        Args:
            pdf_path: Path to the PDF file
            pdf_type: Type of PDF (Document/Map)
            
        Returns:
            QTreeWidgetItem for the PDF
        """
        item = QTreeWidgetItem()
        
        # Set icon and format based on PDF type
        if pdf_type == "Document":
            item.setText(0, f"📄 {pdf_path.name} (Document)")
            item.setForeground(0, QColor("#1976D2"))  # Blue for Document
        else:  # Map
            item.setText(0, f"🗺️ {pdf_path.name} (Map)")
            item.setForeground(0, QColor("#388E3C"))  # Green for Map
            
        item.setToolTip(0, f"Full path: {pdf_path}")
        return item
            
    def handle_scan_results(self, results: List[Tuple[str, PDFPair]]) -> None:
        """
        Handle the results from the scanner thread.
        
        Args:
            results: List of tuples containing (relative_path, PDFPair)
        """
        try:
            logger.debug(f"Handling scan results: {len(results)} folders found")
            # Hide progress bar and re-enable button
            self.progress.setVisible(False)
            self.select_button.setEnabled(True)
            
            # Display results
            if not results:
                logger.info("No results found")
                no_results = QTreeWidgetItem()
                no_results.setText(0, NO_RESULTS_MESSAGE)
                self.result_tree.addTopLevelItem(no_results)
            else:
                # Sort results by path for better organization
                sorted_results = sorted(results, key=lambda x: x[0])
                logger.debug(f"Processing {len(sorted_results)} sorted results")
                
                for relative_path, pdf_pair in sorted_results:
                    # Create folder item
                    is_processed = (Path(self.selected_folder) / relative_path / PROCESSED_FOLDER_MARKER).exists() \
                        if self.selected_folder else False
                    folder_item = self.create_folder_item(relative_path, pdf_pair, is_processed)
                    self.result_tree.addTopLevelItem(folder_item)
                    
                    # Add Document PDF if exists
                    if pdf_pair.document_pdf:
                        doc_item = self.create_pdf_item(pdf_pair.document_pdf, "Document")
                        folder_item.addChild(doc_item)
                    
                    # Add Map PDF if exists
                    if pdf_pair.map_pdf:
                        map_item = self.create_pdf_item(pdf_pair.map_pdf, "Map")
                        folder_item.addChild(map_item)
                    
                # Expand all items for better visibility
                self.result_tree.expandAll()
                logger.debug("Finished processing results")
                        
        except Exception as e:
            logger.error(f"Error handling scan results: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error displaying results: {str(e)}"
            )
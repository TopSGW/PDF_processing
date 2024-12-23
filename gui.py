"""Module containing the GUI components of the application."""
import logging
import fitz
from pathlib import Path
from typing import List, Tuple, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QLabel, QProgressBar, QMessageBox,
    QHBoxLayout, QFrame, QTreeWidget, QTreeWidgetItem,
    QToolButton, QStyle, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from constants import (
    WINDOW_TITLE, DEFAULT_FOLDER_LABEL, SELECT_FOLDER_BUTTON_TEXT,
    NO_RESULTS_MESSAGE, FOLDER_DIALOG_TITLE, PROCESSED_FOLDER_MARKER,
    MOVE_UP_TEXT, MOVE_DOWN_TEXT, REMOVE_PAIR_TEXT, ADD_PAIR_TEXT,
    PROCESS_TEXT, ADD_PDF_DIALOG_TITLE, REMOVE_CONFIRM_TITLE,
    REMOVE_CONFIRM_TEXT, PDF_EXTENSION, MERGE_AND_COMPRESS_PDFS,
    GENERATE_ANNUAL_LETTER, GENERATE_15_YEAR_LETTER,
    GENERATE_LETTER_ERROR, GENERATE_LETTER_SUCCESS, LETTER_SAVE_DIALOG
)
from pdf_scanner import ScannerThread, PDFPair, PDFContent
from letter_generator import generate_letter_for_pdf, ContentError, WayleaveLetterGenerator

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
        self.letter_generator = WayleaveLetterGenerator()
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(800, 600)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create header section
        self.create_header_section(main_layout)
        
        # Create progress section
        self.create_progress_section(main_layout)
        
        # Create main content area with controls
        content_layout = QHBoxLayout()
        
        # Create results section
        self.create_results_section(content_layout)
        
        # Create control buttons section
        self.create_control_buttons(content_layout)
        
        main_layout.addLayout(content_layout)
        
        # Create letter generation buttons
        letter_buttons_layout = QHBoxLayout()
        
        # Create Letters button for all PDFs
        self.create_all_letters_btn = QPushButton("Create Letters")
        self.create_all_letters_btn.setEnabled(False)
        self.create_all_letters_btn.clicked.connect(self.generate_all_letters)
        letter_buttons_layout.addWidget(self.create_all_letters_btn)
        
        # Individual letter generation buttons
        self.annual_letter_btn = QPushButton(GENERATE_ANNUAL_LETTER)
        self.annual_letter_btn.setEnabled(False)
        self.annual_letter_btn.clicked.connect(lambda: self.generate_letter("annual"))
        letter_buttons_layout.addWidget(self.annual_letter_btn)
        
        self.fifteen_year_letter_btn = QPushButton(GENERATE_15_YEAR_LETTER)
        self.fifteen_year_letter_btn.setEnabled(False)
        self.fifteen_year_letter_btn.clicked.connect(lambda: self.generate_letter("15-year"))
        letter_buttons_layout.addWidget(self.fifteen_year_letter_btn)
        
        main_layout.addLayout(letter_buttons_layout)
        
        # Add process button at bottom
        self.merge_btn = QPushButton(MERGE_AND_COMPRESS_PDFS)
        self.merge_btn.setEnabled(False)
        self.merge_btn.clicked.connect(self.merge_and_compress_pdfs)
        main_layout.addWidget(self.merge_btn)
        
        self.setLayout(main_layout)

    def generate_all_letters(self) -> None:
        """Generate letters for all PDFs in their respective sub-folders."""
        try:
            success_count = 0
            error_count = 0
            error_messages = []

            generated_letters = []

            # Iterate through all folders
            for i in range(self.result_tree.topLevelItemCount()):
                folder_item = self.result_tree.topLevelItem(i)
                
                # Find document PDF in this folder
                doc_pdf = None
                wayleave_type = None
                
                for j in range(folder_item.childCount()):
                    child = folder_item.child(j)
                    if "(Document)" in child.text(0):
                        doc_pdf = Path(child.toolTip(0).replace("Full path: ", "").split("\n")[0])
                        # Get wayleave type from tooltip
                        tooltip = child.toolTip(0)
                        if "Wayleave Type: " in tooltip:
                            wayleave_type = tooltip.split("Wayleave Type: ")[1]
                        break
                
                if doc_pdf and doc_pdf.exists():
                    try:
                        # Extract content from PDF
                        content = PDFContent.extract_text_content(doc_pdf)
                        page_count = PDFContent.get_page_count(doc_pdf)
                        
                        if content:
                            # Determine letter type based on the document content
                            letter_type = wayleave_type if wayleave_type in ["annual", "15-year"] else "annual"
                            
                            # Generate letter content
                            letter_content, suggested_filename = self.letter_generator.generate_letter(
                                content, letter_type, page_count=page_count
                            )
                            
                            # Save in the same folder as the document PDF
                            save_path = doc_pdf.parent / suggested_filename
                            self.letter_generator.create_pdf_letter(letter_content, save_path)

                            docx_filename = suggested_filename.replace(".pdf", ".docx")
                            docx_save_path = doc_pdf.parent / docx_filename
                            self.letter_generator.create_word_letter(letter_content, docx_save_path)
                            
                            success_count += 1
                            generated_letters.append(save_path)
                            
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f"Error processing {doc_pdf.name}: {str(e)}")
            
            if generated_letters:
                try:
                    merged_path = self.selected_folder / "Print 2.pdf"
                    merged_doc = fitz.open()
                    
                    for letter_pdf in generated_letters:
                        with fitz.open(letter_pdf) as src_doc:
                            merged_doc.insert_pdf(src_doc)
                    
                    # optionally flatten / deflate if needed
                    merged_doc.save(merged_path, deflate=True, garbage=4)
                    merged_doc.close()
                except Exception as merge_err:
                    logger.error(f"Error merging final PDF: {merge_err}")
                    error_messages.append(f"Error merging final PDF: {merge_err}")
            # Show summary message
            message = f"Letter Generation Complete\n\n"
            message += f"Successfully generated: {success_count} letters\n"
            if error_count > 0:
                message += f"Errors encountered: {error_count}\n\n"
                message += "Error Details:\n" + "\n".join(error_messages)
            
            QMessageBox.information(
                self,
                "Generate Letters Results",
                message
            )
            
        except Exception as e:
            logger.error(f"Error generating letters: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error generating letters: {str(e)}"
            )

    # [Previous methods remain unchanged...]
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
        
    def create_results_section(self, parent_layout: QHBoxLayout) -> None:
        """Create the results section of the UI."""
        results_frame = QFrame()
        results_frame.setFrameStyle(QFrame.StyledPanel)
        
        results_layout = QVBoxLayout()
        
        # Results tree
        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderLabels(["Folders and PDFs"])
        self.result_tree.setAlternatingRowColors(True)
        self.result_tree.setIndentation(20)
        self.result_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.result_tree.itemSelectionChanged.connect(self.update_button_states)
        results_layout.addWidget(self.result_tree)
        
        results_frame.setLayout(results_layout)
        parent_layout.addWidget(results_frame)
        
    def create_control_buttons(self, parent_layout: QHBoxLayout) -> None:
        """Create the control buttons section."""
        buttons_frame = QFrame()
        buttons_frame.setFixedWidth(100)
        buttons_frame.setFrameStyle(QFrame.StyledPanel)
        
        buttons_layout = QVBoxLayout()
        buttons_layout.setAlignment(Qt.AlignTop)
        
        # Move Up button
        self.move_up_btn = QPushButton(MOVE_UP_TEXT)
        self.move_up_btn.setEnabled(False)
        self.move_up_btn.clicked.connect(self.move_item_up)
        buttons_layout.addWidget(self.move_up_btn)
        
        # Move Down button
        self.move_down_btn = QPushButton(MOVE_DOWN_TEXT)
        self.move_down_btn.setEnabled(False)
        self.move_down_btn.clicked.connect(self.move_item_down)
        buttons_layout.addWidget(self.move_down_btn)
        
        # Add spacing
        buttons_layout.addSpacing(20)
        
        # Remove button
        self.remove_btn = QPushButton(REMOVE_PAIR_TEXT)
        self.remove_btn.setEnabled(False)
        self.remove_btn.clicked.connect(self.remove_selected)
        buttons_layout.addWidget(self.remove_btn)
        
        # Add PDF Pair button
        self.add_btn = QPushButton(ADD_PAIR_TEXT)
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self.add_pdf_pair)
        buttons_layout.addWidget(self.add_btn)

        buttons_layout.addStretch()
        buttons_frame.setLayout(buttons_layout)
        parent_layout.addWidget(buttons_frame)
        
    def update_button_states(self) -> None:
        """Update the enabled state of control buttons based on selection."""
        selected = self.result_tree.selectedItems()
        has_selection = bool(selected)
        is_folder = has_selection and selected[0].childCount() > 0
        
        # Get the selected item's index if it's a folder
        current_index = -1
        if is_folder:
            current_index = self.result_tree.indexOfTopLevelItem(selected[0])
        
        # Enable/disable standard buttons
        self.move_up_btn.setEnabled(is_folder and current_index > 0)
        self.move_down_btn.setEnabled(is_folder and current_index < self.result_tree.topLevelItemCount() - 1)
        self.remove_btn.setEnabled(is_folder)
        self.add_btn.setEnabled(bool(self.selected_folder))
        self.merge_btn.setEnabled(self.result_tree.topLevelItemCount() > 0)
        
        # Enable Create Letters button if there are any items
        self.create_all_letters_btn.setEnabled(self.result_tree.topLevelItemCount() > 0)
        
        # Enable/disable letter generation buttons based on document selection
        has_document = False
        wayleave_type = "unknown"
        if has_selection:
            selected_item = selected[0]
            if selected_item.childCount() > 0:  # If it's a folder
                for i in range(selected_item.childCount()):
                    child = selected_item.child(i)
                    if "(Document)" in child.text(0):
                        has_document = True
                        # Extract wayleave type from tooltip
                        tooltip = child.toolTip(0)
                        if "Wayleave Type: " in tooltip:
                            wayleave_type = tooltip.split("Wayleave Type: ")[1]
                        break
            elif "(Document)" in selected_item.text(0):  # If it's a document
                has_document = True
                # Extract wayleave type from tooltip
                tooltip = selected_item.toolTip(0)
                if "Wayleave Type: " in tooltip:
                    wayleave_type = tooltip.split("Wayleave Type: ")[1]
        
        # Enable appropriate letter button based on wayleave type
        self.annual_letter_btn.setEnabled(has_document and (wayleave_type == "annual" or wayleave_type == "unknown"))
        self.fifteen_year_letter_btn.setEnabled(has_document and (wayleave_type == "15-year" or wayleave_type == "unknown"))
        
    def get_selected_document_pdf(self) -> Optional[Path]:
        """Get the selected document PDF path."""
        selected = self.result_tree.selectedItems()
        if not selected:
            return None
            
        selected_item = selected[0]
        if selected_item.childCount() > 0:  # If folder is selected
            for i in range(selected_item.childCount()):
                child = selected_item.child(i)
                if "(Document)" in child.text(0):
                    return Path(child.toolTip(0).replace("Full path: ", "").split("\n")[0])
        elif "(Document)" in selected_item.text(0):  # If document is selected
            return Path(selected_item.toolTip(0).replace("Full path: ", "").split("\n")[0])
            
        return None
        
    def generate_letter(self, letter_type: str) -> None:
        """
        Generate a letter for the selected document.
        
        Args:
            letter_type: Type of letter to generate ("annual" or "15-year")
        """
        try:
            # Get selected document PDF
            pdf_path = self.get_selected_document_pdf()
            if not pdf_path:
                QMessageBox.warning(
                    self,
                    "No Document Selected",
                    "Please select a document PDF to generate a letter."
                )
                return
                
            if not pdf_path.exists():
                QMessageBox.critical(
                    self,
                    GENERATE_LETTER_ERROR,
                    f"PDF file not found: {pdf_path}"
                )
                return
                
            # Extract content from PDF
            from pdf_scanner import PDFContent
            content = PDFContent.extract_text_content(pdf_path)
            page_count = PDFContent.get_page_count(pdf_path)
            if not content:
                QMessageBox.critical(
                    self,
                    GENERATE_LETTER_ERROR,
                    "Failed to extract content from PDF"
                )
                return
            
            # Generate letter content
            try:
                letter_content, suggested_filename = self.letter_generator.generate_letter(content, letter_type, page_count=page_count)
            except ContentError as e:
                QMessageBox.critical(
                    self,
                    GENERATE_LETTER_ERROR,
                    f"Error extracting information from PDF: {str(e)}\n\n"
                    f"This might be because the selected PDF is not a valid {letter_type} wayleave document."
                )
                return
                
            try:
                # Save the letter in the same folder as the document PDF
                save_path = pdf_path.parent / suggested_filename
                
                # Create the PDF with proper formatting
                self.letter_generator.create_pdf_letter(letter_content, save_path)
                
                QMessageBox.information(
                    self,
                    GENERATE_LETTER_SUCCESS,
                    f"Letter has been generated and saved to:\n{save_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    GENERATE_LETTER_ERROR,
                    f"Error saving letter: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Error generating letter: {e}")
            QMessageBox.critical(
                self,
                GENERATE_LETTER_ERROR,
                f"Error generating letter: {str(e)}"
            )
            
    def move_item_up(self) -> None:
        """Move the selected folder item up in the list."""
        item = self.result_tree.selectedItems()[0]
        index = self.result_tree.indexOfTopLevelItem(item)
        if index > 0:
            self.result_tree.takeTopLevelItem(index)
            self.result_tree.insertTopLevelItem(index - 1, item)
            self.result_tree.setCurrentItem(item)
            
    def move_item_down(self) -> None:
        """Move the selected folder item down in the list."""
        item = self.result_tree.selectedItems()[0]
        index = self.result_tree.indexOfTopLevelItem(item)
        if index < self.result_tree.topLevelItemCount() - 1:
            self.result_tree.takeTopLevelItem(index)
            self.result_tree.insertTopLevelItem(index + 1, item)
            self.result_tree.setCurrentItem(item)
            
    def remove_selected(self) -> None:
        """Remove the selected folder item after confirmation."""
        reply = QMessageBox.question(
            self,
            REMOVE_CONFIRM_TITLE,
            REMOVE_CONFIRM_TEXT,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            item = self.result_tree.selectedItems()[0]
            index = self.result_tree.indexOfTopLevelItem(item)
            self.result_tree.takeTopLevelItem(index)
            self.update_button_states()
            
    def add_pdf_pair(self) -> None:
        """Add a new PDF pair to the list."""
        if not self.selected_folder:
            return
            
        # Open file dialog for selecting PDFs
        files, _ = QFileDialog.getOpenFileNames(
            self,
            ADD_PDF_DIALOG_TITLE,
            str(self.selected_folder),
            f"PDF files (*{PDF_EXTENSION})"
        )
        
        if len(files) != 2:
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Please select exactly two PDF files (one document and one map)."
            )
            return
            
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
                
            folder_item = self.create_folder_item(str(folder_path), PDFPair(doc_pdf, map_pdf, [], wayleave_type), False)
            
            # Add PDFs to folder item
            doc_item = self.create_pdf_item(doc_pdf, "Document", wayleave_type)
            map_item = self.create_pdf_item(map_pdf, "Map")
            folder_item.addChild(doc_item)
            folder_item.addChild(map_item)
            
            # Add to tree
            self.result_tree.addTopLevelItem(folder_item)
            folder_item.setExpanded(True)
            self.update_button_states()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error adding PDF pair: {str(e)}"
            )
        
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
        """Create a folder item for the tree widget."""
        item = QTreeWidgetItem()
        status = "✓" if is_processed else ""
        total_pdfs = sum(1 for pdf in [pdf_pair.document_pdf, pdf_pair.map_pdf] if pdf is not None)
        wayleave_info = f" [{pdf_pair.wayleave_type}]" if pdf_pair.wayleave_type != "unknown" else ""
        item.setText(0, f"📁 {folder_path} ({total_pdfs} PDFs){wayleave_info} {status}")

        if self.selected_folder:
            folder_path_obj = Path(folder_path)
            if folder_path_obj.is_absolute():
                full_path = folder_path
            else:
                full_path = str(self.selected_folder / folder_path)
            
            tooltip = f"Full path: {full_path}\n"
            tooltip += f"Document PDF: {'Yes' if pdf_pair.document_pdf else 'No'}\n"
            tooltip += f"Map PDF: {'Yes' if pdf_pair.map_pdf else 'No'}\n"
            tooltip += f"Wayleave Type: {pdf_pair.wayleave_type}"
            item.setToolTip(0, tooltip)

        if is_processed:
            item.setBackground(0, QColor("#E8F5E9"))  # Light green
        
        return item      
          
    def create_pdf_item(self, pdf_path: Path, pdf_type: str = "", wayleave_type: str = "") -> QTreeWidgetItem:
        """Create a PDF item for the tree widget."""
        item = QTreeWidgetItem()
        
        # Set icon and format based on PDF type
        if pdf_type == "Document":
            wayleave_info = f" [{wayleave_type}]" if wayleave_type and wayleave_type != "unknown" else ""
            item.setText(0, f"📄 {pdf_path.name} (Document){wayleave_info}")
            item.setForeground(0, QColor("#1976D2"))  # Blue for Document
        else:  # Map
            item.setText(0, f"🗺️ {pdf_path.name} (Map)")
            item.setForeground(0, QColor("#388E3C"))  # Green for Map
            
        item.setToolTip(0, f"Full path: {pdf_path}\nWayleave Type: {wayleave_type}")
        return item
            
    def handle_scan_results(self, results: List[Tuple[str, PDFPair]]) -> None:
        """Handle the results from the scanner thread."""
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
                        doc_item = self.create_pdf_item(pdf_pair.document_pdf, "Document", pdf_pair.wayleave_type)
                        folder_item.addChild(doc_item)
                    
                    # Add Map PDF if exists
                    if pdf_pair.map_pdf:
                        map_item = self.create_pdf_item(pdf_pair.map_pdf, "Map")
                        folder_item.addChild(map_item)
                    
                # Expand all items for better visibility
                self.result_tree.expandAll()
                logger.debug("Finished processing results")
                
            # Enable/disable buttons based on results
            self.update_button_states()
                        
        except Exception as e:
            logger.error(f"Error handling scan results: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error displaying results: {str(e)}"
            )
    
    def merge_and_compress_pdfs(self):
        """Process the selected PDF pairs."""
        # Get all folder items
        folders = []
        for i in range(self.result_tree.topLevelItemCount()):
            item = self.result_tree.topLevelItem(i)
            folder_path = item.text(0).split(" (")[0].replace("📁 ", "")
            
            # Get document and map PDFs
            doc_pdf = None
            map_pdf = None
            
            for j in range(item.childCount()):
                child = item.child(j)
                pdf_path = Path(child.toolTip(0).replace("Full path: ", "").split("\n")[0])
                if "(Document)" in child.text(0):
                    doc_pdf = pdf_path
                else:
                    map_pdf = pdf_path
                    
            folders.append((folder_path, PDFPair(doc_pdf, map_pdf, [])))

        pdf_paths = []
        for folder_path, pair in folders:
            # Order here is Document first, then Map
            # If you need a different order, adjust accordingly.
            if pair.document_pdf:
                pdf_paths.append(pair.document_pdf)
            if pair.map_pdf:
                pdf_paths.append(pair.map_pdf)

        output_path = self.selected_folder / "Print.pdf"
        merged_doc = fitz.open()

        # Append all PDFs in specified order
        for pdf_path in pdf_paths:
            with fitz.open(pdf_path) as src_doc:
                # Append each page
                merged_doc.insert_pdf(src_doc)

        # Remove all annotations from each page to "flatten" the document
        # (This removes pop-ups, comments, highlights, etc.)
        for page_index in range(len(merged_doc)):
            page = merged_doc[page_index]
            annot = page.first_annot
            while annot:
                page.delete_annot(annot)
                annot = page.first_annot

        merged_doc.save(output_path, deflate=True, garbage=4)
        merged_doc.close()

        QMessageBox.information(
            self,
            "Merge and Compress",
            f"Successfully merged!"
        )
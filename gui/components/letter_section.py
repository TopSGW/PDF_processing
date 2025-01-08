"""Module containing the letter generation section of the GUI."""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from num2words import num2words

import fitz
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QPushButton, QMessageBox,
    QLabel, QHBoxLayout, QStyle
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from constants import (
    GENERATE_LETTER_ERROR,
    GENERATE_LETTER_SUCCESS,
    LETTER_SAVE_DIALOG
)
from letter_generator import (
    generate_letter,
    generate_second_letter,
    create_word_letter,
    convert_pdf_letter,
    extract_names_and_address_annual,
    extract_names_and_address_fifteen_year,
    format_names,
    format_address,
    generate_filename
)
from pdf_scanner import PDFContent
from gui.components.batch_edit_details_dialog import BatchEditDetailsDialog

logger = logging.getLogger(__name__)

class StyledButton(QPushButton):
    """Custom styled button with hover effects."""
    
    def __init__(self, text, icon_type=None, primary=True):
        super().__init__(text)
        self.setMinimumHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        
        if icon_type:
            self.setIcon(self.style().standardIcon(icon_type))
        
        # Set object name for styling
        self.setObjectName("primary" if primary else "secondary")
        
        # Apply styles
        self.setStyleSheet("""
            QPushButton#primary {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#primary:hover {
                background-color: #357abd;
            }
            QPushButton#primary:pressed {
                background-color: #2d6da3;
            }
            QPushButton#primary:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QPushButton#secondary {
                background-color: #f8f9fa;
                color: #4a90e2;
                border: 2px solid #4a90e2;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#secondary:hover {
                background-color: #e9ecef;
            }
            QPushButton#secondary:pressed {
                background-color: #dde2e6;
            }
            QPushButton#secondary:disabled {
                border-color: #cccccc;
                color: #666666;
            }
        """)

class LetterSection(QFrame):
    """Letter generation section of the application."""

    def __init__(self, progress_callback=None) -> None:
        """
        Initialize the letter section.
        
        Args:
            progress_callback: Callback to update progress UI
        """
        super().__init__()
        self.selected_folder: Optional[Path] = None
        self.progress_callback = progress_callback
        
        # Initialize UI components
        self.create_all_letters_btn: Optional[StyledButton] = None
        self.merge_btn: Optional[StyledButton] = None
        self.result_tree = None  # Will be set by set_tree_widget
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        # Set frame style
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QLabel {
                color: #333333;
                font-size: 13px;
            }
            QLabel#title {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add title
        title_label = QLabel("Letter Generation")
        title_label.setObjectName("title")
        layout.addWidget(title_label)
        
        # Add description
        desc_label = QLabel("Generate letters for all selected documents. You can edit all details at once before letters are created.")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Button container
        button_container = QHBoxLayout()
        
        # Create Letters button with icon
        self.create_all_letters_btn = StyledButton(
            "Create Letters",
            QStyle.SP_FileIcon,
            primary=True
        )
        self.create_all_letters_btn.setEnabled(False)
        self.create_all_letters_btn.clicked.connect(self.generate_all_letters)
        button_container.addWidget(self.create_all_letters_btn)
        
        button_container.addStretch()
        layout.addLayout(button_container)
        
        self.setLayout(layout)
        
    def set_selected_folder(self, folder: Optional[Path]) -> None:
        """Set the selected folder path."""
        self.selected_folder = folder
        
    def set_tree_widget(self, tree_widget) -> None:
        """Set the tree widget reference."""
        self.result_tree = tree_widget
        
    def set_merge_button(self, merge_btn: QPushButton) -> None:
        """Set the merge button reference."""
        self.merge_btn = merge_btn
        
    def set_button_enabled(self, enabled: bool) -> None:
        """Enable or disable the create letters button."""
        if self.create_all_letters_btn:
            self.create_all_letters_btn.setEnabled(enabled)
            
    def update_progress(self, current: int, total: int, message: str) -> None:
        """Update the progress UI through callback."""
        if self.progress_callback:
            self.progress_callback(current, total, message)
            
    def generate_all_letters(self) -> None:
        """Generate letters for all PDFs in their respective sub-folders."""
        try:
            if not self.result_tree:
                return

            # Count total documents to process
            total_docs = 0
            documents_info = []
            
            # First pass: collect all document information
            for i in range(self.result_tree.topLevelItemCount()):
                folder_item = self.result_tree.topLevelItem(i)
                for j in range(folder_item.childCount()):
                    child = folder_item.child(j)
                    if "(Document)" in child.text(0):
                        total_docs += 1
                        doc_path = Path(child.toolTip(0).replace("Full path: ", "").split("\n")[0])
                        
                        # Get wayleave type from tooltip
                        tooltip = child.toolTip(0)
                        wayleave_type = "annual"
                        if "Wayleave Type: " in tooltip:
                            wayleave_type = tooltip.split("Wayleave Type: ")[1]
                        
                        if doc_path.exists():
                            try:
                                # Extract content from PDF
                                content = PDFContent.extract_text_content(doc_path)
                                
                                if content:
                                    # Extract initial details based on type
                                    if wayleave_type == "annual":
                                        info = extract_names_and_address_annual(content)
                                    else:
                                        info = extract_names_and_address_fifteen_year(content)
                                    
                                    # Add to documents info
                                    documents_info.append({
                                        'filename': doc_path.name,
                                        'path': doc_path,
                                        'names': info['full_names'],
                                        'address': info['address'],
                                        'type': wayleave_type,
                                        'content': content,
                                        'page_count': PDFContent.get_page_count(doc_path)
                                    })
                            except Exception as e:
                                logger.error(f"Error extracting info from {doc_path.name}: {e}")

            if total_docs == 0:
                QMessageBox.warning(self, "No Documents", "No documents found to process.")
                return

            if not documents_info:
                QMessageBox.warning(self, "Error", "Could not extract information from any documents.")
                return

            # Show batch edit dialog
            dialog = BatchEditDetailsDialog(documents_info, self)
            if dialog.exec_() == BatchEditDetailsDialog.Accepted:
                # Get edited values
                edited_docs = dialog.get_values()
                
                # Update progress
                self.update_progress(0, total_docs, "Starting letter generation...")

                success_count = 0
                error_count = 0
                error_messages = []
                generated_letters = []

                # Disable buttons during processing
                self.create_all_letters_btn.setEnabled(False)
                if self.merge_btn:
                    self.merge_btn.setEnabled(False)

                # Process each document with edited values
                for current_doc, edited_info in enumerate(edited_docs, 1):
                    try:
                        self.update_progress(
                            current_doc,
                            total_docs,
                            f"Processing document {current_doc} of {total_docs}: {edited_info['filename']}"
                        )

                        # Find original document info
                        original_doc = next(
                            (doc for doc in documents_info if doc['filename'] == edited_info['filename']),
                            None
                        )
                        
                        if original_doc:
                            # Generate main letter using edited values
                            letter_content, suggested_filename = generate_letter(
                                original_doc['content'],
                                letter_type=edited_info['type'],
                                page_count=original_doc['page_count'],
                                override_names=edited_info['names'],
                                override_address=edited_info['address']
                            )
                            
                            # Generate second letter using edited values
                            second_letter_content, _ = generate_second_letter(
                                original_doc['content'],
                                letter_type=edited_info['type'],
                                override_names=edited_info['names'],
                                override_address=edited_info['address']
                            )
                            
                            # Save paths
                            doc_path = original_doc['path']
                            save_path = doc_path.parent / suggested_filename
                            docx_save_path = save_path.with_suffix('.docx')
                            second_letter_path = doc_path.parent / "Wayleave and Cheque Enclosed - Good Printer.docx"
                            
                            # Generate documents
                            create_word_letter(letter_content, docx_save_path)
                            convert_pdf_letter(letter_content, save_path)
                            create_word_letter(second_letter_content, second_letter_path)

                            success_count += 1
                            generated_letters.append(save_path)
                            
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f"Error processing {edited_info['filename']}: {str(e)}")
            
                if generated_letters:
                    self.update_progress(total_docs, total_docs, "Merging generated letters...")
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

                # Hide progress
                self.update_progress(0, 0, "")

                # Re-enable buttons
                self.create_all_letters_btn.setEnabled(True)
                if self.merge_btn:
                    self.merge_btn.setEnabled(True)

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
            # Ensure buttons are re-enabled on error
            self.create_all_letters_btn.setEnabled(True)
            if self.merge_btn:
                self.merge_btn.setEnabled(True)
            # Hide progress
            self.update_progress(0, 0, "")
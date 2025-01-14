"""Dialog for batch editing multiple documents' details before letter generation."""
from typing import List, Dict, Tuple
import re
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QStyle, QScrollArea,
    QWidget
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QColor
from letter_generator.document_processor import get_first_names

class BatchEditDetailsDialog(QDialog):
    """Dialog for editing multiple documents' details at once."""
    
    # Column indices for easy reference
    COL_DOCUMENT = 0
    COL_NAMES = 1
    COL_SALUTATION_NAME = 2
    COL_ADDR_1 = 3
    COL_ADDR_2 = 4
    COL_ADDR_3 = 5
    COL_ADDR_4 = 6
    COL_ADDR_5 = 7
    COL_ADDR_6 = 8
    COL_POSTCODE = 9
    COL_TYPE = 10
    
    def __init__(self, documents_info: List[Dict], parent=None) -> None:
        """
        Initialize the dialog with multiple documents' details.
        
        Args:
            documents_info: List of dictionaries containing document information
                          Each dict should have 'names', 'salutation_name', 'address', and 'filename' keys
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Batch Edit Letter Details")
        self.setModal(True)
        
        # Store original values
        self.documents_info = documents_info
        self.edited_values = []
        
        # Settings for saving column widths
        self.settings = QSettings('KoduAI', 'PDFProcessor')
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface with modern styling."""
        # Set dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                font-size: 12px;
                color: #333333;
                font-weight: bold;
            }
            QPushButton {
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton#primary {
                background-color: #4a90e2;
                color: white;
                border: none;
            }
            QPushButton#primary:hover {
                background-color: #357abd;
            }
            QPushButton#secondary {
                background-color: #f8f9fa;
                color: #4a90e2;
                border: 2px solid #4a90e2;
            }
            QPushButton#secondary:hover {
                background-color: #e9ecef;
            }
            QPushButton#danger {
                background-color: #dc3545;
                color: white;
                border: none;
            }
            QPushButton#danger:hover {
                background-color: #c82333;
            }
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: white;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 5px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
            }
            QHeaderView::section:hover {
                background-color: #e9ecef;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title section
        title_label = QLabel("Batch Edit Letter Details")
        title_label.setStyleSheet("""
            font-size: 18px;
            color: #2c3e50;
            font-weight: bold;
            padding-bottom: 10px;
        """)
        main_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Edit details for all documents at once. Each row represents a document. The 'Salutation Name' field is used in the 'Dear {}' section of the letter.")
        desc_label.setStyleSheet("font-weight: normal; color: #666;")
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        main_layout.addWidget(separator)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        headers = [
            'Document',
            'Names',
            'Salutation Name (Dear {})',
            'Address 1',
            'Address 2',
            'Address 3',
            'Address 4',
            'Address 5',
            'Address 6',
            'Postcode',
            'Type'
        ]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Set reduced default column widths
        default_widths = {
            self.COL_DOCUMENT: 150,    # Document
            self.COL_NAMES: 150,       # Names
            self.COL_SALUTATION_NAME: 150, # Salutation Name
            self.COL_ADDR_1: 120,      # Address 1
            self.COL_ADDR_2: 120,      # Address 2
            self.COL_ADDR_3: 120,      # Address 3
            self.COL_ADDR_4: 120,      # Address 4
            self.COL_ADDR_5: 120,      # Address 5
            self.COL_ADDR_6: 120,      # Address 6
            self.COL_POSTCODE: 100,    # Postcode
            self.COL_TYPE: 80,         # Type
        }
        
        # Enable horizontal scrolling
        self.table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        
        # Make all columns interactive (user-resizable)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)
        
        # Load saved column widths or use defaults
        for col, default_width in default_widths.items():
            saved_width = self.settings.value(f'batch_dialog/column_{col}_width', default_width, type=int)
            self.table.setColumnWidth(col, saved_width)
        
        # Enable column width tracking
        self.table.horizontalHeader().sectionResized.connect(self.on_column_resized)
        
        # Add rows for each document
        self.table.setRowCount(len(self.documents_info))
        for row, doc_info in enumerate(self.documents_info):
            # Document name (non-editable)
            doc_item = QTableWidgetItem(doc_info['filename'])
            doc_item.setFlags(doc_item.flags() & ~Qt.ItemIsEditable)
            doc_item.setBackground(QColor('#f8f9fa'))
            self.table.setItem(row, self.COL_DOCUMENT, doc_item)
            
            # Names
            self.table.setItem(row, self.COL_NAMES, QTableWidgetItem(doc_info['names']))
            
            # Salutation Name (for Dear {} section)
            salutation_name = doc_info.get('salutation_name', '')
            if not salutation_name:
                salutation_name = get_first_names(doc_info['names'])
            self.table.setItem(row, self.COL_SALUTATION_NAME, QTableWidgetItem(salutation_name))
            
            # Address lines 1-6
            for i in range(6):
                addr_key = f'address_{i+1}'
                value = doc_info['address'].get(addr_key, '')
                self.table.setItem(row, self.COL_ADDR_1 + i, QTableWidgetItem(value))
            
            # Postcode with special handling
            postcode = doc_info['address'].get('postcode', '')
            postcode = postcode.replace('\n', '')
            postcode_item = QTableWidgetItem(postcode)
            postcode_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            postcode_item.setFlags(postcode_item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
            self.table.setItem(row, self.COL_POSTCODE, postcode_item)
            
            # Type (non-editable)
            type_item = QTableWidgetItem(doc_info.get('type', 'annual'))
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            type_item.setBackground(QColor('#f8f9fa'))
            self.table.setItem(row, self.COL_TYPE, type_item)
        
        # Set word wrap mode for the table
        self.table.setWordWrap(False)
        
        # Create scroll area for table with both horizontal and vertical scrolling
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.table)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_layout.addWidget(scroll_area)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Create styled buttons
        save_button = QPushButton("Save All Changes")
        save_button.setObjectName("primary")
        save_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("secondary")
        cancel_button.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        
        reset_button = QPushButton("Reset All")
        reset_button.setObjectName("danger")
        reset_button.setIcon(self.style().standardIcon(QStyle.SP_DialogResetButton))
        
        # Connect buttons
        save_button.clicked.connect(self.validate_and_accept)
        cancel_button.clicked.connect(self.reject)
        reset_button.clicked.connect(self.reset_values)
        
        # Add buttons to layout
        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
    def on_column_resized(self, column: int, _, new_width: int) -> None:
        """Save the new column width when user resizes it."""
        self.settings.setValue(f'batch_dialog/column_{column}_width', new_width)
        
    def validate_postcode(self, postcode: str) -> bool:
        """Validate postcode format."""
        postcode = postcode.strip().upper()
        postcode_pattern = r'^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$'
        return bool(re.match(postcode_pattern, postcode))
            
    def validate_and_accept(self) -> None:
        """Validate all fields before accepting."""
        invalid_rows = []
        
        for row in range(self.table.rowCount()):
            # Get values from table
            names = self.table.item(row, self.COL_NAMES).text().strip()
            salutation_name = self.table.item(row, self.COL_SALUTATION_NAME).text().strip()
            postcode = self.table.item(row, self.COL_POSTCODE).text().strip()
            
            if not names:
                invalid_rows.append(f"Row {row + 1}: Names field cannot be empty")
                
            if not salutation_name:
                invalid_rows.append(f"Row {row + 1}: Salutation Name field cannot be empty")
                
            if not self.validate_postcode(postcode):
                invalid_rows.append(f"Row {row + 1}: Invalid UK postcode format")
        
        if invalid_rows:
            QMessageBox.warning(
                self,
                "Validation Errors",
                "Please correct the following errors:\n\n" + "\n".join(invalid_rows)
            )
            return
            
        self.save_values()
        self.accept()
        
    def reset_values(self) -> None:
        """Reset all fields to their original values."""
        for row, doc_info in enumerate(self.documents_info):
            # Reset names
            self.table.item(row, self.COL_NAMES).setText(doc_info['names'])
            
            # Reset salutation name
            salutation_name = doc_info.get('salutation_name', '')
            if not salutation_name:
                salutation_name = get_first_names(doc_info['names'])
            self.table.item(row, self.COL_SALUTATION_NAME).setText(salutation_name)
            
            # Reset address lines 1-6
            for i in range(6):
                addr_key = f'address_{i+1}'
                value = doc_info['address'].get(addr_key, '')
                self.table.item(row, self.COL_ADDR_1 + i).setText(value)
            
            # Reset postcode
            self.table.item(row, self.COL_POSTCODE).setText(doc_info['address'].get('postcode', ''))
        
    def save_values(self) -> None:
        """Save current values from the table."""
        self.edited_values = []
        
        for row in range(self.table.rowCount()):
            # Create address dictionary
            address = {
                'postcode': self.table.item(row, self.COL_POSTCODE).text().strip().upper()
            }
            
            # Add address lines 1-6
            for i in range(6):
                addr_key = f'address_{i+1}'
                value = self.table.item(row, self.COL_ADDR_1 + i).text().strip()
                if value:  # Only add non-empty lines
                    address[addr_key] = value
            
            # Add to edited values
            self.edited_values.append({
                'filename': self.table.item(row, self.COL_DOCUMENT).text(),
                'names': self.table.item(row, self.COL_NAMES).text().strip(),
                'salutation_name': self.table.item(row, self.COL_SALUTATION_NAME).text().strip(),
                'address': address,
                'type': self.table.item(row, self.COL_TYPE).text()
            })
    
    def get_values(self) -> List[Dict]:
        """Get the edited values."""
        return self.edited_values
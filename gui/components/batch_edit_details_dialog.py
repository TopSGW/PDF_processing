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

class BatchEditDetailsDialog(QDialog):
    """Dialog for editing multiple documents' details at once."""
    
    # Column indices for easy reference
    COL_DOCUMENT = 0
    COL_NAMES = 1
    COL_HOUSE_NUMBER = 2
    COL_CITY = 3
    COL_COUNTY = 4
    COL_POSTCODE = 5
    COL_TYPE = 6
    COL_STREET = 7
    COL_ADDR_1 = 8
    COL_ADDR_2 = 9
    COL_ADDR_3 = 10
    
    def __init__(self, documents_info: List[Dict], parent=None) -> None:
        """
        Initialize the dialog with multiple documents' details.
        
        Args:
            documents_info: List of dictionaries containing document information
                          Each dict should have 'names', 'address', and 'filename' keys
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Batch Edit Letter Details")
        self.setModal(True)
        self.setMinimumWidth(1200)
        self.setMinimumHeight(800)
        
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
        desc_label = QLabel("Edit details for all documents at once. Each row represents a document. You can resize columns by dragging their edges.")
        desc_label.setStyleSheet("font-weight: normal; color: #666;")
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
            'House/Number',
            'City',
            'County',
            'Postcode',
            'Type',
            'Street',
            'Address Line 1',
            'Address Line 2',
            'Address Line 3'
        ]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Set initial column widths
        default_widths = {
            self.COL_DOCUMENT: 200,      # Document
            self.COL_NAMES: 250,         # Names
            self.COL_HOUSE_NUMBER: 120,  # House/Number
            self.COL_CITY: 120,          # City
            self.COL_COUNTY: 120,        # County
            self.COL_POSTCODE: 100,      # Postcode
            self.COL_TYPE: 80,           # Type
            self.COL_STREET: 150,        # Street
            self.COL_ADDR_1: 150,        # Address Line 1
            self.COL_ADDR_2: 150,        # Address Line 2
            self.COL_ADDR_3: 150,        # Address Line 3
        }
        
        # Make all columns interactive (user-resizable)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
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
            
            # Parse address parts
            house_parts = doc_info['address'].get('house', '').split(',')
            house_number = house_parts[0] if house_parts else ''
            street = house_parts[1].strip() if len(house_parts) > 1 else ''
            
            # Additional address lines (after house number and street)
            addr_lines = house_parts[2:] if len(house_parts) > 2 else []
            
            # Set house number
            self.table.setItem(row, self.COL_HOUSE_NUMBER, QTableWidgetItem(house_number))
            
            # Set main address fields
            self.table.setItem(row, self.COL_CITY, QTableWidgetItem(doc_info['address'].get('city', '')))
            self.table.setItem(row, self.COL_COUNTY, QTableWidgetItem(doc_info['address'].get('county', '')))
            self.table.setItem(row, self.COL_POSTCODE, QTableWidgetItem(doc_info['address'].get('postcode', '')))
            
            # Type (non-editable)
            type_item = QTableWidgetItem(doc_info.get('type', 'annual'))
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            type_item.setBackground(QColor('#f8f9fa'))
            self.table.setItem(row, self.COL_TYPE, type_item)
            
            # Set street
            self.table.setItem(row, self.COL_STREET, QTableWidgetItem(street))
            
            # Set additional address lines
            for i in range(3):
                value = addr_lines[i].strip() if i < len(addr_lines) else ''
                self.table.setItem(row, self.COL_ADDR_1 + i, QTableWidgetItem(value))
        
        # Create scroll area for table
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.table)
        scroll_area.setWidgetResizable(True)
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
            postcode = self.table.item(row, self.COL_POSTCODE).text().strip()
            
            if not names:
                invalid_rows.append(f"Row {row + 1}: Names field cannot be empty")
                
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
            
            # Parse address parts
            house_parts = doc_info['address'].get('house', '').split(',')
            house_number = house_parts[0] if house_parts else ''
            street = house_parts[1].strip() if len(house_parts) > 1 else ''
            addr_lines = house_parts[2:] if len(house_parts) > 2 else []
            
            # Reset house number and street
            self.table.item(row, self.COL_HOUSE_NUMBER).setText(house_number)
            self.table.item(row, self.COL_STREET).setText(street)
            
            # Reset main address fields
            self.table.item(row, self.COL_CITY).setText(doc_info['address'].get('city', ''))
            self.table.item(row, self.COL_COUNTY).setText(doc_info['address'].get('county', ''))
            self.table.item(row, self.COL_POSTCODE).setText(doc_info['address'].get('postcode', ''))
            
            # Reset additional address lines
            for i in range(3):
                value = addr_lines[i].strip() if i < len(addr_lines) else ''
                self.table.item(row, self.COL_ADDR_1 + i).setText(value)
        
    def save_values(self) -> None:
        """Save current values from the table."""
        self.edited_values = []
        
        for row in range(self.table.rowCount()):
            # Create address dictionary with all components
            address = {
                'house': '',  # Will be built from parts
                'city': self.table.item(row, self.COL_CITY).text().strip(),
                'county': self.table.item(row, self.COL_COUNTY).text().strip(),
                'postcode': self.table.item(row, self.COL_POSTCODE).text().strip().upper()
            }
            
            # Build house string from components
            house_parts = []
            
            # Add house number if not empty
            house_number = self.table.item(row, self.COL_HOUSE_NUMBER).text().strip()
            if house_number:
                house_parts.append(house_number)
            
            # Add street if not empty
            street = self.table.item(row, self.COL_STREET).text().strip()
            if street:
                house_parts.append(street)
            
            # Add additional address lines if not empty
            for i in range(3):
                line = self.table.item(row, self.COL_ADDR_1 + i).text().strip()
                if line:
                    house_parts.append(line)
                # Also add to address dict for filename generation
                address[f'address_line_{i+1}'] = line
            
            # Set the complete house string
            address['house'] = ", ".join(house_parts)
            
            # Add to edited values
            self.edited_values.append({
                'filename': self.table.item(row, self.COL_DOCUMENT).text(),
                'names': self.table.item(row, self.COL_NAMES).text().strip(),
                'address': address,
                'type': self.table.item(row, self.COL_TYPE).text()
            })
    
    def get_values(self) -> List[Dict]:
        """Get the edited values."""
        return self.edited_values
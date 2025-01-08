"""Dialog for editing names and address before letter generation."""
import re
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QStyle
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class EditDetailsDialog(QDialog):
    """Dialog for editing extracted details before letter generation."""
    
    def __init__(self, names: str, address: dict, parent=None) -> None:
        """Initialize the dialog with extracted details."""
        super().__init__(parent)
        self.setWindowTitle("Edit Letter Details")
        self.setModal(True)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        # Store original values
        self.original_names = names
        self.original_address = address
        
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
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title section
        title_label = QLabel("Edit Letter Details")
        title_label.setStyleSheet("""
            font-size: 18px;
            color: #2c3e50;
            font-weight: bold;
            padding-bottom: 10px;
        """)
        main_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Enter each address line, using commas to separate parts. The postcode will be placed at the end.")
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
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Field', 'Value'])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        
        # Add rows
        rows = [
            ('Names', self.original_names),
            ('Address 1', self.original_address.get('address_1', '')),
            ('Address 2', self.original_address.get('address_2', '')),
            ('Address 3', self.original_address.get('address_3', '')),
            ('Address 4', self.original_address.get('address_4', '')),
            ('Address 5', self.original_address.get('address_5', '')),
            ('Address 6', self.original_address.get('address_6', '')),
            ('Postcode', self.original_address.get('postcode', ''))
        ]
        
        self.table.setRowCount(len(rows))
        for i, (field, value) in enumerate(rows):
            field_item = QTableWidgetItem(field)
            field_item.setFlags(field_item.flags() & ~Qt.ItemIsEditable)  # Make field name non-editable
            field_item.setBackground(QColor('#f8f9fa'))
            
            value_item = QTableWidgetItem(value)
            
            self.table.setItem(i, 0, field_item)
            self.table.setItem(i, 1, value_item)
        
        main_layout.addWidget(self.table)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Create styled buttons
        ok_button = QPushButton("Save Changes")
        ok_button.setObjectName("primary")
        ok_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("secondary")
        cancel_button.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        
        reset_button = QPushButton("Reset")
        reset_button.setObjectName("danger")
        reset_button.setIcon(self.style().standardIcon(QStyle.SP_DialogResetButton))
        
        # Connect buttons
        ok_button.clicked.connect(self.validate_and_accept)
        cancel_button.clicked.connect(self.reject)
        reset_button.clicked.connect(self.reset_values)
        
        # Add buttons to layout
        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
    def validate_postcode(self, postcode: str) -> bool:
        """Validate postcode format."""
        postcode = postcode.strip().upper()
        postcode_pattern = r'^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$'
        return bool(re.match(postcode_pattern, postcode))
            
    def validate_and_accept(self) -> None:
        """Validate all fields before accepting."""
        # Get values from table
        names = self.table.item(0, 1).text().strip()
        postcode = self.table.item(7, 1).text().strip()
        
        if not names:
            QMessageBox.warning(self, "Validation Error", "Names field cannot be empty.")
            return
            
        if not self.validate_postcode(postcode):
            QMessageBox.warning(self, "Validation Error", "Please enter a valid UK postcode.")
            return
            
        self.accept()
        
    def reset_values(self) -> None:
        """Reset all fields to their original values."""
        rows = [
            ('Names', self.original_names),
            ('Address 1', self.original_address.get('address_1', '')),
            ('Address 2', self.original_address.get('address_2', '')),
            ('Address 3', self.original_address.get('address_3', '')),
            ('Address 4', self.original_address.get('address_4', '')),
            ('Address 5', self.original_address.get('address_5', '')),
            ('Address 6', self.original_address.get('address_6', '')),
            ('Postcode', self.original_address.get('postcode', ''))
        ]
        
        for i, (_, value) in enumerate(rows):
            self.table.item(i, 1).setText(value)
        
    def get_values(self) -> tuple:
        """Get the current values from the dialog."""
        names = self.table.item(0, 1).text().strip()
        
        address = {
            'address_1': self.table.item(1, 1).text().strip(),
            'address_2': self.table.item(2, 1).text().strip(),
            'address_3': self.table.item(3, 1).text().strip(),
            'address_4': self.table.item(4, 1).text().strip(),
            'address_5': self.table.item(5, 1).text().strip(),
            'address_6': self.table.item(6, 1).text().strip(),
            'postcode': self.table.item(7, 1).text().strip().upper()
        }
        
        return names, address
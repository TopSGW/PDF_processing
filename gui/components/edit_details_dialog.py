"""Dialog for editing names and address before letter generation."""
import re
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFormLayout, QWidget,
    QStyle, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPalette, QColor

class StyledLineEdit(QLineEdit):
    """Custom styled line edit with validation."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumHeight(30)
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #4a90e2;
                background-color: #f8f9fa;
            }
            QLineEdit:hover {
                border: 2px solid #4a90e2;
            }
        """)

class EditDetailsDialog(QDialog):
    """Dialog for editing extracted details before letter generation."""
    
    def __init__(self, names: str, address: dict, parent=None) -> None:
        """Initialize the dialog with extracted details."""
        super().__init__(parent)
        self.setWindowTitle("Edit Letter Details")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        # Store original values
        self.original_names = names
        self.original_address = address
        
        # Initialize UI components with custom styling
        self.names_edit = StyledLineEdit(names)
        self.house_edit = StyledLineEdit(address.get('house', ''))
        self.city_edit = StyledLineEdit(address.get('city', ''))
        self.county_edit = StyledLineEdit(address.get('county', ''))
        self.postcode_edit = StyledLineEdit(address.get('postcode', ''))
        
        # Set tooltips
        self.names_edit.setToolTip("Enter full names separated by '&' or 'and'")
        self.house_edit.setToolTip("Enter house name/number and street")
        self.city_edit.setToolTip("Enter city or town name")
        self.county_edit.setToolTip("Enter county name")
        self.postcode_edit.setToolTip("Enter valid UK postcode")
        
        # Add validation
        self.postcode_edit.textChanged.connect(self.validate_postcode)
        
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
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0;")
        main_layout.addWidget(separator)
        
        # Create form layout for the fields
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        # Add fields with labels
        form_layout.addRow("Names:", self.names_edit)
        form_layout.addRow("House/Street:", self.house_edit)
        form_layout.addRow("City:", self.city_edit)
        form_layout.addRow("County:", self.county_edit)
        form_layout.addRow("Postcode:", self.postcode_edit)
        
        main_layout.addLayout(form_layout)
        
        # Add another separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("background-color: #e0e0e0;")
        main_layout.addWidget(separator2)
        
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
        
    def validate_postcode(self) -> None:
        """Validate postcode format and provide visual feedback."""
        postcode = self.postcode_edit.text().strip().upper()
        # Basic UK postcode validation
        postcode_pattern = r'^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$'
        
        if postcode and not re.match(postcode_pattern, postcode):
            self.postcode_edit.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #dc3545;
                    border-radius: 5px;
                    padding: 5px 10px;
                    background-color: #fff8f8;
                }
            """)
        else:
            self.postcode_edit.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #28a745;
                    border-radius: 5px;
                    padding: 5px 10px;
                    background-color: #f8fff8;
                }
            """)
            
    def validate_and_accept(self) -> None:
        """Validate all fields before accepting."""
        if not self.names_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Names field cannot be empty.")
            return
            
        if not self.house_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "House/Street field cannot be empty.")
            return
            
        if not self.city_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "City field cannot be empty.")
            return
            
        if not self.county_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "County field cannot be empty.")
            return
            
        postcode = self.postcode_edit.text().strip().upper()
        postcode_pattern = r'^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$'
        if not re.match(postcode_pattern, postcode):
            QMessageBox.warning(self, "Validation Error", "Please enter a valid UK postcode.")
            return
            
        self.accept()
        
    def reset_values(self) -> None:
        """Reset all fields to their original values."""
        self.names_edit.setText(self.original_names)
        self.house_edit.setText(self.original_address.get('house', ''))
        self.city_edit.setText(self.original_address.get('city', ''))
        self.county_edit.setText(self.original_address.get('county', ''))
        self.postcode_edit.setText(self.original_address.get('postcode', ''))
        
    def get_values(self) -> tuple:
        """Get the current values from the dialog."""
        names = self.names_edit.text().strip()
        address = {
            'house': self.house_edit.text().strip(),
            'city': self.city_edit.text().strip(),
            'county': self.county_edit.text().strip(),
            'postcode': self.postcode_edit.text().strip().upper()
        }
        return names, address
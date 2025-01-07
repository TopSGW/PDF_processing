"""Module containing the header section of the GUI."""
from pathlib import Path
from typing import Optional, Callable

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QPushButton, QLabel,
    QFileDialog
)
from PyQt5.QtCore import Qt

from constants import (
    DEFAULT_FOLDER_LABEL,
    SELECT_FOLDER_BUTTON_TEXT,
    FOLDER_DIALOG_TITLE
)

class HeaderSection(QFrame):
    """Header section of the application containing folder selection controls."""

    def __init__(self, on_folder_selected: Callable[[str], None]) -> None:
        """
        Initialize the header section.
        
        Args:
            on_folder_selected: Callback function to handle folder selection
        """
        super().__init__()
        self.on_folder_selected = on_folder_selected
        self.selected_folder: Optional[Path] = None
        
        # Initialize UI components
        self.folder_label: Optional[QLabel] = None
        self.select_button: Optional[QPushButton] = None
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.setFrameStyle(QFrame.StyledPanel)
        
        layout = QVBoxLayout()
        
        # Folder selection label
        self.folder_label = QLabel(DEFAULT_FOLDER_LABEL)
        self.folder_label.setWordWrap(True)
        layout.addWidget(self.folder_label)
        
        # Select folder button
        self.select_button = QPushButton(SELECT_FOLDER_BUTTON_TEXT)
        self.select_button.clicked.connect(self.select_home_folder)
        self.select_button.setFixedWidth(200)
        layout.addWidget(self.select_button, alignment=Qt.AlignLeft)
        
        self.setLayout(layout)
        
    def select_home_folder(self) -> None:
        """Handle the folder selection dialog."""
        try:
            folder = QFileDialog.getExistingDirectory(
                self,
                FOLDER_DIALOG_TITLE,
            )
            
            if folder:
                self.selected_folder = Path(folder)
                self.folder_label.setText(f"Selected Folder: {folder}")
                self.on_folder_selected(folder)
                
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error",
                f"Error selecting folder: {str(e)}"
            )
            
    def set_button_enabled(self, enabled: bool) -> None:
        """Enable or disable the select button."""
        if self.select_button:
            self.select_button.setEnabled(enabled)
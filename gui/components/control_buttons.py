"""Module containing the control buttons section of the GUI."""
from pathlib import Path
from typing import Optional, Callable

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QPushButton,
    QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt

from constants import (
    MOVE_UP_TEXT, MOVE_DOWN_TEXT, REMOVE_PAIR_TEXT,
    ADD_PAIR_TEXT, ADD_PDF_DIALOG_TITLE,
    REMOVE_CONFIRM_TITLE, REMOVE_CONFIRM_TEXT,
    PDF_EXTENSION
)

class ControlButtons(QFrame):
    """Control buttons section of the application."""

    def __init__(
        self,
        on_move_up: Callable[[], None],
        on_move_down: Callable[[], None],
        on_remove: Callable[[], None],
        on_add_pair: Callable[[list], None]
    ) -> None:
        """
        Initialize the control buttons section.
        
        Args:
            on_move_up: Callback function for move up button
            on_move_down: Callback function for move down button
            on_remove: Callback function for remove button
            on_add_pair: Callback function for add PDF pair button
        """
        super().__init__()
        self.on_move_up = on_move_up
        self.on_move_down = on_move_down
        self.on_remove = on_remove
        self.on_add_pair = on_add_pair
        self.selected_folder: Optional[Path] = None
        
        # Initialize UI components
        self.move_up_btn: Optional[QPushButton] = None
        self.move_down_btn: Optional[QPushButton] = None
        self.remove_btn: Optional[QPushButton] = None
        self.add_btn: Optional[QPushButton] = None
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.setFixedWidth(100)
        self.setFrameStyle(QFrame.StyledPanel)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        
        # Move Up button
        self.move_up_btn = QPushButton(MOVE_UP_TEXT)
        self.move_up_btn.setEnabled(False)
        self.move_up_btn.clicked.connect(self.on_move_up)
        layout.addWidget(self.move_up_btn)
        
        # Move Down button
        self.move_down_btn = QPushButton(MOVE_DOWN_TEXT)
        self.move_down_btn.setEnabled(False)
        self.move_down_btn.clicked.connect(self.on_move_down)
        layout.addWidget(self.move_down_btn)
        
        # Add spacing
        layout.addSpacing(20)
        
        # Remove button
        self.remove_btn = QPushButton(REMOVE_PAIR_TEXT)
        self.remove_btn.setEnabled(False)
        self.remove_btn.clicked.connect(self.handle_remove)
        layout.addWidget(self.remove_btn)
        
        # Add PDF Pair button
        self.add_btn = QPushButton(ADD_PAIR_TEXT)
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self.handle_add_pair)
        layout.addWidget(self.add_btn)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def set_selected_folder(self, folder: Optional[Path]) -> None:
        """Set the selected folder path."""
        self.selected_folder = folder
        self.add_btn.setEnabled(bool(folder))
        
    def update_button_states(self, has_selection: bool, is_folder: bool, current_index: int, total_items: int) -> None:
        """Update the enabled state of control buttons based on selection."""
        self.move_up_btn.setEnabled(is_folder and current_index > 0)
        self.move_down_btn.setEnabled(is_folder and current_index < total_items - 1)
        self.remove_btn.setEnabled(is_folder)
        self.add_btn.setEnabled(bool(self.selected_folder))
        
    def handle_remove(self) -> None:
        """Handle the remove button click with confirmation."""
        reply = QMessageBox.question(
            self,
            REMOVE_CONFIRM_TITLE,
            REMOVE_CONFIRM_TEXT,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.on_remove()
            
    def handle_add_pair(self) -> None:
        """Handle the add PDF pair button click."""
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
            
        self.on_add_pair(files)
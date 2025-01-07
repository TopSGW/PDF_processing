"""Module containing the progress section of the GUI."""
from typing import Optional

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QProgressBar
)

class ProgressSection(QFrame):
    """Progress section of the application containing progress bar and status label."""

    def __init__(self) -> None:
        """Initialize the progress section."""
        super().__init__()
        
        # Initialize UI components
        self.status_label: Optional[QLabel] = None
        self.progress_bar: Optional[QProgressBar] = None
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
    def show_progress(self, visible: bool = True) -> None:
        """Show or hide the progress bar."""
        if self.progress_bar:
            self.progress_bar.setVisible(visible)
            
    def show_status(self, visible: bool = True) -> None:
        """Show or hide the status label."""
        if self.status_label:
            self.status_label.setVisible(visible)
            
    def set_status_text(self, text: str) -> None:
        """Set the status label text."""
        if self.status_label:
            self.status_label.setText(text)
            
    def set_progress_range(self, minimum: int, maximum: int) -> None:
        """Set the progress bar range."""
        if self.progress_bar:
            self.progress_bar.setRange(minimum, maximum)
            
    def set_progress_value(self, value: int) -> None:
        """Set the progress bar value."""
        if self.progress_bar:
            self.progress_bar.setValue(value)
            
    def set_indeterminate(self) -> None:
        """Set the progress bar to indeterminate mode."""
        if self.progress_bar:
            self.progress_bar.setRange(0, 0)  # Indeterminate state
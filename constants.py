"""Constants used throughout the application."""
from typing import Final

# File extensions
PDF_EXTENSION: Final[str] = '.pdf'

# GUI constants
WINDOW_TITLE: Final[str] = "PDF Folder Scanner"
WINDOW_WIDTH: Final[int] = 600
WINDOW_HEIGHT: Final[int] = 400
DEFAULT_FOLDER_LABEL: Final[str] = "No folder selected"
SELECT_FOLDER_BUTTON_TEXT: Final[str] = "Select Home Folder"
NO_RESULTS_MESSAGE: Final[str] = "No PDF files were found in the subfolders."
FOLDER_DIALOG_TITLE: Final[str] = "Select Home Folder"

# Processing constants
REQUIRED_PDF_COUNT: Final[int] = 2  # Minimum number of PDFs required
PROCESSED_FOLDER_MARKER: Final[str] = ".processed"  # Marker for processed folders
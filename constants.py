"""Constants used throughout the application."""
from typing import Final

# File extensions
PDF_EXTENSION: Final[str] = '.pdf'

# GUI constants
WINDOW_TITLE: Final[str] = "PDF Folder Scanner"
WINDOW_WIDTH: Final[int] = 800
WINDOW_HEIGHT: Final[int] = 600
DEFAULT_FOLDER_LABEL: Final[str] = "No folder selected"
SELECT_FOLDER_BUTTON_TEXT: Final[str] = "Select Home Folder"
NO_RESULTS_MESSAGE: Final[str] = "No PDF files were found in the subfolders."
FOLDER_DIALOG_TITLE: Final[str] = "Select Home Folder"

# Control button texts
MOVE_UP_TEXT: Final[str] = "Move Up"
MOVE_DOWN_TEXT: Final[str] = "Move Down"
REMOVE_PAIR_TEXT: Final[str] = "Remove"
ADD_PAIR_TEXT: Final[str] = "Add PDF Pair"
PROCESS_TEXT: Final[str] = "Process Selected"

# Letter generation buttons
GENERATE_ANNUAL_LETTER: Final[str] = "Generate Annual Letter"
GENERATE_15_YEAR_LETTER: Final[str] = "Generate 15-Year Letter"
GENERATE_LETTER_ERROR: Final[str] = "Error Generating Letter"
GENERATE_LETTER_SUCCESS: Final[str] = "Letter Generated Successfully"
LETTER_SAVE_DIALOG: Final[str] = "Save Letter As"

# Processing constants
REQUIRED_PDF_COUNT: Final[int] = 2  # Minimum number of PDFs required
PROCESSED_FOLDER_MARKER: Final[str] = ".processed"  # Marker for processed folders

# Dialog titles
ADD_PDF_DIALOG_TITLE: Final[str] = "Select PDF Files"
REMOVE_CONFIRM_TITLE: Final[str] = "Confirm Removal"
REMOVE_CONFIRM_TEXT: Final[str] = "Are you sure you want to remove this PDF pair?"

MERGE_AND_COMPRESS_PDFS: Final[str] = "Print"
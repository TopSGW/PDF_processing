"""Main script for PDF processing application with GUI."""
import sys
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow  # Updated import to use new implementation

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the GUI application."""
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
"""Main entry point of the application."""
import sys
import logging
from PyQt5.QtWidgets import QApplication
from constants import WINDOW_WIDTH, WINDOW_HEIGHT
from gui import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Initialize and run the application."""
    try:
        # Create the application
        app = QApplication(sys.argv)
        
        # Create and configure the main window
        window = MainWindow()
        window.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        window.show()
        
        # Start the event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""Script to run the PDF processing GUI application."""
import sys
from PyQt5.QtWidgets import QApplication
from gui import MainWindow

def main():
    """Main function to run the GUI application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
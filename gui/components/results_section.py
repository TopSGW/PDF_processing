"""Module containing the results section of the GUI."""
import logging
from pathlib import Path
from typing import Optional, Callable, List, Tuple

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

from constants import (
    NO_RESULTS_MESSAGE,
    PROCESSED_FOLDER_MARKER
)
from pdf_scanner import PDFPair

logger = logging.getLogger(__name__)

class ResultsSection(QFrame):
    """Results section of the application containing the tree widget for PDF files."""

    def __init__(self, on_selection_changed: Callable[[], None]) -> None:
        """
        Initialize the results section.
        
        Args:
            on_selection_changed: Callback function to handle selection changes
        """
        super().__init__()
        self.on_selection_changed = on_selection_changed
        self.selected_folder: Optional[Path] = None
        
        # Initialize UI components
        self.result_tree: Optional[QTreeWidget] = None
        
        self.init_ui()
        
    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.setFrameStyle(QFrame.StyledPanel)
        
        layout = QVBoxLayout()
        
        # Results tree
        self.result_tree = QTreeWidget()
        self.result_tree.setHeaderLabels(["Folders and PDFs"])
        self.result_tree.setAlternatingRowColors(True)
        self.result_tree.setIndentation(20)
        self.result_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.result_tree.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.result_tree)
        
        self.setLayout(layout)
        
    def clear_results(self) -> None:
        """Clear all items from the tree widget."""
        if self.result_tree:
            self.result_tree.clear()
            
    def set_selected_folder(self, folder: Path) -> None:
        """Set the selected folder path."""
        self.selected_folder = folder
        
    def create_folder_item(self, folder_path: str, pdf_pair: PDFPair, is_processed: bool) -> QTreeWidgetItem:
        """Create a folder item for the tree widget."""
        item = QTreeWidgetItem()
        status = "✓" if is_processed else ""
        total_pdfs = sum(1 for pdf in [pdf_pair.document_pdf, pdf_pair.map_pdf] if pdf is not None)
        wayleave_info = f" [{pdf_pair.wayleave_type}]" if pdf_pair.wayleave_type != "unknown" else ""
        item.setText(0, f"📁 {folder_path} ({total_pdfs} PDFs){wayleave_info} {status}")

        if self.selected_folder:
            folder_path_obj = Path(folder_path)
            if folder_path_obj.is_absolute():
                full_path = folder_path
            else:
                full_path = str(self.selected_folder / folder_path)
            
            tooltip = f"Full path: {full_path}\n"
            tooltip += f"Document PDF: {'Yes' if pdf_pair.document_pdf else 'No'}\n"
            tooltip += f"Map PDF: {'Yes' if pdf_pair.map_pdf else 'No'}\n"
            tooltip += f"Wayleave Type: {pdf_pair.wayleave_type}"
            item.setToolTip(0, tooltip)

        if is_processed:
            item.setBackground(0, QColor("#E8F5E9"))  # Light green
        
        return item
        
    def create_pdf_item(self, pdf_path: Path, pdf_type: str = "", wayleave_type: str = "") -> QTreeWidgetItem:
        """Create a PDF item for the tree widget."""
        item = QTreeWidgetItem()
        
        # Set icon and format based on PDF type
        if pdf_type == "Document":
            wayleave_info = f" [{wayleave_type}]" if wayleave_type and wayleave_type != "unknown" else ""
            item.setText(0, f"📄 {pdf_path.name} (Document){wayleave_info}")
            item.setForeground(0, QColor("#1976D2"))  # Blue for Document
        else:  # Map
            item.setText(0, f"🗺️ {pdf_path.name} (Map)")
            item.setForeground(0, QColor("#388E3C"))  # Green for Map
            
        item.setToolTip(0, f"Full path: {pdf_path}\nWayleave Type: {wayleave_type}")
        return item
        
    def display_results(self, results: List[Tuple[str, PDFPair]]) -> None:
        """Display the scan results in the tree widget."""
        try:
            self.clear_results()
            
            if not results:
                logger.info("No results found")
                no_results = QTreeWidgetItem()
                no_results.setText(0, NO_RESULTS_MESSAGE)
                self.result_tree.addTopLevelItem(no_results)
            else:
                # Sort results by path for better organization
                sorted_results = sorted(results, key=lambda x: x[0])
                logger.debug(f"Processing {len(sorted_results)} sorted results")
                
                for relative_path, pdf_pair in sorted_results:
                    # Create folder item
                    is_processed = (Path(self.selected_folder) / relative_path / PROCESSED_FOLDER_MARKER).exists() \
                        if self.selected_folder else False
                    folder_item = self.create_folder_item(relative_path, pdf_pair, is_processed)
                    self.result_tree.addTopLevelItem(folder_item)
                    
                    # Add Document PDF if exists
                    if pdf_pair.document_pdf:
                        doc_item = self.create_pdf_item(pdf_pair.document_pdf, "Document", pdf_pair.wayleave_type)
                        folder_item.addChild(doc_item)
                    
                    # Add Map PDF if exists
                    if pdf_pair.map_pdf:
                        map_item = self.create_pdf_item(pdf_pair.map_pdf, "Map")
                        folder_item.addChild(map_item)
                    
                # Expand all items for better visibility
                self.result_tree.expandAll()
                logger.debug("Finished processing results")
                
        except Exception as e:
            logger.error(f"Error displaying results: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error",
                f"Error displaying results: {str(e)}"
            )
            
    def get_selected_document_pdf(self) -> Optional[Path]:
        """Get the selected document PDF path."""
        if not self.result_tree:
            return None
            
        selected = self.result_tree.selectedItems()
        if not selected:
            return None
            
        selected_item = selected[0]
        if selected_item.childCount() > 0:  # If folder is selected
            for i in range(selected_item.childCount()):
                child = selected_item.child(i)
                if "(Document)" in child.text(0):
                    return Path(child.toolTip(0).replace("Full path: ", "").split("\n")[0])
        elif "(Document)" in selected_item.text(0):  # If document is selected
            return Path(selected_item.toolTip(0).replace("Full path: ", "").split("\n")[0])
            
        return None
        
    def move_item_up(self) -> None:
        """Move the selected folder item up in the list."""
        if not self.result_tree:
            return
            
        selected = self.result_tree.selectedItems()
        if not selected:
            return
            
        item = selected[0]
        index = self.result_tree.indexOfTopLevelItem(item)
        if index > 0:
            self.result_tree.takeTopLevelItem(index)
            self.result_tree.insertTopLevelItem(index - 1, item)
            self.result_tree.setCurrentItem(item)
            
    def move_item_down(self) -> None:
        """Move the selected folder item down in the list."""
        if not self.result_tree:
            return
            
        selected = self.result_tree.selectedItems()
        if not selected:
            return
            
        item = selected[0]
        index = self.result_tree.indexOfTopLevelItem(item)
        if index < self.result_tree.topLevelItemCount() - 1:
            self.result_tree.takeTopLevelItem(index)
            self.result_tree.insertTopLevelItem(index + 1, item)
            self.result_tree.setCurrentItem(item)
            
    def remove_selected_item(self) -> None:
        """Remove the selected folder item."""
        if not self.result_tree:
            return
            
        selected = self.result_tree.selectedItems()
        if not selected:
            return
            
        item = selected[0]
        index = self.result_tree.indexOfTopLevelItem(item)
        self.result_tree.takeTopLevelItem(index)
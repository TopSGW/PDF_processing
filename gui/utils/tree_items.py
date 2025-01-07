"""Module containing tree widget item utility functions."""
from pathlib import Path
from typing import Optional, Tuple

from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtGui import QColor

from pdf_scanner import PDFPair
from constants import PROCESSED_FOLDER_MARKER

def create_folder_item(
    folder_path: str,
    pdf_pair: PDFPair,
    selected_folder: Optional[Path],
    is_processed: bool = False
) -> QTreeWidgetItem:
    """
    Create a folder item for the tree widget.
    
    Args:
        folder_path: Path to the folder
        pdf_pair: PDFPair object containing document and map PDFs
        selected_folder: Currently selected root folder
        is_processed: Whether the folder has been processed
        
    Returns:
        QTreeWidgetItem: Created tree widget item
    """
    item = QTreeWidgetItem()
    status = "✓" if is_processed else ""
    total_pdfs = sum(1 for pdf in [pdf_pair.document_pdf, pdf_pair.map_pdf] if pdf is not None)
    wayleave_info = f" [{pdf_pair.wayleave_type}]" if pdf_pair.wayleave_type != "unknown" else ""
    item.setText(0, f"📁 {folder_path} ({total_pdfs} PDFs){wayleave_info} {status}")

    if selected_folder:
        folder_path_obj = Path(folder_path)
        if folder_path_obj.is_absolute():
            full_path = folder_path
        else:
            full_path = str(selected_folder / folder_path)
        
        tooltip = f"Full path: {full_path}\n"
        tooltip += f"Document PDF: {'Yes' if pdf_pair.document_pdf else 'No'}\n"
        tooltip += f"Map PDF: {'Yes' if pdf_pair.map_pdf else 'No'}\n"
        tooltip += f"Wayleave Type: {pdf_pair.wayleave_type}"
        item.setToolTip(0, tooltip)

    if is_processed:
        item.setBackground(0, QColor("#E8F5E9"))  # Light green
    
    return item

def create_pdf_item(pdf_path: Path, pdf_type: str = "", wayleave_type: str = "") -> QTreeWidgetItem:
    """
    Create a PDF item for the tree widget.
    
    Args:
        pdf_path: Path to the PDF file
        pdf_type: Type of PDF (Document or Map)
        wayleave_type: Type of wayleave for document PDFs
        
    Returns:
        QTreeWidgetItem: Created tree widget item
    """
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

def get_pdf_paths_from_item(item: QTreeWidgetItem) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Get document and map PDF paths from a tree widget item.
    
    Args:
        item: Tree widget item to extract paths from
        
    Returns:
        Tuple[Optional[Path], Optional[Path]]: Tuple of (document_pdf_path, map_pdf_path)
    """
    doc_pdf = None
    map_pdf = None
    
    for i in range(item.childCount()):
        child = item.child(i)
        pdf_path = Path(child.toolTip(0).replace("Full path: ", "").split("\n")[0])
        if "(Document)" in child.text(0):
            doc_pdf = pdf_path
        else:
            map_pdf = pdf_path
            
    return doc_pdf, map_pdf

def get_wayleave_type_from_item(item: QTreeWidgetItem) -> str:
    """
    Get wayleave type from a tree widget item.
    
    Args:
        item: Tree widget item to extract wayleave type from
        
    Returns:
        str: Wayleave type or "unknown" if not found
    """
    for i in range(item.childCount()):
        child = item.child(i)
        if "(Document)" in child.text(0):
            tooltip = child.toolTip(0)
            if "Wayleave Type: " in tooltip:
                return tooltip.split("Wayleave Type: ")[1]
    return "unknown"

def is_folder_processed(folder_path: Path) -> bool:
    """
    Check if a folder has been processed.
    
    Args:
        folder_path: Path to the folder to check
        
    Returns:
        bool: True if the folder has been processed, False otherwise
    """
    return (folder_path / PROCESSED_FOLDER_MARKER).exists()
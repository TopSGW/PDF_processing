from pathlib import Path
from pdf_scanner import PDFContent
import logging
import fitz

# Configure logging to show only important messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_pdf_details(pdf_path: Path):
    """Analyze and print detailed information about the PDF."""
    try:
        print(f"\nAnalyzing PDF: {pdf_path}")
        print("-" * 50)
        
        # Get basic PDF information
        with fitz.open(pdf_path) as doc:
            print(f"Number of pages: {len(doc)}")
            print(f"PDF Version: {doc.metadata.get('format', 'Unknown')}")
            
            # Analyze first page
            page = doc[0]
            print(f"\nPage 1 Analysis:")
            print(f"Page size: {page.rect.width:.0f} x {page.rect.height:.0f} points")
            
            # Get image count
            images = page.get_images()
            print(f"Number of images: {len(images)}")
            
            # Get text content
            text = page.get_text()
            print(f"Text length: {len(text)} characters")
            print("\nFirst 200 characters of text:")
            print(text[:200] if text else "No text found")
            
            # Extract keywords found
            map_keywords = [
                'map', 'scale', 'legend', 'coordinates', 'location',
                'projection', 'latitude', 'longitude', 'grid', 'terrain'
            ]
            found_keywords = [word for word in map_keywords if word in text.lower()]
            print(f"\nMap keywords found: {found_keywords}")
            
        return True
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        return False

def test_map_detection():
    """Test the map detection functionality with detailed output."""
    # Path to test PDF
    pdf_path = Path("New folder/New folder/New folder (original)/NW SSE 1/lv.1 - 52 Ambleside Road.pdf")
    
    print("\nSTARTING MAP DETECTION TEST")
    print("=" * 50)
    
    # First analyze PDF details
    if analyze_pdf_details(pdf_path):
        # Then test map detection
        try:
            print("\nRunning map detection algorithm...")
            is_map = PDFContent.is_map_pdf(pdf_path)
            print(f"\nFinal Results:")
            print(f"Is map PDF: {is_map}")
        except Exception as e:
            print(f"Error during map detection: {e}")
    else:
        print("Could not proceed with map detection due to analysis failure")

if __name__ == "__main__":
    test_map_detection()
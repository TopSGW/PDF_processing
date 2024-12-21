"""Main script for testing PDF processing."""
from pathlib import Path
import logging
from letter_generator import generate_letter_for_pdf

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to test PDF processing."""
    try:
        # Test with the 15-year PDF
        pdf_path = Path("15 year.pdf")
        
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return
            
        logger.info(f"Processing PDF: {pdf_path}")
        letter, filename = generate_letter_for_pdf(pdf_path, "15-year")
        
        logger.info(f"Generated filename: {filename}")
        logger.info("Generated letter content:")
        logger.info("-" * 80)
        logger.info(letter)
        logger.info("-" * 80)
        
    except Exception as e:
        logger.error(f"Error processing PDF: {e}", exc_info=True)

if __name__ == "__main__":
    main()
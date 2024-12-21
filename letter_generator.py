"""Module for generating wayleave letters."""
from datetime import datetime
import re
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContentError(Exception):
    """Exception raised for content-related errors."""
    pass

class WayleaveLetterGenerator:
    """Class for generating wayleave letters."""
    
    def __init__(self):
        """Initialize the letter generator with templates."""
        self.company_header = """Autaway Ltd t.a Darlands Suite 2063 6-8 Revenge Road Lordswood Kent ME5 8UD
E: info@darlands.co.uk W: darlands.co.uk Company No. 12185075"""
        
        self.annual_letter_template = """{}
{}

{}

Dear {}

Re: Electrical Equipment on your Land – Wayleave Agreement

We are pleased to inform you that we have now secured agreement for payment to be made to you
from Scottish & Southern Energy (SSE).

Please find enclosed two copies of your Wayleave agreement which ALL registered homeowners must
sign. These documents confirm that SSE hold electrical equipment on your land and as such they will
now make a wayleave payment to you.

The amount being offered to you is confirmed on the agreement under 'Section 1: the Wayleave
Payment'.

To help you complete the agreement, please follow these steps for both copies of the wayleave
agreements:
1) All homeowners must sign on the SECOND PAGE
2) All homeowners must sign and date on the FOURTH PAGE (Title Plan)
3) Send both copies back to us in the prepaid envelope provided

Please note that there is no cost, or charge to you whatsoever for us setting your wayleave up. All
the monies for the wayleave will be paid to, and kept by you.

Yours sincerely,

Paul Wakeford
Partner
DARLANDS"""

        self.fifteen_year_letter_template = """{}
{}

{}

Dear {}

Re: Electrical Equipment on your Land – 15 Year Wayleave Agreement

We are pleased to inform you that we have now secured agreement for a 15-year wayleave payment to be
made to you from Scottish & Southern Energy (SSE).

Please find enclosed two copies of your 15-year Wayleave agreement which ALL registered homeowners
must sign. These documents confirm that SSE hold electrical equipment on your land and as such they
will make a one-time wayleave payment to you covering a 15-year period.

The amount being offered to you is confirmed on the agreement under 'Section 1: the Wayleave
Payment'. This is a one-time payment covering the full 15-year term.

To help you complete the agreement, please follow these steps for both copies of the wayleave
agreements:
1) All homeowners must sign on the SECOND PAGE
2) All homeowners must sign and date on the FOURTH PAGE (Title Plan)
3) Send both copies back to us in the prepaid envelope provided

Please note that:
- This is a 15-year agreement with a one-time payment
- There is no cost or charge to you whatsoever for us setting your wayleave up
- The payment covers the entire 15-year period
- After the 15-year term, the agreement will need to be renewed

Yours sincerely,

Paul Wakeford
Partner
DARLANDS"""

    def extract_names_and_address_annual(self, content: str) -> dict:
        """
        Extract names and address from annual wayleave document content.
        
        Args:
            content: String containing the document text
            
        Returns:
            Dictionary containing extracted names and address
            
        Raises:
            ContentError: If required information cannot be extracted
        """
        try:
            # Log raw content for debugging
            logger.debug("Raw content:")
            logger.debug("-" * 80)
            logger.debug(content)
            logger.debug("-" * 80)
            
            # Validate content first
            self.validate_content(content, "annual")
            
            logger.debug("Extracting names from annual document")
            # Extract the full name line using regex
            name_match = re.search(r'I/We,\s+([^\n]+)', content)
            if not name_match:
                logger.error("Name pattern not found in content")
                logger.debug(f"Content preview: {content[:200]}")
                raise ContentError("Could not find names in document")
            
            logger.debug(f"Found names: {name_match.group(1)}")
            
            logger.debug("Extracting address from annual document")
            # Look for address after "of"
            address_match = re.search(r'of\s+(.*?)(?=being|$)', content, re.DOTALL)
            if not address_match:
                logger.error("Address pattern not found in content")
                raise ContentError("Could not find address starting with 'of'")
            
            # Clean up the address
            address = address_match.group(1).strip()
            logger.debug(f"Found raw address: {address}")
            
            # Look for postcode in the address
            postcode_match = re.search(r'([A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2})', address)
            if not postcode_match:
                logger.error("Postcode not found in address")
                raise ContentError("Could not find valid postcode in address")
            
            postcode = postcode_match.group(1).replace("  ", " ")  # Normalize spaces
            logger.debug(f"Found postcode: {postcode}")
            
            # Remove postcode from address and split remaining parts
            address_without_postcode = address[:address.find(postcode)].strip()
            if address_without_postcode.endswith(","):
                address_without_postcode = address_without_postcode[:-1]
            
            # Split address parts by comma
            parts = [p.strip() for p in address_without_postcode.split(",")]
            logger.debug(f"Address parts: {parts}")
            
            if len(parts) < 2:
                logger.error("Not enough address parts found")
                raise ContentError("Address format is incomplete")
            
            result = {
                'full_names': name_match.group(1),
                'address': {
                    'house': parts[0],
                    'road': parts[1],
                    'city': parts[2] if len(parts) > 2 else '',
                    'postcode': postcode
                }
            }
            
            logger.debug(f"Successfully extracted information: {result}")
            return result
            
        except ContentError:
            raise
        except Exception as e:
            logger.error(f"Error extracting names and address from annual document: {e}")
            raise ContentError(f"Error processing annual document: {str(e)}")

    def extract_names_and_address_fifteen_year(self, content: str) -> dict:
        """
        Extract names and address from 15-year wayleave document content.
        
        Args:
            content: String containing the document text
            
        Returns:
            Dictionary containing extracted names and address
            
        Raises:
            ContentError: If required information cannot be extracted
        """
        try:
            # Log raw content for debugging
            logger.debug("Raw content:")
            logger.debug("-" * 80)
            logger.debug(content)
            logger.debug("-" * 80)
            
            # Look for the pattern "(1) NAME AND NAME of ADDRESS" in the agreement section
            pattern = r'\(1\)\s*(.*?)\s+of\s+([^,]+),\s*([^,]+),\s*([^,]+)\s+([A-Z0-9\s]+)'
            match = re.search(pattern, content, re.DOTALL)
            
            if not match:
                logger.error("Name and address pattern not found in content")
                logger.debug(f"Content preview: {content[:500]}")
                raise ContentError("Could not find names and address in 15-year document")
            
            # Extract components
            names = match.group(1).strip()
            house_and_road = match.group(2).strip()
            city = match.group(3).strip()
            county = match.group(4).strip()
            postcode = match.group(5).strip()
            
            logger.debug(f"Found names: {names}")
            logger.debug(f"Found address components: {house_and_road}, {city}, {county}, {postcode}")
            
            # Clean up names
            names = re.sub(r'\s+', ' ', names)  # Replace multiple spaces with single space
            
            result = {
                'full_names': names,
                'address': {
                    'house': house_and_road,
                    'road': '',  # Road is included in house_and_road
                    'city': city,
                    'county': county,
                    'postcode': postcode
                }
            }
            
            logger.debug(f"Successfully extracted information: {result}")
            return result
            
        except ContentError:
            raise
        except Exception as e:
            logger.error(f"Error extracting names and address from 15-year document: {e}")
            raise ContentError(f"Error processing 15-year document: {str(e)}")

    def validate_content(self, content: str, letter_type: str) -> None:
        """
        Validate the content before processing.
        
        Args:
            content: String containing the document text
            letter_type: Type of letter ("annual" or "15-year")
            
        Raises:
            ContentError: If content is invalid
        """
        if not content or not isinstance(content, str):
            raise ContentError("Document content is empty or invalid")
            
        content = content.strip()
        if not content:
            raise ContentError("Document content is empty after trimming whitespace")
            
        # Check for minimum content length
        if len(content) < 50:  # Arbitrary minimum length
            raise ContentError("Document content is too short to be valid")
            
        # Check for expected markers based on letter type
        if letter_type == "annual":
            if "ELECTRICITY ACT 1989" not in content and "Re: Electrical Equipment" not in content:
                raise ContentError("Content does not appear to be a valid annual wayleave document")
        elif letter_type == "15-year":
            if "This Agreement" not in content and "AGREED TERMS" not in content:
                raise ContentError("Content does not appear to be a valid 15-year wayleave document")
                
        logger.debug(f"Content validation passed for {letter_type} document")

    def format_names(self, full_names: str) -> tuple:
        """
        Format names for header and salutation.
        
        Args:
            full_names: String containing full names separated by AND
            
        Returns:
            Tuple of (header_names, salutation_names)
            
        Raises:
            ContentError: If names cannot be formatted properly
        """
        try:
            if not full_names:
                raise ContentError("Names string is empty")
                
            # Format names for header (with &)
            header_names = full_names.replace(' AND ', ' & ').replace(' and ', ' & ')
            
            # Format names for salutation (with first names only and 'and')
            first_names = []
            # Split by both AND and &
            for name in re.split(' AND | & ', full_names):
                name = name.strip()
                if not name:
                    continue
                name_parts = name.split()
                if not name_parts:
                    continue
                first_names.append(name_parts[0])
            
            if not first_names:
                raise ContentError("No valid names found")
            
            if len(first_names) == 2:
                salutation_names = f"{first_names[0]} and {first_names[1]}"
            elif len(first_names) > 2:
                salutation_names = ", ".join(first_names[:-1]) + f", and {first_names[-1]}"
            else:
                salutation_names = first_names[0]
                
            return header_names, salutation_names
            
        except Exception as e:
            logger.error(f"Error formatting names: {e}")
            raise ContentError(f"Error formatting names: {str(e)}")

    def format_address(self, address_dict: dict) -> str:
        """
        Format address dictionary into string with proper line breaks.
        
        Args:
            address_dict: Dictionary containing address components
            
        Returns:
            Formatted address string
            
        Raises:
            ContentError: If address cannot be formatted properly
        """
        try:
            if not isinstance(address_dict, dict):
                raise ContentError("Invalid address dictionary")
                
            # For 15-year documents, house already includes road
            address_parts = [
                address_dict['house'],  # Already includes road
                address_dict['city'],
                'Surrey' if 'county' in address_dict and 'Surrey' in address_dict['county'] else address_dict.get('county', 'Surrey'),
                address_dict['postcode']
            ]
            
            # Filter out empty parts and join with newlines
            return '\n'.join(part for part in address_parts if part)
            
        except Exception as e:
            logger.error(f"Error formatting address: {e}")
            raise ContentError(f"Error formatting address: {str(e)}")

    def generate_filename(self, address_dict: dict) -> str:
        """
        Generate filename from address components.
        
        Args:
            address_dict: Dictionary containing address components
            
        Returns:
            Generated filename string
            
        Raises:
            ContentError: If filename cannot be generated
        """
        try:
            if not isinstance(address_dict, dict):
                raise ContentError("Invalid address dictionary")
            
            # For 15-year documents, use the format: "house, city, county postcode.pdf"
            filename_parts = [
                address_dict['house'],
                address_dict['city'],
                'Surrey' if 'county' in address_dict and 'Surrey' in address_dict['county'] else address_dict.get('county', 'Surrey'),
                address_dict['postcode']
            ]
            
            return f"{', '.join(part for part in filename_parts if part)}.pdf"
            
        except Exception as e:
            logger.error(f"Error generating filename: {e}")
            raise ContentError(f"Error generating filename: {str(e)}")

    def generate_letter(self, content: str, letter_type: str = "annual") -> tuple:
        """
        Generate a wayleave letter based on document content.
        
        Args:
            content: String containing the document text
            letter_type: Type of letter to generate ("annual" or "15-year")
            
        Returns:
            Tuple of (letter_content, filename)
            
        Raises:
            ContentError: If letter cannot be generated
        """
        try:
            logger.info(f"Generating {letter_type} letter")
            logger.debug(f"Content preview: {content[:200] if content else 'Empty content'}")
            
            # Validate letter type
            if letter_type not in ["annual", "15-year"]:
                raise ContentError(f"Invalid letter type: {letter_type}")
            
            # Extract information based on letter type
            if letter_type == "annual":
                info = self.extract_names_and_address_annual(content)
                template = self.annual_letter_template
            else:  # 15-year
                info = self.extract_names_and_address_fifteen_year(content)
                template = self.fifteen_year_letter_template
            
            # Format names and address
            header_names, salutation_names = self.format_names(info['full_names'])
            formatted_address = self.format_address(info['address'])
            
            # Generate current date
            current_date = datetime.now().strftime("%d %B %Y")
            
            # Format the complete letter
            letter = template.format(
                self.company_header,
                current_date,
                f"{header_names}\n{formatted_address}",
                salutation_names
            )
            
            filename = self.generate_filename(info['address'])
            
            logger.info("Letter generation successful")
            return letter, filename
            
        except Exception as e:
            logger.error(f"Error generating {letter_type} letter: {e}")
            raise ContentError(f"Error generating letter: {str(e)}")

def generate_letter_for_pdf(pdf_path: Path, letter_type: str = "annual") -> tuple:
    """
    Generate a letter for a given PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        letter_type: Type of letter to generate ("annual" or "15-year")
        
    Returns:
        Tuple of (letter_content, filename)
        
    Raises:
        ContentError: If letter cannot be generated
    """
    try:
        logger.info(f"Generating letter for PDF: {pdf_path}")
        
        if not pdf_path.exists():
            raise ContentError(f"PDF file not found: {pdf_path}")
            
        from pdf_scanner import PDFContent
        
        # Extract text content from PDF
        content = PDFContent.extract_text_content(pdf_path)
        if not content:
            raise ContentError("Failed to extract content from PDF")
            
        logger.debug(f"Extracted content preview: {content[:200]}")
        
        # Generate letter
        generator = WayleaveLetterGenerator()
        return generator.generate_letter(content, letter_type)
        
    except Exception as e:
        logger.error(f"Error generating letter for PDF {pdf_path}: {e}")
        raise ContentError(f"Error generating letter from PDF: {str(e)}")

# Example usage
if __name__ == "__main__":
    test_content = '''Wayleave Agreement
Electricity Act 1989

This Agreement is made between:
(1)
LUCA COPPOLA AND KARON LESLEY COPPOLA of 52 Ambleside Road,
Lightwater, Surrey GU18 5UH'''
    
    try:
        generator = WayleaveLetterGenerator()
        letter, filename = generator.generate_letter(test_content, "15-year")
        
        print(f"Generated filename: {filename}")
        print("\nGenerated letter content:")
        print("-" * 80)
        print(letter)
        print("-" * 80)
        
    except ContentError as e:
        print(f"Error: {e}")
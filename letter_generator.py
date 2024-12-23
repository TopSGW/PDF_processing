"""Module for generating wayleave letters."""
from datetime import datetime
import re
import os
from pathlib import Path
import logging
import fitz  # PyMuPDF
from num2words import num2words
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENTATION

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
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
        self.company_footer = """Autaway Ltd t.a Darlands   Suite 2063 6-8 Revenge Road Lordswood Kent ME5 8UD
E: info@darlands.co.uk     W: darlands.co.uk     Company No. 12185075"""
        
        self.annual_letter_template = """{}

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

    1) All homeowners must sign on the {} PAGE
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

    1) All homeowners must sign on the {} PAGE
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

    def create_word_letter(self, letter_content: str, output_path: Path) -> None:
        """
        Create a Word (DOCX) letter with improved styling and formatting, set to A4 size.
        
        Args:
            letter_content: The text of the letter (line by line).
            output_path: Where to save the .docx file.
        """
        try:
            doc = Document()

            # ------------------------------------------------------------------------------
            # 1) Set up document page size and margins
            # ------------------------------------------------------------------------------
            section = doc.sections[0]
            section.page_width = Cm(21.0)   # A4 width
            section.page_height = Cm(29.7)  # A4 height
            section.orientation = WD_ORIENTATION.PORTRAIT  # Portrait orientation

            # Set margins (adjust as needed)
            section.top_margin = Cm(2.54)    # 1 inch
            section.bottom_margin = Cm(2.54) # 1 inch
            section.left_margin = Cm(2.54)   # 1 inch
            section.right_margin = Cm(2.54)  # 1 inch

            # ------------------------------------------------------------------------------
            # 2) Configure the default (Normal) style: font, size, line spacing
            # ------------------------------------------------------------------------------
            style = doc.styles['Normal']
            style.font.name = "Helvetica"
            style.font.size = Pt(11)
            paragraph_format = style.paragraph_format
            paragraph_format.line_spacing = 1.15
            paragraph_format.space_after = Pt(6)

            # ------------------------------------------------------------------------------
            # 3) Insert logo in header if available
            # ------------------------------------------------------------------------------
            logo_path = Path("asset/derland.png")
            if logo_path.exists():
                header = section.header
                header.is_linked_to_previous = False
                header_paragraph = header.paragraphs[0]
                header_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = header_paragraph.add_run()
                run.add_picture(str(logo_path), width=Inches(2))  # Adjust width as needed

            # ------------------------------------------------------------------------------
            # 4) Build paragraphs out of letter content
            # ------------------------------------------------------------------------------
            lines = letter_content.split('\n')
            buffer_lines = []

            def flush_buffer_as_paragraph():
                """Take the buffered lines, join them, and create a new paragraph."""
                if buffer_lines:
                    combined_text = " ".join(buffer_lines)
                    paragraph = doc.add_paragraph(combined_text)
                    buffer_lines.clear()

            for line in lines:
                if line.strip():
                    buffer_lines.append(line)
                else:
                    flush_buffer_as_paragraph()
                    doc.add_paragraph("")  # blank paragraph

            flush_buffer_as_paragraph()

            # ------------------------------------------------------------------------------
            # 5) Insert signature image if available
            # ------------------------------------------------------------------------------
            signature_path = Path("asset/sign.png")
            if signature_path.exists():
                doc.add_paragraph("")
                sig_paragraph = doc.add_paragraph()
                run = sig_paragraph.add_run()
                run.add_picture(str(signature_path), width=Inches(1.4))  # Adjust width as needed

            # ------------------------------------------------------------------------------
            # 6) Footer: put the company footer in the Word footer section
            # ------------------------------------------------------------------------------
            footer_lines = self.company_footer.split('\n')
            footer = section.footer
            footer.is_linked_to_previous = False
            footer_paragraph = footer.paragraphs[0]
            footer_paragraph.text = ""
            footer_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

            for line in footer_lines:
                run = footer_paragraph.add_run(line + "\n")
                run.font.name = "Helvetica"
                run.font.size = Pt(11)

            # ------------------------------------------------------------------------------
            # 7) Save the Word document
            # ------------------------------------------------------------------------------
            doc.save(output_path)

        except Exception as e:
            logger.error(f"Error creating Word DOCX: {e}")
            raise ContentError(f"Error creating Word DOCX: {str(e)}")

    def create_pdf_letter(self, letter_content: str, output_path: Path) -> None:
        """
        Create a PDF letter with proper formatting.
        
        Args:
            letter_content: The content of the letter
            output_path: Path where to save the PDF
        """
        # Create a new PDF document
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # A4 size in points
        
        # Set margins (in points, 1 inch = 72 points)
        left_margin = 72
        top_margin = 72
        right_margin = 72
        
        # Load logo and signature
        try:
            logo_path = Path("asset/derland.png")
            signature_path = Path("asset/sign.png")
            
            if logo_path.exists():
                logo_rect = fitz.Rect(left_margin, top_margin - 30, 200, top_margin + 10)
                page.insert_image(logo_rect, filename=str(logo_path))
            
            # Calculate text width
            text_width = page.rect.width - left_margin - right_margin
            
            # Split content into lines
            lines = letter_content.split('\n')
            
            # Current y position for text
            y_pos = top_margin + 50
            
            # Font sizes
            header_font_size = 11
            body_font_size = 11
            
            # Line spacing
            line_spacing = 1.15
            
            for line in lines:
                if not line.strip():
                    # Empty line - add spacing
                    y_pos += body_font_size * line_spacing
                    continue
                
                if "Autaway Ltd" in line:
                    font_size = header_font_size
                    font = "Helvetica"
                else:
                    font_size = body_font_size
                    font = "Helvetica"
                
                # Insert text
                page.insert_text(
                    point=(left_margin, y_pos),
                    text=line,
                    fontname=font,
                    fontsize=font_size
                )
                
                y_pos += font_size * line_spacing
            
            # Add signature at the bottom
            if signature_path.exists():
                sig_height = 50
                sig_width = 100
                sig_y = y_pos - 110  # Position above the name
                sig_rect = fitz.Rect(left_margin - 30, sig_y, left_margin + sig_width, sig_y + sig_height)
                page.insert_image(sig_rect, filename=str(signature_path))
            
            footer_lines = self.company_footer.split('\n')
            footer_y = page.rect.height - (len(footer_lines) * font_size * line_spacing)
            center_x = page.rect.width / 2

            for footer_line in footer_lines:
                # Calculate the width of the text to center it
                text_width = len(footer_line) * font_size * 0.5  # Approximate width
                x_pos = center_x - (text_width / 2)
                
                page.insert_text(
                    point=(x_pos, footer_y),
                    text=footer_line,
                    fontname="Helvetica",
                    fontsize=font_size
                )
                footer_y += font_size * line_spacing
            # Save the PDF
            doc.save(output_path, deflate=True, garbage=4)
            doc.close()
            
        except Exception as e:
            logger.error(f"Error creating PDF: {e}")
            raise ContentError(f"Error creating PDF: {str(e)}")

    def extract_names_and_address_annual(self, content: str) -> dict:
        """Extract names and address from annual wayleave document content (updated to handle multiple postcodes)."""
        try:
            logger.debug("Raw content:")
            logger.debug("-" * 80)
            logger.debug(content)
            logger.debug("-" * 80)

            self.validate_content(content, "annual")

            logger.debug("Extracting names from annual document")
            name_match = re.search(r'I/We,\s+([^\n]+)', content)
            if not name_match:
                logger.error("Name pattern not found in content")
                logger.debug(f"Content preview: {content[:200]}")
                raise ContentError("Could not find names in document")

            names = name_match.group(1).strip()
            logger.debug(f"Found names: {names}")

            logger.debug("Extracting address from annual document")
            address_match = re.search(r'of\s+(.*?)(?=being|$)', content, re.DOTALL)
            if not address_match:
                logger.error("Address pattern not found in content")
                raise ContentError("Could not find address starting with 'of'")

            address = address_match.group(1).strip()
            logger.debug(f"Found raw address: {address}")

            # --------------------------------------------------
            # Updated: find ALL possible postcodes in the address
            # --------------------------------------------------
            postcode_pattern = r'[A-Z]{1,2}\d[\dA-Z]?\s*\d[A-Z]{2}'
            multiple_postcodes = re.findall(postcode_pattern, address, flags=re.IGNORECASE)
            if not multiple_postcodes:
                logger.error("Postcode not found in address")
                raise ContentError("Could not find valid postcode in address")

            logger.debug(f"Found multiple postcodes: {multiple_postcodes}")

            # Use the first matched postcode as the "primary" one
            primary_postcode = multiple_postcodes[0].upper()

            # Locate this first postcode in the address string so we can separate it out
            first_pc_index = address.upper().find(primary_postcode)
            if first_pc_index == -1:
                logger.error("Could not find the location of the first postcode in the address")
                raise ContentError("Could not parse the address properly")

            # Slice the address up to the start of that postcode
            address_without_postcode = address[:first_pc_index].strip()
            if address_without_postcode.endswith(","):
                address_without_postcode = address_without_postcode[:-1]

            parts = [p.strip() for p in address_without_postcode.split(",")]
            logger.debug(f"Address parts: {parts}")

            if len(parts) < 2:
                logger.error("Not enough address parts found")
                raise ContentError("Address format is incomplete")

            # Build the final result
            result = {
                'full_names': names,
                'address': {
                    'house': parts[0],
                    'city': parts[1],
                    'county': parts[2] if len(parts) > 2 else '',
                    'postcode': " ".join([pc.upper() for pc in multiple_postcodes]),
                    # Store all postcodes in a list if desired:
                    'all_postcodes': [pc.upper() for pc in multiple_postcodes]
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
        """Extract names and address from 15-year wayleave document content."""
        try:
            logger.debug("Raw content:")
            logger.debug("-" * 80)
            logger.debug(content)
            logger.debug("-" * 80)
            
            # Pattern to extract names and house_and_road
            pattern = r'\(1\)\s*(.*?)\s+of\s*(.*?)\s*(?=,\s*|\))'
            match = re.search(pattern, content, re.DOTALL)
            
            if not match:
                logger.error("Name and address pattern not found in content")
                logger.debug(f"Content preview: {content[:500]}")
                raise ContentError("Could not find names and address in 15-year document")
            
            names = match.group(1).strip()
            house_and_road = match.group(2).strip()
            
            # Use your existing pattern to capture *some* address text
            address_pattern = r',\s*([^,]+),\s*([^,]+)\s+([A-Z0-9][A-Z0-9\s-]{0,10}[A-Z0-9])'
            address_match = re.search(address_pattern, content)
                        
            if not address_match:
                # Fallback if needed
                fallback_pattern = r',\s*([^,]+),\s*([^,]+)\s+(.+?)(?:\s*$|\))'
                address_match = re.search(fallback_pattern, content)
                if not address_match:
                    raise ContentError("Could not find complete address details")
            
            # Pull out the entire substring that address_match matched
            address_text = address_match.group(0)
            
            # --- KEY ADDITION: find all postcodes in that matched substring ---
            postcode_pattern = r'[A-Z]{1,2}\d[\dA-Z]?\s*\d[A-Z]{2}'
            multiple_postcodes = re.findall(postcode_pattern, address_text, flags=re.IGNORECASE)
            
            logger.info(f"Found multiple postcodes in matched address text: {multiple_postcodes}")
                        
            # For completeness, let's just pick the first one (if there are multiple):
            postcode = multiple_postcodes[0].upper() if multiple_postcodes else ''
            
            # We still parse city / county from the original capture groups as before
            city = address_match.group(1).strip()
            county = address_match.group(2).strip()
            # And 'postcode' is from the multiple_postcodes list above
            
            logger.debug(f"Found names: {names}")
            logger.debug(f"Found address components: {house_and_road}, {city}, {county}, {postcode}")
            
            # Clean up the name string
            names = re.sub(r'\s+', ' ', names)
            
            # Split house_and_road into components (backward compatibility)
            house_parts = house_and_road.split(' ', 1)
            house = house_parts[0]
            road = house_parts[1] if len(house_parts) > 1 else ''
            
            # Build final result object
            result = {
                'full_names': names,
                'address': {
                    'house': house_and_road,     # Keep 'house' for backward compatibility
                    'road': road,                # Keep 'road' for backward compatibility
                    'house_and_road': house_and_road,
                    'city': city,
                    'county': county,
                    'postcode': " ".join([pc.upper() for pc in multiple_postcodes]),
                    # Optionally store all matched postcodes if you want them:
                    'all_postcodes': [pc.upper() for pc in multiple_postcodes]
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
        """Validate the content before processing."""
        if not content or not isinstance(content, str):
            raise ContentError("Document content is empty or invalid")
            
        content = content.strip()
        if not content:
            raise ContentError("Document content is empty after trimming whitespace")
            
        if len(content) < 50:
            raise ContentError("Document content is too short to be valid")
            
        if letter_type == "annual":
            if "ELECTRICITY ACT 1989" not in content and "Re: Electrical Equipment" not in content:
                raise ContentError("Content does not appear to be a valid annual wayleave document")
        elif letter_type == "15-year":
            if "This Agreement" not in content and "AGREED TERMS" not in content:
                raise ContentError("Content does not appear to be a valid 15-year wayleave document")
                
        logger.debug(f"Content validation passed for {letter_type} document")

    def format_names(self, full_names: str) -> tuple:
        """Format names for header and salutation."""
        try:
            if not full_names:
                raise ContentError("Names string is empty")
                
            header_names = full_names.replace(' AND ', ' & ').replace(' and ', ' & ')
            
            first_names = []
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
        """Format address dictionary into string with proper line breaks."""
        try:
            if not isinstance(address_dict, dict):
                raise ContentError("Invalid address dictionary")
                
            address_parts = [
                address_dict['house'],
                address_dict['city'],
                'Surrey' if 'county' in address_dict and 'Surrey' in address_dict['county'] else address_dict.get('county', 'Surrey'),
                address_dict['postcode']
            ]
            
            return '\n'.join(part for part in address_parts if part)
            
        except Exception as e:
            logger.error(f"Error formatting address: {e}")
            raise ContentError(f"Error formatting address: {str(e)}")

    def generate_filename(self, address_dict: dict) -> str:
        """Generate filename from address components."""
        try:
            if not isinstance(address_dict, dict):
                raise ContentError("Invalid address dictionary")
            
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

    def generate_letter(self, content: str, letter_type: str = "annual", page_count: int = 1) -> tuple:
        """Generate a wayleave letter based on document content."""
        try:
            logger.info(f"Generating {letter_type} letter")
            logger.debug(f"Content preview: {content[:200] if content else 'Empty content'}")
            
            if letter_type not in ["annual", "15-year"]:
                raise ContentError(f"Invalid letter type: {letter_type}")
            
            if letter_type == "annual":
                info = self.extract_names_and_address_annual(content)
                template = self.annual_letter_template
            else:
                info = self.extract_names_and_address_fifteen_year(content)
                template = self.fifteen_year_letter_template
            
            header_names, salutation_names = self.format_names(info['full_names'])
            formatted_address = self.format_address(info['address'])
            
            current_date = datetime.now().strftime("%d %B %Y")
            
            page_counts = (page_count - 1) if letter_type == "annual" else page_count

            sign_page = num2words(page_counts, to="ordinal").upper()

            letter = template.format(
                current_date,
                f"{header_names}\n{formatted_address}",
                salutation_names,
                sign_page
            )
            
            filename = self.generate_filename(info['address'])
            
            logger.info("Letter generation successful")
            return letter, filename
            
        except Exception as e:
            logger.error(f"Error generating {letter_type} letter: {e}")
            raise ContentError(f"Error generating letter: {str(e)}")

def generate_letter_for_pdf(pdf_path: Path, letter_type: str = "annual") -> tuple:
    """Generate a letter for a given PDF file."""
    try:
        logger.info(f"Generating letter for PDF: {pdf_path}")
        
        if not pdf_path.exists():
            raise ContentError(f"PDF file not found: {pdf_path}")
            
        from pdf_scanner import PDFContent
        
        content = PDFContent.extract_text_content(pdf_path)
        page_count = PDFContent.get_page_count(pdf_path=pdf_path)

        logger.info(f"ddddddddddddddd : {page_count}")

        if not content:
            raise ContentError("Failed to extract content from PDF")
            
        logger.debug(f"Extracted content preview: {content[:200]}")
        
        generator = WayleaveLetterGenerator()

        letter, filename = generator.generate_letter(content, letter_type, page_count=page_count)
        
        # Create PDF version of the letter
        output_path = pdf_path.parent / filename
        generator.create_pdf_letter(letter, output_path)
        
        return letter, filename
        
    except Exception as e:
        logger.error(f"Error generating letter for PDF {pdf_path}: {e}")
        raise ContentError(f"Error generating letter from PDF: {str(e)}")

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
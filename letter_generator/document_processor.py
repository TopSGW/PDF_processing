"""Document content extraction and validation utilities."""
import re
import logging
from .exceptions import ContentError, ValidationError

logger = logging.getLogger(__name__)

def validate_content(content: str, letter_type: str) -> None:
    """Validate the content before processing."""
    if not content or not isinstance(content, str):
        raise ValidationError("Document content is empty or invalid")
        
    content = content.strip()
    if not content:
        raise ValidationError("Document content is empty after trimming whitespace")
        
    if len(content) < 50:
        raise ValidationError("Document content is too short to be valid")
        
    if letter_type == "annual":
        if "ELECTRICITY ACT 1989" not in content and "Re: Electrical Equipment" not in content:
            raise ValidationError("Content does not appear to be a valid annual wayleave document")
    elif letter_type == "15-year":
        if "This Agreement" not in content and "AGREED TERMS" not in content:
            raise ValidationError("Content does not appear to be a valid 15-year wayleave document")
            
    logger.debug(f"Content validation passed for {letter_type} document")

def extract_names_and_address_annual(content: str) -> dict:
    """Extract names and address from annual wayleave document content."""
    try:
        logger.debug("Raw content:")
        logger.debug("-" * 80)
        logger.debug(content)
        logger.debug("-" * 80)

        validate_content(content, "annual")

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

        postcode_pattern = r'[A-Z]{1,2}\d[\dA-Z]?\s*\d[A-Z]{2}'
        multiple_postcodes = re.findall(postcode_pattern, address, flags=re.IGNORECASE)
        if not multiple_postcodes:
            logger.error("Postcode not found in address")
            raise ContentError("Could not find valid postcode in address")

        logger.debug(f"Found multiple postcodes: {multiple_postcodes}")

        primary_postcode = multiple_postcodes[0].upper()
        first_pc_index = address.upper().find(primary_postcode)
        
        if first_pc_index == -1:
            logger.error("Could not find the location of the first postcode in the address")
            raise ContentError("Could not parse the address properly")

        address_without_postcode = address[:first_pc_index].strip()
        if address_without_postcode.endswith(","):
            address_without_postcode = address_without_postcode[:-1]

        parts = [p.strip() for p in address_without_postcode.split(",")]
        logger.debug(f"Address parts: {parts}")

        if len(parts) < 2:
            logger.error("Not enough address parts found")
            raise ContentError("Address format is incomplete")

        result = {
            'full_names': names,
            'address': {
                'house': parts[0],
                'city': parts[1],
                'county': parts[2] if len(parts) > 2 else '',
                'postcode': " ".join([pc.upper() for pc in multiple_postcodes]),
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

def extract_names_and_address_fifteen_year(content: str) -> dict:
    """Extract names and address from 15-year wayleave document content."""
    try:
        logger.debug("Raw content:")
        logger.debug("-" * 80)
        logger.debug(content)
        logger.debug("-" * 80)
        
        pattern = r'\(1\)\s*(.*?)\s+of\s*(.*?)\s*(?=,\s*|\))'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            logger.error("Name and address pattern not found in content")
            logger.debug(f"Content preview: {content[:500]}")
            raise ContentError("Could not find names and address in 15-year document")
        
        names = match.group(1).strip()
        house_and_road = match.group(2).strip()
        house_and_road = house_and_road.replace('\n', '')
        
        address_pattern = (
            r',\s*([^,]+),'         # group(1)
            r'\s*([^,]+)'          # group(2)
            r'(?:,\s*([^,]+))?'    # optional group(3)
            r'\s+([A-Z0-9][A-Z0-9\s-]{0,10}[A-Z0-9])'  # group(4) = postcode
        )
        address_match = re.search(address_pattern, content)
        
        if not address_match:
            logger.error("Could not find address details with 2 or 3 commas + postcode")
            raise ContentError("Could not find complete address details")
        
        line1 = address_match.group(1).strip()
        line2 = address_match.group(2).strip()
        line3 = address_match.group(3).strip() if address_match.group(3) else ''
        postcode_match = address_match.group(4).strip()
        
        if '(' in line2:
            parts = line2.split()
            if parts:
                line2 = parts[0]

        address_text = address_match.group(0)
        postcode_pattern = r'[A-Z]{1,2}\d[\dA-Z]?\s*\d[A-Z]{2}'
        multiple_postcodes = re.findall(postcode_pattern, address_text, flags=re.IGNORECASE)
        
        postcode = multiple_postcodes[0].upper() if multiple_postcodes else postcode_match
        
        names = re.sub(r'\s+', ' ', names)
        
        house_parts = house_and_road.split(' ', 1)
        house = house_parts[0]
        road = house_parts[1] if len(house_parts) > 1 else ''
        
        result = {
            'full_names': names,
            'address': {
                'house': house_and_road,
                'road': road,
                'house_and_road': house_and_road,
                'city': line1,
                'county': line2,
                'line1': line1,
                'line2': line2,
                'line3': line3,
                'postcode': " ".join([pc.upper() for pc in multiple_postcodes]),
                'all_postcodes': [pc.upper() for pc in multiple_postcodes],
            }
        }
        
        logger.debug(f"Successfully extracted information: {result}")
        return result
        
    except ContentError:
        raise
    except Exception as e:
        logger.error(f"Error extracting names and address from 15-year document: {e}")
        raise ContentError(f"Error processing 15-year document: {str(e)}")
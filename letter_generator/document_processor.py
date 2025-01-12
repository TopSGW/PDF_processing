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

def clean_address_line(line: str) -> str:
    """Clean address line by removing parenthetical content, 'and', and handling whitespace."""
    if not line or line.isspace():
        return ""
        
    # Replace newlines and multiple spaces with a single space
    line = re.sub(r'\s+', ' ', line)
    
    # Remove 'and' from the line
    line = line.replace(' and ', ' ').replace(' AND ', ' ')
    
    if '(' in line:
        parts = line.split()
        if parts:
            # Take everything before the first part containing a parenthesis
            cleaned_parts = []
            for part in parts:
                if '(' in part:
                    break
                cleaned_parts.append(part)
            return ' '.join(cleaned_parts) if cleaned_parts else parts[0]
    return line.strip()

def get_first_names(full_names: str) -> str:
    """Extract and format first names from full names string."""
    if not full_names:
        return ""
    
    # Replace various forms of 'AND' and other separators with a consistent separator
    normalized = full_names.replace(' AND ', ',').replace('AND ', ',').replace(' & ', ',')
    # Split by comma and clean up each part
    names = [name.strip() for name in normalized.split(',') if name.strip()]
    
    # Extract first names
    first_names = []
    for full_name in names:
        name_parts = full_name.split()
        if name_parts:
            # Convert to title case for initial style
            first_name = name_parts[0].capitalize()
            first_names.append(first_name)
    
    # Format first names with title case and lowercase "and"
    if len(first_names) == 2:
        return f"{first_names[0]} and {first_names[1]}"
    elif len(first_names) > 2:
        return ", ".join(first_names[:-1]) + f" and {first_names[-1]}"
    elif first_names:
        return first_names[0]
    return ""

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

        # Find postcode
        postcode_pattern = r'[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}'
        postcode_match = re.search(postcode_pattern, address, flags=re.IGNORECASE)
        if not postcode_match:
            logger.error("Postcode not found in address")
            raise ContentError("Could not find valid postcode in address")

        # Split address at postcode
        postcode = postcode_match.group(0).upper()
        address_parts = address[:postcode_match.start()].strip()
        if address_parts.endswith(","):
            address_parts = address_parts[:-1]

        # Split remaining address into parts and clean each line
        parts = [clean_address_line(p) for p in address_parts.split(",")]
        # Filter out empty lines and whitespace-only lines
        parts = [p for p in parts if p and not p.isspace()]
        logger.debug(f"Address parts: {parts}")

        # Create address dictionary with numbered lines
        address_dict = {}
        current_line = 1
        for part in parts:
            if current_line <= 6 and part:  # Only use up to 6 address lines
                address_dict[f'address_{current_line}'] = part
                current_line += 1

        # Add postcode
        address_dict['postcode'] = postcode

        # Get salutation name with title case and lowercase "and"
        salutation_name = get_first_names(names)

        result = {
            'full_names': names,
            'salutation_name': salutation_name,
            'address': address_dict
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
        initial_address = clean_address_line(match.group(2).strip())
        
        # Find the complete address section
        address_text = content[match.end():].strip()
        
        # Find postcode
        postcode_pattern = r'[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}'
        postcode_match = re.search(postcode_pattern, address_text, flags=re.IGNORECASE)
        if not postcode_match:
            logger.error("Postcode not found in address")
            raise ContentError("Could not find valid postcode in address")

        # Split address at postcode
        postcode = postcode_match.group(0).upper()
        address_parts = address_text[:postcode_match.start()].strip()
        if address_parts.endswith(","):
            address_parts = address_parts[:-1]

        # Combine initial address with remaining parts and clean
        all_parts = [initial_address] + [clean_address_line(p) for p in address_parts.split(",")]
        # Filter out empty lines and whitespace-only lines
        all_parts = [p for p in all_parts if p and not p.isspace()]
        
        # Create address dictionary with numbered lines
        address_dict = {}
        current_line = 1
        for part in all_parts:
            if current_line <= 6 and part:  # Only use up to 6 address lines
                address_dict[f'address_{current_line}'] = part
                current_line += 1

        # Add postcode
        address_dict['postcode'] = postcode

        # Get salutation name with title case and lowercase "and"
        salutation_name = get_first_names(names)
        
        result = {
            'full_names': names,
            'salutation_name': salutation_name,
            'address': address_dict
        }
        
        logger.debug(f"Successfully extracted information: {result}")
        return result
        
    except ContentError:
        raise
    except Exception as e:
        logger.error(f"Error extracting names and address from 15-year document: {e}")
        raise ContentError(f"Error processing 15-year document: {str(e)}")
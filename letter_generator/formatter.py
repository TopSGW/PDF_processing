"""Formatting utilities for names and addresses."""
import re
import logging
from .exceptions import FormattingError

logger = logging.getLogger(__name__)

def format_names(full_names: str) -> tuple:
    """Format names for header and salutation."""
    try:
        if not full_names:
            raise FormattingError("Names string is empty")
            
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
            raise FormattingError("No valid names found")
        
        if len(first_names) == 2:
            salutation_names = f"{first_names[0]} and {first_names[1]}"
        elif len(first_names) > 2:
            salutation_names = ", ".join(first_names[:-1]) + f", and {first_names[-1]}"
        else:
            salutation_names = first_names[0]
            
        return header_names, salutation_names
        
    except Exception as e:
        logger.error(f"Error formatting names: {e}")
        raise FormattingError(f"Error formatting names: {str(e)}")

def format_address(address_dict: dict) -> str:
    """Format address dictionary into string with proper line breaks."""
    try:
        if not isinstance(address_dict, dict):
            raise FormattingError("Invalid address dictionary")
        
        address_parts = []
        
        # Add house/number if it exists
        if address_dict.get('house'):
            address_parts.append(address_dict['house'])
        
        # Add any additional address lines that exist and are not empty
        for i in range(1, 7):  # Address lines 1-6
            line_key = f'address_line_{i}'
            if line_key in address_dict and address_dict[line_key]:
                address_parts.append(address_dict[line_key])
        
        # Add city, county, and postcode
        if address_dict.get('city'):
            address_parts.append(address_dict['city'])
            
        if address_dict.get('county'):
            address_parts.append(address_dict['county'])
        elif 'county' not in address_dict:
            address_parts.append('')
            
        if address_dict.get('postcode'):
            address_parts.append(address_dict['postcode'])
        
        # Filter out empty parts and join with newlines
        return '\n'.join(part for part in address_parts if part)
        
    except Exception as e:
        logger.error(f"Error formatting address: {e}")
        raise FormattingError(f"Error formatting address: {str(e)}")

def generate_filename(address_dict: dict) -> str:
    """Generate filename from address components."""
    try:
        if not isinstance(address_dict, dict):
            raise FormattingError("Invalid address dictionary")
        
        # Clean and sanitize each component
        def sanitize_component(component):
            if not component:
                return ""
            # Replace newlines and multiple spaces with a single space
            component = re.sub(r'\s+', ' ', component.strip())
            # Replace invalid filename characters
            component = re.sub(r'[<>:"/\\|?*]', '', component)
            return component
        
        filename_parts = []
        
        # Add house/number if it exists
        house = sanitize_component(address_dict.get('house', ''))
        if house:
            filename_parts.append(house)
        
        # Add city if it exists
        city = sanitize_component(address_dict.get('city', ''))
        if city:
            filename_parts.append(city)
            
        # Add county only if it exists and is not empty
        county = sanitize_component(address_dict.get('county', ''))
        if county:
            filename_parts.append(county)
            
        # Add postcode if it exists
        postcode = sanitize_component(address_dict.get('postcode', ''))
        if postcode:
            filename_parts.append(postcode)
        
        # Filter out empty parts and join with commas
        filename = ", ".join(filename_parts)
        
        # Ensure the filename ends with .pdf
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
            
        return filename
        
    except Exception as e:
        logger.error(f"Error generating filename: {e}")
        raise FormattingError(f"Error generating filename: {str(e)}")

def validate_postcode(postcode: str) -> bool:
    """Validate UK postcode format."""
    postcode = postcode.strip().upper()
    postcode_pattern = r'^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$'
    return bool(re.match(postcode_pattern, postcode))
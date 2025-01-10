"""Formatting utilities for names and addresses."""
import re
import logging
from typing import Optional
from .exceptions import FormattingError

logger = logging.getLogger(__name__)

def format_names(full_names: str, override_salutation_name: Optional[str] = None) -> tuple:
    """
    Format names for header and salutation.
    
    Args:
        full_names: Full names string to format
        override_salutation_name: Optional override for the salutation name (Dear {} section)
    """
    try:
        if not full_names:
            raise FormattingError("Names string is empty")
        
        # Convert names to title case (first letter capital)
        def title_case(name):
            # Split on spaces and hyphens to handle hyphenated names
            parts = re.split(r'([-\s])', name.lower())
            # Capitalize first letter of each part, keeping separators unchanged
            return ''.join(p.capitalize() if i % 2 == 0 else p for i, p in enumerate(parts))
        
        # Split names and convert each to title case
        names_list = []
        for name in re.split(' AND | & ', full_names):
            name = name.strip()
            if name:
                names_list.append(title_case(name))
        
        if not names_list:
            raise FormattingError("No valid names found")
        
        # Join with & for header
        header_names = ' & '.join(names_list)
        
        # If override_salutation_name is provided, use it exactly as provided
        if override_salutation_name is not None:
            salutation_names = override_salutation_name  # Use exactly as provided
        else:
            # Get first names for salutation
            first_names = []
            for name in names_list:
                name_parts = name.split()
                if name_parts:
                    first_names.append(name_parts[0])
            
            # Format salutation with title case and lowercase "and"
            if len(first_names) == 2:
                salutation_names = f"{first_names[0]} and {first_names[1]}"
            elif len(first_names) > 2:
                salutation_names = ", ".join(first_names[:-1]) + f" and {first_names[-1]}"
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
        postcode = ""
        
        # Extract postcode if it exists
        if address_dict.get('postcode'):
            postcode = address_dict['postcode'].strip()
        
        # Process address lines 1-6
        for i in range(1, 7):
            line_key = f'address_{i}'
            if line_key in address_dict and address_dict[line_key]:
                # Split the line by commas and take the first part
                line_parts = address_dict[line_key].split(',')
                if line_parts:
                    address_parts.append(line_parts[0].strip())
                    # If there are more parts, add them as new lines
                    for part in line_parts[1:]:
                        if len(address_parts) < 6:  # Only add if we haven't reached 6 lines
                            address_parts.append(part.strip())
        
        # Add postcode at the end if it exists
        if postcode:
            address_parts.append(postcode)
        
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
        
        # Add all address lines in order
        for i in range(1, 7):
            addr_key = f'address_{i}'
            if addr_key in address_dict and address_dict[addr_key]:
                part = sanitize_component(address_dict[addr_key])
                if part:
                    filename_parts.append(part)
            
        # Add postcode if it exists
        if address_dict.get('postcode'):
            filename_parts.append(sanitize_component(address_dict['postcode']))
        
        # Filter out empty parts and join with commas
        filename = ", ".join(part for part in filename_parts if part)
        
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
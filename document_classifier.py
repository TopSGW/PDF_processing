def identify_wayleave_type(document_content: str) -> str:
    """
    Identifies whether a wayleave document is an annual or 15-year type based on content analysis.
    
    Args:
        document_content: String containing the document text
        
    Returns:
        str: 'annual' or '15-year'
    """
    # Key identifying features for each type
    annual_indicators = [
        "SCHEDULE OF PAYMENTS",
        "£ per annum",
        "Back Pay",
        "The Company shall pay to me/us during the existence of the works"
    ]
    
    fifteen_year_indicators = [
        "means a term commencing on the date hereof",
        "the Term",
        "the Wayleave Payment",
        "15 years",
        "following the expiry of 15 years"
    ]
    
    # Count occurrences of indicators
    annual_matches = sum(1 for indicator in annual_indicators if indicator in document_content)
    fifteen_year_matches = sum(1 for indicator in fifteen_year_indicators if indicator in document_content)
    
    # Additional check for payment structure references
    has_per_annum_payment = "£ per annum" in document_content
    has_term_definition = "\"the Term\" means" in document_content
    
    # Decision logic
    if annual_matches > fifteen_year_matches or has_per_annum_payment:
        return "annual"
    elif fifteen_year_matches > annual_matches or has_term_definition:
        return "15-year"
    else:
        return "unknown"

def process_wayleave_documents(documents: list) -> dict:
    """
    Processes multiple wayleave documents and identifies their types.
    
    Args:
        documents: List of dictionaries containing document content
        
    Returns:
        dict: Dictionary with document indices and their identified types
    """
    results = {}
    
    for doc in documents:
        doc_index = doc.get('index')
        doc_content = doc.get('document_content', '')
        doc_type = identify_wayleave_type(doc_content)
        results[doc_index] = doc_type
    
    return results
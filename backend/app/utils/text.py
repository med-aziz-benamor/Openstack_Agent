"""
Text processing utilities for log analysis.
"""
import re
from typing import List, Optional


def deduplicate_lines(lines: List[str], max_items: int = 50) -> List[str]:
    """
    Deduplicate lines while preserving order.
    
    Args:
        lines: List of lines
        max_items: Maximum number of items to return
        
    Returns:
        Deduplicated list
    """
    seen = set()
    result = []
    
    for line in lines:
        if line not in seen:
            seen.add(line)
            result.append(line)
            
            if len(result) >= max_items:
                break
    
    return result


def extract_hostname_from_path(path: str) -> Optional[str]:
    """
    Extract hostname from bundle path or filename.
    
    Expects formats like:
    - controller-1_ai_bundle_20260127_143022
    - compute-node-3_bundle_2026_01_27
    
    Args:
        path: Path or filename string
        
    Returns:
        Hostname or None if not found
    """
    # Remove .tar.gz extension if present
    path = path.replace(".tar.gz", "").replace(".tgz", "")
    
    # Split by underscore
    parts = path.split("_")
    
    # Look for "bundle" keyword
    for i, part in enumerate(parts):
        if "bundle" in part.lower():
            # Hostname is typically before "bundle"
            if i > 0:
                # Join all parts before "bundle"
                hostname = "_".join(parts[:i])
                return hostname
    
    # If no "bundle" found, try to extract first part that looks like a hostname
    if parts:
        # First part is often the hostname
        candidate = parts[0]
        # Check if it looks like a hostname (contains letters)
        if re.search(r'[a-zA-Z]', candidate):
            return candidate
    
    return None


def truncate_text(text: str, max_length: int = 500) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = filename.split("/")[-1].split("\\")[-1]
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '_', filename)
    
    return filename

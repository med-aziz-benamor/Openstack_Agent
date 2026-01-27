"""
Hashing utilities for file integrity verification.
"""
import hashlib


def compute_sha256(content: bytes) -> str:
    """
    Compute SHA256 hash of file content.
    
    Args:
        content: File content as bytes
        
    Returns:
        Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()


def compute_sha256_file(file_path: str) -> str:
    """
    Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

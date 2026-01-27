"""
Safe tar file extraction with path traversal protection.
"""
import logging
import os
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


def safe_extract_tar(file_content: bytes, filename: str) -> Path:
    """
    Safely extract a tar.gz file with path traversal protection.
    
    Args:
        file_content: Bytes content of the tar.gz file
        filename: Original filename for logging
        
    Returns:
        Path to the extracted directory
        
    Raises:
        ValueError: If extraction is unsafe or fails
    """
    # Create a temporary directory for extraction
    temp_dir = Path(tempfile.mkdtemp(prefix="openstack_bundle_"))
    
    try:
        # Open tar file from bytes
        with tarfile.open(fileobj=BytesIO(file_content), mode='r:gz') as tar:
            # Validate all members before extraction
            members = tar.getmembers()
            logger.debug(f"Validating {len(members)} tar members")
            
            for member in members:
                # Check for path traversal attempts
                if not _is_safe_path(temp_dir, member.name):
                    raise ValueError(
                        f"Unsafe path detected in tar archive: {member.name}"
                    )
                
                # Check for absolute paths
                if os.path.isabs(member.name):
                    raise ValueError(
                        f"Absolute path not allowed in tar archive: {member.name}"
                    )
                
                # Check for dangerous link types
                if member.issym() or member.islnk():
                    link_target = member.linkname
                    if os.path.isabs(link_target):
                        raise ValueError(
                            f"Absolute symlink not allowed: {member.name} -> {link_target}"
                        )
                    if not _is_safe_path(temp_dir, link_target):
                        raise ValueError(
                            f"Unsafe symlink detected: {member.name} -> {link_target}"
                        )
            
            # Extract all members (already validated)
            tar.extractall(path=temp_dir, filter='data')
            logger.info(f"Extracted {len(members)} files to {temp_dir}")
            
            # Find the bundle root directory
            bundle_root = _find_bundle_root(temp_dir)
            
            return bundle_root
    
    except tarfile.TarError as e:
        # Cleanup on failure
        _cleanup_dir(temp_dir)
        raise ValueError(f"Invalid tar archive: {e}")
    
    except Exception as e:
        # Cleanup on failure
        _cleanup_dir(temp_dir)
        raise


def _is_safe_path(base_dir: Path, target_path: str) -> bool:
    """
    Check if a path is safe (doesn't escape base directory).
    
    Args:
        base_dir: Base directory for extraction
        target_path: Target path to validate
        
    Returns:
        True if path is safe
    """
    # Resolve the full path
    full_path = (base_dir / target_path).resolve()
    
    # Check if it's within base_dir
    try:
        full_path.relative_to(base_dir.resolve())
        return True
    except ValueError:
        # Path is outside base_dir
        return False


def _find_bundle_root(extract_dir: Path) -> Path:
    """
    Find the actual bundle root directory.
    
    Many bundles extract to a single top-level directory.
    This function finds that directory or returns extract_dir if multiple entries exist.
    
    Args:
        extract_dir: Directory where tar was extracted
        
    Returns:
        Path to bundle root
    """
    entries = list(extract_dir.iterdir())
    
    # If there's exactly one directory, that's likely the bundle root
    if len(entries) == 1 and entries[0].is_dir():
        logger.debug(f"Bundle root found: {entries[0]}")
        return entries[0]
    
    # Otherwise, the extract_dir itself is the bundle root
    logger.debug(f"Using extract dir as bundle root: {extract_dir}")
    return extract_dir


def _cleanup_dir(directory: Path) -> None:
    """
    Safely cleanup a directory.
    
    Args:
        directory: Directory to remove
    """
    try:
        import shutil
        if directory.exists():
            shutil.rmtree(directory)
            logger.debug(f"Cleaned up directory: {directory}")
    except Exception as e:
        logger.warning(f"Failed to cleanup {directory}: {e}")

"""
Tests for safe tar extraction functionality.
"""
import io
import tarfile
import tempfile
from pathlib import Path

import pytest

from app.utils.safe_extract import safe_extract_tar, _is_safe_path


def create_test_tar(files: dict, filename: str = "test.tar.gz") -> bytes:
    """
    Create a test tar.gz file in memory.
    
    Args:
        files: Dictionary of {path: content}
        filename: Name for the archive
        
    Returns:
        Bytes of tar.gz archive
    """
    buffer = io.BytesIO()
    
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        for file_path, content in files.items():
            # Create tarinfo
            tarinfo = tarfile.TarInfo(name=file_path)
            tarinfo.size = len(content.encode())
            
            # Add to archive
            tar.addfile(tarinfo, io.BytesIO(content.encode()))
    
    buffer.seek(0)
    return buffer.read()


def test_safe_extraction():
    """Test safe extraction of a valid bundle."""
    files = {
        "bundle/cmd/services_failed.txt": "apache2.service\nnova-api.service\n",
        "bundle/logs/journal_nova-api.txt": "ERROR: Connection failed\n",
    }
    
    tar_content = create_test_tar(files)
    extracted_path = safe_extract_tar(tar_content, "test_bundle.tar.gz")
    
    assert extracted_path.exists()
    assert extracted_path.is_dir()
    
    # Check that files were extracted
    cmd_dir = extracted_path / "cmd"
    assert cmd_dir.exists()
    
    services_file = cmd_dir / "services_failed.txt"
    assert services_file.exists()
    
    content = services_file.read_text()
    assert "apache2.service" in content


def test_path_traversal_prevention():
    """Test that path traversal attempts are blocked."""
    files = {
        "../../../etc/passwd": "malicious content",
    }
    
    tar_content = create_test_tar(files)
    
    with pytest.raises(ValueError, match="Unsafe path"):
        safe_extract_tar(tar_content, "malicious.tar.gz")


def test_absolute_path_prevention():
    """Test that absolute paths are blocked."""
    files = {
        "/etc/passwd": "malicious content",
    }
    
    tar_content = create_test_tar(files)
    
    with pytest.raises(ValueError, match="Absolute path not allowed"):
        safe_extract_tar(tar_content, "malicious.tar.gz")


def test_is_safe_path():
    """Test the _is_safe_path function."""
    base_dir = Path("/tmp/test")
    
    # Safe paths
    assert _is_safe_path(base_dir, "bundle/cmd/test.txt")
    assert _is_safe_path(base_dir, "test.txt")
    
    # Unsafe paths
    assert not _is_safe_path(base_dir, "../../../etc/passwd")
    assert not _is_safe_path(base_dir, "../../test.txt")


def test_empty_archive():
    """Test extraction of empty archive."""
    files = {}
    
    tar_content = create_test_tar(files)
    extracted_path = safe_extract_tar(tar_content, "empty.tar.gz")
    
    assert extracted_path.exists()


def test_nested_directories():
    """Test extraction with nested directory structure."""
    files = {
        "bundle/logs/var/log/nova/nova-api.log": "ERROR line 1\n",
        "bundle/configs/nova/nova.conf": "[DEFAULT]\n",
    }
    
    tar_content = create_test_tar(files)
    extracted_path = safe_extract_tar(tar_content, "nested.tar.gz")
    
    assert extracted_path.exists()
    
    # Check nested structure
    log_file = extracted_path / "logs" / "var" / "log" / "nova" / "nova-api.log"
    assert log_file.exists()
    assert "ERROR line 1" in log_file.read_text()


def test_invalid_tar():
    """Test handling of invalid tar content."""
    invalid_content = b"This is not a valid tar file"
    
    with pytest.raises(ValueError, match="Invalid tar archive"):
        safe_extract_tar(invalid_content, "invalid.tar.gz")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

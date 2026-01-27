"""
Smoke tests for bundle parser functionality.
"""
import io
import tarfile
import tempfile
from pathlib import Path

import pytest

from app.parsers.bundle_parser import BundleParser
from app.utils.safe_extract import safe_extract_tar


def create_test_bundle() -> bytes:
    """
    Create a minimal test bundle with typical structure.
    
    Returns:
        Bytes of tar.gz archive
    """
    buffer = io.BytesIO()
    
    files = {
        "controller-1_ai_bundle_20260127_143022/cmd/services_failed.txt": "apache2.service\nnova-api.service\nrabbitmq-server.service\n",
        "controller-1_ai_bundle_20260127_143022/cmd/listen_ports.txt": "tcp LISTEN 0 511 *:80 *:* users:((\"apache2\",pid=1234))\ntcp LISTEN 0 128 *:5672 *:* users:((\"rabbitmq\",pid=5678))\n",
        "controller-1_ai_bundle_20260127_143022/logs/journal_haproxy.txt": "Jan 27 14:30:22 controller-1 haproxy[1234]: horizon_backend has no server available\nJan 27 14:30:25 controller-1 haproxy[1234]: Server horizon_backend/controller-1 is DOWN\n",
        "controller-1_ai_bundle_20260127_143022/logs/journal_nova-api.txt": "2026-01-27 14:30:00.123 ERROR nova.api Connection refused to database\n2026-01-27 14:30:01.456 ERROR nova.api Traceback (most recent call last):\n2026-01-27 14:30:02.789 ERROR nova.api sqlalchemy.exc.OperationalError: connection refused\n",
    }
    
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        for file_path, content in files.items():
            tarinfo = tarfile.TarInfo(name=file_path)
            tarinfo.size = len(content.encode())
            tar.addfile(tarinfo, io.BytesIO(content.encode()))
    
    buffer.seek(0)
    return buffer.read()


def test_parser_smoke():
    """Smoke test: parse a minimal test bundle."""
    # Create test bundle
    tar_content = create_test_bundle()
    
    # Extract bundle
    extracted_path = safe_extract_tar(tar_content, "test_bundle.tar.gz")
    
    # Parse bundle
    parser = BundleParser(extracted_path)
    result = parser.analyze()
    
    # Verify structure
    assert "metadata" in result
    assert "failed_services" in result
    assert "listen_summary" in result
    assert "haproxy_findings" in result
    assert "error_summary" in result
    assert "recommendations" in result
    
    # Verify metadata
    metadata = result["metadata"]
    assert metadata["hostname"] == "controller-1"
    assert metadata["timestamp"] == "20260127_143022"
    assert metadata["extracted_file_count"] > 0
    
    # Verify failed services
    failed_services = result["failed_services"]
    assert "apache2.service" in failed_services
    assert "nova-api.service" in failed_services
    assert "rabbitmq-server.service" in failed_services
    
    # Verify listen summary
    listen_summary = result["listen_summary"]
    assert len(listen_summary) >= 2
    ports = [ls["port"] for ls in listen_summary]
    assert "80" in ports
    assert "5672" in ports
    
    # Verify HAProxy findings
    haproxy = result["haproxy_findings"]
    assert haproxy is not None
    assert len(haproxy["has_no_server_available"]) > 0
    assert "horizon" in haproxy["has_no_server_available"][0].lower()
    
    # Verify error summary
    errors = result["error_summary"]
    assert len(errors) > 0
    
    # Check that nova errors are captured
    nova_errors = [e for e in errors if "nova" in e["service"].lower()]
    assert len(nova_errors) > 0
    
    # Verify recommendations
    recommendations = result["recommendations"]
    assert len(recommendations) > 0
    
    # Should have horizon/apache recommendation due to HAProxy finding
    horizon_rec = [r for r in recommendations if "apache" in r["title"].lower() or "horizon" in r["title"].lower()]
    assert len(horizon_rec) > 0
    assert len(horizon_rec[0]["commands"]) > 0


def test_parser_missing_directories():
    """Test parser handles missing directories gracefully."""
    # Create bundle with only metadata
    buffer = io.BytesIO()
    files = {
        "minimal_bundle/readme.txt": "This is a minimal bundle\n",
    }
    
    with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
        for file_path, content in files.items():
            tarinfo = tarfile.TarInfo(name=file_path)
            tarinfo.size = len(content.encode())
            tar.addfile(tarinfo, io.BytesIO(content.encode()))
    
    buffer.seek(0)
    tar_content = buffer.read()
    
    # Extract and parse
    extracted_path = safe_extract_tar(tar_content, "minimal.tar.gz")
    parser = BundleParser(extracted_path)
    result = parser.analyze()
    
    # Should not crash
    assert result is not None
    assert result["failed_services"] == []
    assert result["listen_summary"] == []


def test_parser_hostname_extraction():
    """Test hostname extraction from various formats."""
    test_cases = [
        ("controller-1_ai_bundle_20260127", "controller-1"),
        ("compute-node-3_bundle_2026_01_27", "compute-node-3"),
        ("test_bundle", "test"),
    ]
    
    for dirname, expected_hostname in test_cases:
        # Create minimal bundle
        buffer = io.BytesIO()
        files = {
            f"{dirname}/test.txt": "content",
        }
        
        with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
            for file_path, content in files.items():
                tarinfo = tarfile.TarInfo(name=file_path)
                tarinfo.size = len(content.encode())
                tar.addfile(tarinfo, io.BytesIO(content.encode()))
        
        buffer.seek(0)
        tar_content = buffer.read()
        
        extracted_path = safe_extract_tar(tar_content, f"{dirname}.tar.gz")
        parser = BundleParser(extracted_path)
        result = parser.analyze()
        
        assert result["metadata"]["hostname"] == expected_hostname


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

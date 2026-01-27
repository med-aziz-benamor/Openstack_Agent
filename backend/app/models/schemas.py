"""
Pydantic models for API request/response schemas.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")


class VersionResponse(BaseModel):
    """Version response."""
    version: str = Field(..., description="API version")


class BundleMetadata(BaseModel):
    """Bundle metadata extracted from filename and structure."""
    hostname: Optional[str] = Field(None, description="Detected hostname")
    timestamp: Optional[str] = Field(None, description="Bundle timestamp")
    file_hash: str = Field(..., description="SHA256 hash of uploaded file")
    uploaded_filename: Optional[str] = Field(None, description="Original filename")
    extracted_file_count: int = Field(0, description="Number of extracted files")
    extracted_dir_count: int = Field(0, description="Number of extracted directories")


class HAProxyFindings(BaseModel):
    """HAProxy-specific findings."""
    has_no_server_available: List[str] = Field(
        default_factory=list,
        description="Lines indicating backend has no servers"
    )
    server_up_down: List[str] = Field(
        default_factory=list,
        description="Server UP/DOWN transition events"
    )
    timeouts: List[str] = Field(
        default_factory=list,
        description="Layer7 timeout events"
    )


class ErrorEntry(BaseModel):
    """Individual error entry with context."""
    service: str = Field(..., description="Service name (e.g., nova-api, haproxy)")
    line: str = Field(..., description="Error line content")
    count: int = Field(1, description="Number of occurrences")
    source_file: Optional[str] = Field(None, description="Source log file")


class Recommendation(BaseModel):
    """Troubleshooting recommendation."""
    title: str = Field(..., description="Recommendation title")
    why: str = Field(..., description="Reason for this recommendation")
    commands: List[str] = Field(
        default_factory=list,
        description="Suggested commands to run"
    )


class ListenSummary(BaseModel):
    """Port listener summary."""
    port: str = Field(..., description="Port number")
    process: Optional[str] = Field(None, description="Process name")
    full_line: str = Field(..., description="Full line from listen_ports.txt")


class AnalysisResponse(BaseModel):
    """Complete bundle analysis response."""
    metadata: BundleMetadata = Field(..., description="Bundle metadata")
    failed_services: List[str] = Field(
        default_factory=list,
        description="List of failed services"
    )
    listen_summary: List[ListenSummary] = Field(
        default_factory=list,
        description="Summary of listening ports"
    )
    haproxy_findings: Optional[HAProxyFindings] = Field(
        None,
        description="HAProxy-specific findings"
    )
    error_summary: List[ErrorEntry] = Field(
        default_factory=list,
        description="Top errors grouped by service"
    )
    recommendations: List[Recommendation] = Field(
        default_factory=list,
        description="Suggested next steps"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "hostname": "controller-1",
                    "timestamp": "20260127_143022",
                    "file_hash": "abc123...",
                    "uploaded_filename": "controller-1_ai_bundle_20260127_143022.tar.gz",
                    "extracted_file_count": 45,
                    "extracted_dir_count": 8
                },
                "failed_services": ["apache2.service", "nova-api.service"],
                "listen_summary": [
                    {
                        "port": "80",
                        "process": "apache2",
                        "full_line": "tcp LISTEN 0 511 *:80 *:* users:((\"apache2\",pid=1234))"
                    }
                ],
                "haproxy_findings": {
                    "has_no_server_available": [
                        "horizon_backend has no server available"
                    ],
                    "server_up_down": [],
                    "timeouts": []
                },
                "error_summary": [
                    {
                        "service": "nova-api",
                        "line": "ERROR: Connection refused to database",
                        "count": 15,
                        "source_file": "journal_nova-api.txt"
                    }
                ],
                "recommendations": [
                    {
                        "title": "Check Apache2 and Horizon availability",
                        "why": "HAProxy reports horizon_backend has no servers available",
                        "commands": [
                            "ss -lntp | egrep ':80|:443'",
                            "apache2ctl -S",
                            "curl -I http://controller-1/horizon/"
                        ]
                    }
                ]
            }
        }

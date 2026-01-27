"""
Log extractors for parsing error messages from various OpenStack service logs.
"""
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List

from app.models.schemas import ErrorEntry

logger = logging.getLogger(__name__)


class LogExtractor:
    """Extract and analyze errors from OpenStack log files."""
    
    # Keywords that indicate error lines
    ERROR_KEYWORDS = [
        "error", "exception", "traceback", "critical", "fatal",
        "failed", "failure", "timeout", "refused", "down",
        "unavailable", "500", "401", "403", "404", "503"
    ]
    
    # Service name patterns
    SERVICE_PATTERNS = {
        "nova": ["nova-api", "nova-compute", "nova-conductor", "nova-scheduler"],
        "neutron": ["neutron-server", "neutron-openvswitch-agent", "neutron-dhcp-agent", "neutron-l3-agent"],
        "keystone": ["keystone", "keystone-api"],
        "glance": ["glance-api", "glance-registry"],
        "cinder": ["cinder-api", "cinder-scheduler", "cinder-volume"],
        "horizon": ["horizon", "apache2", "httpd"],
        "haproxy": ["haproxy"],
        "rabbitmq": ["rabbitmq", "rabbit"],
        "mariadb": ["mariadb", "mysql", "galera"],
        "gnocchi": ["gnocchi"],
        "ceilometer": ["ceilometer"],
        "heat": ["heat-api", "heat-engine"],
        "swift": ["swift"],
        "placement": ["placement-api", "placement"],
    }
    
    def __init__(self, logs_dir: Path):
        """
        Initialize log extractor.
        
        Args:
            logs_dir: Path to logs directory in bundle
        """
        self.logs_dir = Path(logs_dir)
        
    def extract_errors(self, max_errors: int = 30) -> List[ErrorEntry]:
        """
        Extract top errors from all log files.
        
        Args:
            max_errors: Maximum number of error entries to return
            
        Returns:
            List of error entries sorted by frequency
        """
        if not self.logs_dir.exists():
            logger.warning(f"Logs directory does not exist: {self.logs_dir}")
            return []
        
        # Collect all log files
        log_files = []
        log_files.extend(self.logs_dir.glob("**/*.txt"))
        log_files.extend(self.logs_dir.glob("**/*.log"))
        
        logger.debug(f"Found {len(log_files)} log files to parse")
        
        # Extract errors from each file
        error_lines: Dict[str, Dict[str, any]] = {}  # line -> {count, service, source}
        
        for log_file in log_files:
            service = self._infer_service(log_file.name)
            errors = self._extract_from_file(log_file)
            
            for error_line in errors:
                # Normalize the error line for deduplication
                normalized = self._normalize_line(error_line)
                
                if normalized not in error_lines:
                    error_lines[normalized] = {
                        "line": error_line,
                        "count": 1,
                        "service": service,
                        "source_file": log_file.name
                    }
                else:
                    error_lines[normalized]["count"] += 1
        
        # Convert to ErrorEntry objects and sort by count
        entries = [
            ErrorEntry(
                service=data["service"],
                line=data["line"][:500],  # Truncate very long lines
                count=data["count"],
                source_file=data["source_file"]
            )
            for data in error_lines.values()
        ]
        
        # Sort by count descending
        entries.sort(key=lambda x: x.count, reverse=True)
        
        logger.info(f"Extracted {len(entries)} unique error entries")
        return entries[:max_errors]
    
    def _extract_from_file(self, log_file: Path) -> List[str]:
        """
        Extract error lines from a single log file.
        
        Args:
            log_file: Path to log file
            
        Returns:
            List of error lines
        """
        errors = []
        
        try:
            content = log_file.read_text(errors="ignore")
            lines = content.splitlines()
            
            for line in lines:
                if self._is_error_line(line):
                    errors.append(line.strip())
            
        except Exception as e:
            logger.warning(f"Failed to extract from {log_file.name}: {e}")
        
        return errors
    
    def _is_error_line(self, line: str) -> bool:
        """
        Check if a line contains error indicators.
        
        Args:
            line: Log line to check
            
        Returns:
            True if line appears to be an error
        """
        line_lower = line.lower()
        
        # Check for error keywords
        for keyword in self.ERROR_KEYWORDS:
            if keyword in line_lower:
                # Exclude common false positives
                if "no error" in line_lower or "0 error" in line_lower:
                    continue
                return True
        
        return False
    
    def _infer_service(self, filename: str) -> str:
        """
        Infer service name from log filename.
        
        Args:
            filename: Log filename
            
        Returns:
            Service name
        """
        filename_lower = filename.lower()
        
        # Try to match against known service patterns
        for service, patterns in self.SERVICE_PATTERNS.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    return service
        
        # Extract from journal_<service>.txt format
        if filename_lower.startswith("journal_"):
            service = filename[8:].replace(".txt", "").replace(".log", "")
            return service
        
        # Default to filename without extension
        return filename.replace(".txt", "").replace(".log", "")
    
    def _normalize_line(self, line: str) -> str:
        """
        Normalize error line for deduplication.
        
        Replaces timestamps, IDs, and other variable parts with placeholders.
        
        Args:
            line: Original error line
            
        Returns:
            Normalized line
        """
        # Remove timestamps (various formats)
        normalized = re.sub(
            r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(\.\d+)?',
            'TIMESTAMP',
            line
        )
        
        # Remove UUIDs
        normalized = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            'UUID',
            normalized,
            flags=re.IGNORECASE
        )
        
        # Remove IP addresses
        normalized = re.sub(
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'IP',
            normalized
        )
        
        # Remove PIDs
        normalized = re.sub(r'\bpid[=:\s]+\d+\b', 'PID', normalized, flags=re.IGNORECASE)
        
        # Remove hex addresses
        normalized = re.sub(r'0x[0-9a-f]+', 'ADDR', normalized, flags=re.IGNORECASE)
        
        # Remove long numbers (likely IDs)
        normalized = re.sub(r'\b\d{6,}\b', 'ID', normalized)
        
        return normalized.strip()

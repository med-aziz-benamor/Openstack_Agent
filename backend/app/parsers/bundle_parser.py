"""
Main bundle parser for OpenStack diagnostic bundles.
"""
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.models.schemas import (
    BundleMetadata,
    ErrorEntry,
    HAProxyFindings,
    ListenSummary,
    Recommendation,
)
from app.parsers.log_extractors import LogExtractor
from app.utils.text import deduplicate_lines, extract_hostname_from_path

logger = logging.getLogger(__name__)


class BundleParser:
    """Parser for OpenStack diagnostic bundle analysis."""
    
    def __init__(self, bundle_path: Path):
        """
        Initialize bundle parser.
        
        Args:
            bundle_path: Path to extracted bundle directory
        """
        self.bundle_path = Path(bundle_path)
        self.cmd_dir = self.bundle_path / "cmd"
        self.logs_dir = self.bundle_path / "logs"
        self.configs_dir = self.bundle_path / "configs"
        
        logger.debug(f"Initialized parser for bundle: {self.bundle_path}")
    
    def __del__(self):
        """Cleanup: remove extracted bundle directory."""
        try:
            if self.bundle_path.exists():
                shutil.rmtree(self.bundle_path)
                logger.debug(f"Cleaned up bundle: {self.bundle_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup bundle {self.bundle_path}: {e}")
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform complete bundle analysis.
        
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Starting analysis of bundle: {self.bundle_path}")
        
        # Extract metadata
        metadata = self._extract_metadata()
        
        # Parse failed services
        failed_services = self._parse_failed_services()
        
        # Parse listen ports
        listen_summary = self._parse_listen_ports()
        
        # Parse HAProxy findings
        haproxy_findings = self._parse_haproxy()
        
        # Extract and summarize errors
        error_summary = self._extract_errors()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            failed_services=failed_services,
            haproxy_findings=haproxy_findings,
            error_summary=error_summary
        )
        
        return {
            "metadata": metadata.model_dump(),
            "failed_services": failed_services,
            "listen_summary": [ls.model_dump() for ls in listen_summary],
            "haproxy_findings": haproxy_findings.model_dump() if haproxy_findings else None,
            "error_summary": [err.model_dump() for err in error_summary],
            "recommendations": [rec.model_dump() for rec in recommendations],
        }
    
    def _extract_metadata(self) -> BundleMetadata:
        """Extract bundle metadata from structure and filenames."""
        # Try to extract hostname from bundle directory name
        hostname = extract_hostname_from_path(self.bundle_path.name)
        
        # Try to extract timestamp from directory name
        timestamp = None
        parts = self.bundle_path.name.split("_")
        for i, part in enumerate(parts):
            if "bundle" in part.lower() and i + 1 < len(parts):
                # Likely format: HOST_ai_bundle_TIMESTAMP or similar
                timestamp = "_".join(parts[i + 1:])
                break
        
        # Count extracted files and directories
        file_count = sum(1 for _ in self.bundle_path.rglob("*") if _.is_file())
        dir_count = sum(1 for _ in self.bundle_path.rglob("*") if _.is_dir())
        
        return BundleMetadata(
            hostname=hostname,
            timestamp=timestamp,
            file_hash="",  # Will be set by main.py
            extracted_file_count=file_count,
            extracted_dir_count=dir_count
        )
    
    def _parse_failed_services(self) -> List[str]:
        """Parse failed services from cmd/services_failed.txt."""
        failed_services = []
        
        # Try services_failed.txt
        services_failed_file = self.cmd_dir / "services_failed.txt"
        if services_failed_file.exists():
            try:
                content = services_failed_file.read_text(errors="ignore")
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        failed_services.append(line)
            except Exception as e:
                logger.warning(f"Failed to parse services_failed.txt: {e}")
        
        # Also check services_running_failed.txt
        running_failed_file = self.cmd_dir / "services_running_failed.txt"
        if running_failed_file.exists():
            try:
                content = running_failed_file.read_text(errors="ignore")
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and line not in failed_services:
                        failed_services.append(line)
            except Exception as e:
                logger.warning(f"Failed to parse services_running_failed.txt: {e}")
        
        logger.debug(f"Found {len(failed_services)} failed services")
        return failed_services
    
    def _parse_listen_ports(self) -> List[ListenSummary]:
        """Parse listening ports from cmd/listen_ports.txt."""
        listen_summary = []
        
        listen_file = self.cmd_dir / "listen_ports.txt"
        if not listen_file.exists():
            return listen_summary
        
        try:
            content = listen_file.read_text(errors="ignore")
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # Parse port and process from ss/netstat output
                # Example: tcp LISTEN 0 511 *:80 *:* users:(("apache2",pid=1234))
                port = None
                process = None
                
                parts = line.split()
                for i, part in enumerate(parts):
                    # Look for port in format *:PORT or IP:PORT
                    if ":" in part and not part.startswith("users"):
                        port_candidate = part.split(":")[-1]
                        if port_candidate.isdigit():
                            port = port_candidate
                            break
                
                # Extract process name
                if "users:" in line:
                    try:
                        users_part = line.split("users:")[1]
                        # Extract from (("process_name",pid=123))
                        if '("' in users_part:
                            process = users_part.split('("')[1].split('"')[0]
                    except:
                        pass
                
                if port:
                    listen_summary.append(
                        ListenSummary(
                            port=port,
                            process=process,
                            full_line=line
                        )
                    )
        
        except Exception as e:
            logger.warning(f"Failed to parse listen_ports.txt: {e}")
        
        logger.debug(f"Found {len(listen_summary)} listening ports")
        return listen_summary
    
    def _parse_haproxy(self) -> Optional[HAProxyFindings]:
        """Parse HAProxy-specific findings from logs."""
        has_no_server = []
        server_up_down = []
        timeouts = []
        
        # Look for HAProxy journal or log files
        haproxy_files = []
        
        if self.logs_dir.exists():
            haproxy_files.extend(self.logs_dir.glob("**/journal_haproxy*.txt"))
            haproxy_files.extend(self.logs_dir.glob("**/haproxy*.log"))
        
        if not haproxy_files:
            return None
        
        for log_file in haproxy_files:
            try:
                content = log_file.read_text(errors="ignore")
                for line in content.splitlines():
                    line_lower = line.lower()
                    
                    if "has no server available" in line_lower:
                        has_no_server.append(line.strip())
                    
                    if " is down" in line_lower or " is up" in line_lower:
                        if "server " in line_lower or "backend " in line_lower:
                            server_up_down.append(line.strip())
                    
                    if "layer7 timeout" in line_lower or "l7tout" in line_lower:
                        timeouts.append(line.strip())
            
            except Exception as e:
                logger.warning(f"Failed to parse HAProxy log {log_file}: {e}")
        
        # Deduplicate
        has_no_server = deduplicate_lines(has_no_server, max_items=20)
        server_up_down = deduplicate_lines(server_up_down, max_items=20)
        timeouts = deduplicate_lines(timeouts, max_items=20)
        
        logger.debug(
            f"HAProxy findings: {len(has_no_server)} no-server, "
            f"{len(server_up_down)} up/down, {len(timeouts)} timeouts"
        )
        
        return HAProxyFindings(
            has_no_server_available=has_no_server,
            server_up_down=server_up_down,
            timeouts=timeouts
        )
    
    def _extract_errors(self) -> List[ErrorEntry]:
        """Extract and summarize errors from all log files."""
        extractor = LogExtractor(self.logs_dir)
        errors = extractor.extract_errors(max_errors=30)
        
        logger.debug(f"Extracted {len(errors)} error entries")
        return errors
    
    def _generate_recommendations(
        self,
        failed_services: List[str],
        haproxy_findings: Optional[HAProxyFindings],
        error_summary: List[ErrorEntry]
    ) -> List[Recommendation]:
        """Generate troubleshooting recommendations based on findings."""
        recommendations = []
        
        # HAProxy horizon backend issue
        if haproxy_findings and any("horizon" in line.lower() for line in haproxy_findings.has_no_server_available):
            recommendations.append(Recommendation(
                title="Check Apache2 and Horizon availability",
                why="HAProxy reports horizon_backend has no servers available",
                commands=[
                    "ss -lntp | egrep ':80|:443'",
                    "apache2ctl -S",
                    "systemctl status apache2",
                    "curl -I http://<node_ip>/horizon/",
                    "journalctl -u apache2 --since '2 hours ago' --no-pager | tail -n 200"
                ]
            ))
        
        # RabbitMQ issues
        rabbitmq_errors = any("rabbitmq" in err.service.lower() for err in error_summary)
        if rabbitmq_errors or "rabbitmq" in " ".join(failed_services).lower():
            recommendations.append(Recommendation(
                title="Investigate RabbitMQ cluster health",
                why="RabbitMQ errors detected or service failed",
                commands=[
                    "rabbitmq-diagnostics cluster_status",
                    "rabbitmq-diagnostics check_port_connectivity",
                    "ss -lntp | grep 25672",
                    "journalctl -u rabbitmq-server --since '1 hour ago' --no-pager"
                ]
            ))
        
        # Database issues
        db_keywords = ["mariadb", "mysql", "galera", "wsrep"]
        db_errors = any(
            any(kw in err.service.lower() or kw in err.line.lower() for kw in db_keywords)
            for err in error_summary
        )
        if db_errors:
            recommendations.append(Recommendation(
                title="Check MariaDB/Galera cluster status",
                why="Database-related errors detected",
                commands=[
                    "mysql -e \"SHOW STATUS LIKE 'wsrep_%';\"",
                    "cat /var/lib/mysql/grastate.dat",
                    "systemctl status mariadb",
                    "journalctl -u mariadb --since '1 hour ago' --no-pager"
                ]
            ))
        
        # Nova API issues
        if any("nova" in err.service.lower() for err in error_summary):
            recommendations.append(Recommendation(
                title="Verify Nova API and compute services",
                why="Nova-related errors found in logs",
                commands=[
                    "openstack compute service list",
                    "nova-status upgrade check",
                    "journalctl -u nova-api --since '1 hour ago' --no-pager | tail -n 100",
                    "grep ERROR /var/log/nova/nova-api.log | tail -n 50"
                ]
            ))
        
        # Neutron issues
        if any("neutron" in err.service.lower() for err in error_summary):
            recommendations.append(Recommendation(
                title="Check Neutron networking services",
                why="Neutron-related errors detected",
                commands=[
                    "openstack network agent list",
                    "ovs-vsctl show",
                    "journalctl -u neutron-server --since '1 hour ago' --no-pager",
                    "grep ERROR /var/log/neutron/neutron-server.log | tail -n 50"
                ]
            ))
        
        # Generic failed services
        if failed_services and not recommendations:
            recommendations.append(Recommendation(
                title="Investigate failed services",
                why=f"Found {len(failed_services)} failed service(s)",
                commands=[
                    f"systemctl status {failed_services[0]}" if failed_services else "systemctl list-units --failed",
                    f"journalctl -u {failed_services[0]} --since '1 hour ago' --no-pager" if failed_services else ""
                ]
            ))
        
        logger.debug(f"Generated {len(recommendations)} recommendations")
        return recommendations

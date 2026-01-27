#!/bin/bash
# Script to create a sample diagnostic bundle for testing

set -e

BUNDLE_NAME="controller-1_ai_bundle_$(date +%Y%m%d_%H%M%S)"
OUTPUT_DIR="./sample_bundles"
BUNDLE_DIR="${OUTPUT_DIR}/${BUNDLE_NAME}"

echo "Creating sample diagnostic bundle: ${BUNDLE_NAME}"

# Create directory structure
mkdir -p "${BUNDLE_DIR}/cmd"
mkdir -p "${BUNDLE_DIR}/logs"
mkdir -p "${BUNDLE_DIR}/configs"

# Create sample cmd files
cat > "${BUNDLE_DIR}/cmd/services_failed.txt" << 'EOF'
apache2.service
nova-api.service
rabbitmq-server.service
EOF

cat > "${BUNDLE_DIR}/cmd/services_running_failed.txt" << 'EOF'
neutron-openvswitch-agent.service
cinder-volume.service
EOF

cat > "${BUNDLE_DIR}/cmd/listen_ports.txt" << 'EOF'
tcp   LISTEN 0      511          0.0.0.0:80         0.0.0.0:*    users:(("apache2",pid=1234,fd=4))
tcp   LISTEN 0      128          0.0.0.0:5672       0.0.0.0:*    users:(("beam.smp",pid=5678,fd=50))
tcp   LISTEN 0      128          0.0.0.0:3306       0.0.0.0:*    users:(("mariadbd",pid=9012,fd=21))
tcp   LISTEN 0      128          0.0.0.0:5000       0.0.0.0:*    users:(("keystone-api",pid=3456,fd=5))
tcp   LISTEN 0      128          0.0.0.0:8774       0.0.0.0:*    users:(("nova-api",pid=7890,fd=6))
tcp   LISTEN 0      128          0.0.0.0:9696       0.0.0.0:*    users:(("neutron-serve",pid=2345,fd=4))
EOF

cat > "${BUNDLE_DIR}/cmd/ip_addr.txt" << 'EOF'
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    inet 192.168.1.10/24 brd 192.168.1.255 scope global eth0
3: br-ex: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
    inet 10.0.0.1/24 brd 10.0.0.255 scope global br-ex
EOF

# Create sample log files
cat > "${BUNDLE_DIR}/logs/journal_haproxy.txt" << 'EOF'
Jan 27 14:30:22 controller-1 haproxy[1234]: horizon_backend has no server available
Jan 27 14:30:23 controller-1 haproxy[1234]: Server horizon_backend/controller-1 is DOWN, reason: Layer7 timeout
Jan 27 14:30:25 controller-1 haproxy[1234]: backend nova_api_backend has no server available
Jan 27 14:31:10 controller-1 haproxy[1234]: Server nova_api_backend/controller-1 is UP
Jan 27 14:31:15 controller-1 haproxy[1234]: Layer7 timeout detected on backend horizon_backend
EOF

cat > "${BUNDLE_DIR}/logs/journal_nova-api.txt" << 'EOF'
2026-01-27 14:30:00.123 1234 ERROR nova.api.openstack Connection refused: [Errno 111] ECONNREFUSED
2026-01-27 14:30:01.456 1234 ERROR nova.api.openstack Traceback (most recent call last):
2026-01-27 14:30:01.457 1234 ERROR nova.api.openstack   File "/usr/lib/python3/site-packages/nova/db/api.py", line 45, in _connect
2026-01-27 14:30:02.789 1234 ERROR nova.api.openstack sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (2003, "Can't connect to MySQL server on '192.168.1.10:3306' (111)")
2026-01-27 14:30:05.123 1234 ERROR nova.api.openstack Connection refused: database unavailable
2026-01-27 14:30:10.456 1234 ERROR nova.api.openstack Failed to connect to placement API: Connection timeout
2026-01-27 14:30:15.789 1234 ERROR nova.compute.manager Exception during instance creation: Connection refused
2026-01-27 14:30:20.123 1234 ERROR nova.compute.manager Traceback (most recent call last):
2026-01-27 14:30:25.456 1234 ERROR nova.scheduler.manager Failed to schedule instance: No valid host found
2026-01-27 14:30:30.789 1234 ERROR nova.conductor.manager RPC timeout waiting for compute node response
EOF

cat > "${BUNDLE_DIR}/logs/journal_apache2.txt" << 'EOF'
Jan 27 14:29:50 controller-1 apache2[9876]: [wsgi:error] [pid 9876] ERROR:root:Connection refused to keystone
Jan 27 14:30:05 controller-1 apache2[9876]: [wsgi:error] [pid 9876] ERROR:horizon.exceptions HTTP 500 Internal Server Error
Jan 27 14:30:10 controller-1 apache2[9876]: [core:error] [pid 9877] (13)Permission denied: AH00072: make_sock: could not bind to address [::]:80
Jan 27 14:30:15 controller-1 apache2[9876]: [mpm_prefork:error] [pid 9878] AH00161: server reached MaxRequestWorkers setting
EOF

cat > "${BUNDLE_DIR}/logs/journal_rabbitmq-server.txt" << 'EOF'
2026-01-27 14:28:00.123 [error] <0.1234.0> Channel error on connection <0.5678.0> (192.168.1.10:45678 -> 192.168.1.11:5672):
2026-01-27 14:28:05.456 [error] <0.1234.0> Connection timeout detected
2026-01-27 14:28:10.789 [warning] <0.2345.0> Cluster partition detected between rabbit@controller-1 and rabbit@controller-2
2026-01-27 14:28:15.123 [error] <0.3456.0> Failed to synchronize queue: Connection refused
2026-01-27 14:28:20.456 [warning] <0.4567.0> High memory watermark reached, blocking publishers
EOF

cat > "${BUNDLE_DIR}/logs/journal_neutron-server.txt" << 'EOF'
2026-01-27 14:29:00.123 ERROR neutron.plugins.ml2.drivers.openvswitch Failed to connect to OVS: Connection refused
2026-01-27 14:29:05.456 ERROR neutron.agent.linux.ip_lib Command failed: ip netns add qdhcp-abc123
2026-01-27 14:29:10.789 ERROR neutron.db.db_base_plugin_v2 Database deadlock detected during port creation
2026-01-27 14:29:15.123 ERROR neutron.plugins.ml2.plugin Port binding failed: No suitable agent available
EOF

# Create a sample config file
cat > "${BUNDLE_DIR}/configs/nova.conf" << 'EOF'
[DEFAULT]
debug = True
log_dir = /var/log/nova
state_path = /var/lib/nova

[api_database]
connection = mysql+pymysql://nova:password@192.168.1.10/nova_api

[database]
connection = mysql+pymysql://nova:password@192.168.1.10/nova
EOF

# Create tar.gz
echo "Creating tar.gz archive..."
cd "${OUTPUT_DIR}"
tar -czf "${BUNDLE_NAME}.tar.gz" "${BUNDLE_NAME}"
cd - > /dev/null

# Cleanup
rm -rf "${BUNDLE_DIR}"

echo ""
echo "✅ Sample bundle created successfully!"
echo "📦 Location: ${OUTPUT_DIR}/${BUNDLE_NAME}.tar.gz"
echo ""
echo "You can now upload this bundle through the web interface at:"
echo "   http://localhost:8088"
echo ""
echo "Or test via curl:"
echo "   curl -X POST http://localhost:8088/api/analyze -F \"bundle=@${OUTPUT_DIR}/${BUNDLE_NAME}.tar.gz\""

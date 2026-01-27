# OpenStack Admin Assistant Portal

A web application for OpenStack administrators to upload diagnostic bundles and instantly analyze key findings including failed services, HAProxy backend health, log errors, and port listeners.

## Features

- 📦 **Bundle Analysis**: Upload `.tar.gz` diagnostic bundles for automatic parsing
- 🔍 **Service Monitoring**: Detect failed services and running issues
- 🌐 **HAProxy Health**: Parse backend availability, server status, and timeouts
- 📊 **Error Summary**: Aggregate and deduplicate errors from logs and journals
- 🎯 **Smart Recommendations**: Context-aware troubleshooting commands
- 💬 **Chatbase Assistant**: Embedded AI chat widget for additional support
- 🔒 **Secure**: Path traversal protection, file size limits, no shell execution

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI, Uvicorn, Pydantic
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Reverse Proxy**: Nginx
- **Deployment**: Docker Compose
- **Security**: Safe tar extraction, SHA256 hashing, upload limits

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Run Locally

```bash
# Clone the repository
git clone <repo-url>
cd ProAdmin

# Start all services
docker compose up --build

# Access the application
# UI: http://localhost:8088
# API Health: http://localhost:8088/api/health
```

The application will be available at **http://localhost:8088**

### Development Mode

Run backend only for API development:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access API docs at http://localhost:8000/docs

For frontend development, open `frontend/index.html` directly in a browser or use a simple HTTP server:

```bash
cd frontend
python -m http.server 3000
```

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/version` - Application version
- `POST /api/analyze` - Upload and analyze bundle (multipart/form-data)

### Example API Usage

```bash
# Health check
curl http://localhost:8088/api/health

# Analyze bundle
curl -X POST http://localhost:8088/api/analyze \
  -F "bundle=@/path/to/diagnostic_bundle.tar.gz"
```

## Bundle Format

Expected diagnostic bundle structure:

```
<HOST>_ai_bundle_<TIMESTAMP>/
├── cmd/
│   ├── services_failed.txt
│   ├── services_running_failed.txt
│   ├── ip_addr.txt
│   ├── ip_route.txt
│   ├── listen_ports.txt
│   ├── rabbitmq_cluster_status.txt (optional)
│   └── ovs-vsctl_show.txt (optional)
├── logs/
│   ├── journal_<service>.txt
│   └── var/log/<service>/ (optional)
└── configs/ (optional)
```

## Deployment

### Docker Compose (Recommended)

The `docker-compose.yml` includes:
- **api**: FastAPI backend (port 8000 internal)
- **nginx**: Reverse proxy (port 8088 external)

Nginx routes:
- `/` → Frontend (static files)
- `/api` → Backend API

### Production Deployment on VM

#### Option 1: Docker Compose

```bash
# Install Docker & Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Deploy
cd ProAdmin
docker compose up -d

# Check logs
docker compose logs -f

# Update
git pull
docker compose up -d --build
```

#### Option 2: Native with systemd + Nginx

```bash
# Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx

# Setup backend
cd /opt
sudo git clone <repo-url> openstack-admin
cd openstack-admin/backend
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/openstack-admin.service > /dev/null <<EOF
[Unit]
Description=OpenStack Admin Assistant API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/openstack-admin/backend
Environment="PATH=/opt/openstack-admin/backend/venv/bin"
ExecStart=/opt/openstack-admin/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Setup Nginx
sudo cp nginx/nginx.conf /etc/nginx/sites-available/openstack-admin
sudo ln -s /etc/nginx/sites-available/openstack-admin /etc/nginx/sites-enabled/
sudo cp -r frontend/* /var/www/openstack-admin/
sudo nginx -t
sudo systemctl restart nginx

# Start services
sudo systemctl enable --now openstack-admin
sudo systemctl status openstack-admin

# Access at http://<server-ip>:8088
```

## Configuration

Environment variables (optional, see `.env.example`):

- `MAX_UPLOAD_SIZE_MB`: Maximum bundle size (default: 100)
- `TEMP_DIR`: Temporary extraction directory (default: /tmp)
- `LOG_LEVEL`: Logging level (default: info)

## Security Features

- ✅ Path traversal prevention during tar extraction
- ✅ File size limits (100MB default)
- ✅ No shell command execution
- ✅ Safe file handling with context managers
- ✅ SHA256 file integrity hashing
- ✅ Automatic cleanup of temporary files

## Testing

```bash
cd backend
pytest app/tests/ -v

# Run specific tests
pytest app/tests/test_safe_extract.py -v
pytest app/tests/test_parser_smoke.py -v
```

## Troubleshooting

### Port already in use
```bash
# Check what's using port 8088
sudo lsof -i :8088
# Or change port in docker-compose.yml
```

### Container fails to start
```bash
# Check logs
docker compose logs api
docker compose logs nginx

# Rebuild
docker compose down
docker compose up --build
```

### Upload fails
- Check file size (max 100MB by default)
- Verify file is valid .tar.gz format
- Check backend logs for specific error

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Use the embedded Chatbase assistant in the UI
- Check API documentation at `/docs` endpoint
- Review logs: `docker compose logs -f`

---

**Version**: 0.1.0  
**Last Updated**: January 2026

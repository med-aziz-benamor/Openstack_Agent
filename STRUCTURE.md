# OpenStack Admin Assistant Portal - Project Structure

## Repository Structure

```
ProAdmin/
├── README.md                    # Main documentation
├── LICENSE                      # MIT License
├── .gitignore                   # Git ignore patterns
├── docker-compose.yml           # Docker Compose configuration
├── .env.example                 # Environment variables template
├── Makefile                     # Convenience commands
├── setup.sh                     # Quick setup script
│
├── backend/                     # Python FastAPI backend
│   ├── Dockerfile              # Backend container image
│   ├── requirements.txt        # Python dependencies
│   ├── pytest.ini              # Pytest configuration
│   │
│   └── app/                    # Application code
│       ├── __init__.py
│       ├── main.py             # FastAPI application entry point
│       ├── config.py           # Configuration settings
│       │
│       ├── models/             # Pydantic models
│       │   ├── __init__.py
│       │   └── schemas.py      # API request/response schemas
│       │
│       ├── parsers/            # Bundle parsing logic
│       │   ├── __init__.py
│       │   ├── bundle_parser.py    # Main parser orchestrator
│       │   └── log_extractors.py   # Error extraction from logs
│       │
│       ├── utils/              # Utility functions
│       │   ├── __init__.py
│       │   ├── safe_extract.py     # Safe tar extraction
│       │   ├── hashing.py          # SHA256 hashing
│       │   └── text.py             # Text processing utilities
│       │
│       └── tests/              # Unit tests
│           ├── __init__.py
│           ├── test_safe_extract.py    # Security tests
│           └── test_parser_smoke.py    # Parser integration tests
│
├── frontend/                    # Static web frontend
│   ├── index.html              # Main HTML page
│   ├── app.js                  # JavaScript application logic
│   └── styles.css              # CSS styles
│
├── nginx/                       # Nginx reverse proxy
│   ├── Dockerfile              # Nginx container image
│   └── nginx.conf              # Nginx configuration
│
└── scripts/                     # Helper scripts
    └── create_sample_bundle.sh # Generate test bundle

```

## Component Responsibilities

### Backend (`backend/`)
- **FastAPI Application**: RESTful API for bundle analysis
- **Parser Engine**: Extracts and analyzes OpenStack diagnostic data
- **Security Layer**: Safe tar extraction, path traversal prevention
- **Error Analysis**: Intelligent error grouping and deduplication
- **Recommendations Engine**: Context-aware troubleshooting suggestions

### Frontend (`frontend/`)
- **Single Page Application**: Drag-and-drop file upload
- **Results Dashboard**: Interactive visualization of analysis results
- **Chatbase Integration**: Embedded AI assistant
- **Copy-to-Clipboard**: Easy command copying for recommendations

### Nginx (`nginx/`)
- **Reverse Proxy**: Routes `/` to frontend, `/api` to backend
- **Static File Serving**: Efficient frontend delivery
- **Upload Handling**: Supports large file uploads (100MB+)
- **Compression**: Gzip compression for better performance

## Data Flow

1. **Upload**: User uploads `.tar.gz` bundle via web interface
2. **Extraction**: Backend safely extracts to temporary directory
3. **Parsing**: Bundle structure analyzed, files parsed
4. **Analysis**: 
   - Failed services identified
   - HAProxy health checked
   - Errors extracted and grouped
   - Port listeners summarized
5. **Recommendations**: Context-aware troubleshooting steps generated
6. **Response**: JSON results sent to frontend
7. **Display**: Frontend renders interactive results
8. **Cleanup**: Temporary files automatically removed

## Security Measures

- ✅ Path traversal prevention in tar extraction
- ✅ File size limits (configurable, default 100MB)
- ✅ No shell command execution
- ✅ Safe file handling with context managers
- ✅ Input validation and sanitization
- ✅ Automatic cleanup of temporary files

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/version` - API version
- `POST /api/analyze` - Upload and analyze bundle

## Configuration

Environment variables (see `.env.example`):
- `MAX_UPLOAD_SIZE_MB` - Maximum bundle size
- `TEMP_DIR` - Temporary extraction directory
- `LOG_LEVEL` - Logging verbosity
- `API_HOST` - Backend host
- `API_PORT` - Backend port

## Development Workflow

1. **Local Development**: Use `make backend-dev` and `make frontend-dev`
2. **Testing**: Run `make test` for unit tests
3. **Production**: Deploy with `docker compose up -d`
4. **Monitoring**: Check logs with `make logs`

## Deployment Options

1. **Docker Compose** (Recommended): One command deployment
2. **Native with systemd**: Manual installation on VM
3. **Kubernetes**: Scale horizontally (not included in MVP)

## Testing

- **Unit Tests**: `pytest` for backend logic
- **Security Tests**: Path traversal prevention validation
- **Integration Tests**: Full bundle parsing smoke tests
- **Sample Data**: Generate test bundles with `create_sample_bundle.sh`

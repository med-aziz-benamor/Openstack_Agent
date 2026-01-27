# OpenStack Admin Assistant Portal - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Start the Application

```bash
# Make setup script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

Or manually:

```bash
# Build and start all services
docker compose up --build -d

# Wait a few seconds for services to initialize
# Check if everything is running
curl http://localhost:8088/api/health
```

### Step 2: Create a Test Bundle

```bash
# Make the script executable
chmod +x scripts/create_sample_bundle.sh

# Generate a sample diagnostic bundle
./scripts/create_sample_bundle.sh
```

This creates a realistic test bundle at `./sample_bundles/controller-1_ai_bundle_<timestamp>.tar.gz`

### Step 3: Upload and Analyze

**Option A: Web Interface**
1. Open http://localhost:8088 in your browser
2. Drag and drop the generated bundle or click "Browse Files"
3. Click "Analyze Bundle"
4. View the results in the dashboard

**Option B: API (curl)**
```bash
# Replace with your actual bundle path
curl -X POST http://localhost:8088/api/analyze \
  -F "bundle=@./sample_bundles/controller-1_ai_bundle_20260127_143022.tar.gz" \
  | jq .
```

## 📊 What You'll See

The analysis includes:

### 1. Bundle Metadata
- Hostname (extracted from bundle name)
- Timestamp
- File hash (SHA256)
- Extracted file counts

### 2. Failed Services
- List of systemd services that are in failed state
- Extracted from `cmd/services_failed.txt`

### 3. HAProxy Health
- Backends with no available servers
- Server UP/DOWN transitions
- Layer7 timeouts
- Parsed from HAProxy journal logs

### 4. Top Errors
- Errors grouped by service (Nova, Neutron, Keystone, etc.)
- Deduplication with occurrence counts
- Source file references
- Top 30 most frequent errors

### 5. Port Listeners Summary
- All listening ports
- Associated processes
- Full netstat/ss output details

### 6. Recommendations
- Context-aware troubleshooting steps
- Specific commands to run next
- Copy-to-clipboard functionality

## 🛠️ Common Tasks

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f nginx
```

### Stop Services
```bash
docker compose down
```

### Restart Services
```bash
docker compose restart
```

### Run Tests
```bash
# Inside container
docker compose exec api pytest app/tests/ -v

# Or locally (if you have Python setup)
cd backend
pytest app/tests/ -v
```

### Access API Documentation
Open http://localhost:8088/api/docs for interactive Swagger UI

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8088
sudo lsof -i :8088

# Change the port in docker-compose.yml
# Under nginx service, change "8088:80" to "8080:80" or another port
```

### Container Won't Start
```bash
# Check detailed logs
docker compose logs api

# Rebuild from scratch
docker compose down -v
docker compose up --build
```

### Upload Fails
- Check file size (max 100MB by default)
- Verify file is valid .tar.gz format
- Check backend logs: `docker compose logs api`

### API Returns 500 Error
```bash
# Check backend logs for detailed error
docker compose logs api | tail -n 50

# Check if extraction directory has permissions
docker compose exec api ls -la /tmp
```

## 📝 Next Steps

1. **Customize the Parser**: Edit `backend/app/parsers/bundle_parser.py` to add more analysis
2. **Add More Recommendations**: Extend `_generate_recommendations()` in bundle_parser.py
3. **Enhance Frontend**: Modify `frontend/index.html` and `frontend/app.js`
4. **Configure Limits**: Edit `.env` file to change upload size limits
5. **Deploy to Production**: See README.md for production deployment options

## 🔗 Useful Links

- **Web UI**: http://localhost:8088
- **API Docs**: http://localhost:8088/api/docs
- **API Health**: http://localhost:8088/api/health
- **API Version**: http://localhost:8088/api/version

## 💬 Chatbase Assistant

The Chatbase AI assistant widget is embedded in the bottom-right corner of the web interface. Use it for:
- Additional troubleshooting help
- OpenStack-specific questions
- Interpreting analysis results

## 🔄 Development Mode

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
python3 -m http.server 3000
# Or use any static file server
```

Now you can edit files and see changes immediately!

## 📚 Documentation

- [README.md](README.md) - Full documentation
- [STRUCTURE.md](STRUCTURE.md) - Repository structure
- [LICENSE](LICENSE) - MIT License

## 🎉 Success!

You now have a fully functional OpenStack Admin Assistant Portal running locally. Upload your diagnostic bundles and get instant insights!

# Ubuntu VM Deployment Guide

## Prerequisites
- Ubuntu VM with internet access
- SSH access to the VM
- At least 2GB free disk space

## Step 1: Transfer Project Files to Ubuntu VM

### Option A: Using SCP (Secure Copy)
```bash
# On your Mac, compress the project
cd /Users/azizbna/Documents/4\ ArcTic13/S2/PICloud/
tar -czf ProAdmin.tar.gz ProAdmin/

# Transfer to Ubuntu VM (replace with your VM details)
scp ProAdmin.tar.gz username@ubuntu-vm-ip:/home/username/

# On Ubuntu VM, extract
ssh username@ubuntu-vm-ip
cd /home/username/
tar -xzf ProAdmin.tar.gz
cd ProAdmin
```

### Option B: Using Git
```bash
# On your Mac, initialize git repo if not already done
cd /Users/azizbna/Documents/4\ ArcTic13/S2/PICloud/ProAdmin
git init
git add .
git commit -m "Initial commit"

# Push to GitHub/GitLab (or use git bundle for offline transfer)

# On Ubuntu VM, clone
git clone <your-repo-url>
cd ProAdmin
```

### Option C: Using rsync (Recommended for updates)
```bash
# On your Mac
rsync -avz --progress /Users/azizbna/Documents/4\ ArcTic13/S2/PICloud/ProAdmin/ \
  username@ubuntu-vm-ip:/home/username/ProAdmin/
```

## Step 2: Install Docker on Ubuntu VM

```bash
# Update package index
sudo apt-get update

# Install required packages
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
exit
# SSH back in
ssh username@ubuntu-vm-ip
```

## Step 3: Verify Docker Installation

```bash
# Check Docker version
docker --version
docker compose version

# Test Docker
docker run hello-world
```

## Step 4: Deploy the Application

```bash
cd /home/username/ProAdmin

# Make scripts executable
chmod +x scripts/*.sh

# Start the application
docker compose up --build -d

# Check container status
docker compose ps

# View logs if needed
docker compose logs -f
```

## Step 5: Access the Application

### Local Access (on VM)
```bash
curl http://localhost:8088/api/health
```

### Remote Access (from your Mac)
```bash
# Open http://ubuntu-vm-ip:8088 in your browser
```

**Note**: You may need to configure Ubuntu firewall:
```bash
# Allow port 8088
sudo ufw allow 8088/tcp
sudo ufw status
```

## Step 6: Verify Deployment

```bash
# Check API health
curl http://localhost:8088/api/health

# Check version
curl http://localhost:8088/api/version

# View container logs
docker compose logs api
docker compose logs nginx
```

## Managing the Application

### Start
```bash
docker compose start
```

### Stop
```bash
docker compose stop
```

### Restart
```bash
docker compose restart
```

### Rebuild after changes
```bash
docker compose down
docker compose up --build -d
```

### View logs
```bash
docker compose logs -f api      # Backend logs
docker compose logs -f nginx    # Nginx logs
docker compose logs -f          # All logs
```

### Remove everything
```bash
docker compose down -v
docker system prune -a
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8088
sudo lsof -i :8088
# Or
sudo netstat -tulpn | grep 8088

# Kill the process if needed
sudo kill -9 <PID>
```

### Permission Issues
```bash
# If you get permission denied errors
sudo chown -R $USER:$USER /home/username/ProAdmin
```

### Docker Daemon Not Running
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### Network Issues
```bash
# Check Docker networks
docker network ls

# Inspect specific network
docker network inspect proadmin_default
```

## Performance Tips

### Increase Docker Resources (if needed)
Edit `/etc/docker/daemon.json`:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Then restart Docker:
```bash
sudo systemctl restart docker
```

## Quick Command Reference

```bash
# Full deployment from scratch
cd ProAdmin
docker compose up --build -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Stop everything
docker compose down

# Clean restart
docker compose down && docker compose up --build -d
```

## Security Recommendations

1. **Firewall Configuration**:
   ```bash
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 8088/tcp
   ```

2. **Update regularly**:
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

3. **Monitor logs**:
   ```bash
   docker compose logs -f | tee application.log
   ```

## Next Steps

Once deployed, you can:
1. Access the web UI at `http://ubuntu-vm-ip:8088`
2. Create test bundles with `./scripts/create_sample_bundle.sh`
3. Upload diagnostic bundles for analysis
4. Monitor logs with `docker compose logs -f`

## Support

For issues, check:
- Container logs: `docker compose logs`
- Docker status: `docker compose ps`
- System resources: `docker stats`
- Project documentation: `README.md`, `QUICKSTART.md`

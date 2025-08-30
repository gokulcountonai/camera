#!/bin/bash
# Online Installation Script for Camera Streaming System
# This script downloads and installs everything when internet is available

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/edgecam/projects/knitting-rpi-gs"
SERVICE_USER="edgecam"
SERVICE_GROUP="edgecam"
GITHUB_REPO="https://github.com/lighthouseai/knitting-rpi-gs"
GITHUB_BRANCH="2.4.2/greencam1"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Online Installation Script${NC}"
echo -e "${BLUE}  Camera Streaming System${NC}"
echo -e "${BLUE}================================${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check internet connectivity
print_status "Checking internet connectivity..."
if ! ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    print_error "No internet connection detected. Please check your network connection."
    exit 1
fi

print_status "Internet connection confirmed. Starting online installation..."

# Step 1: Update system packages
print_status "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Step 2: Install required system packages
print_status "Installing required system packages..."

# Core system packages
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    htop \
    vim \
    nano \
    build-essential \
    cmake \
    pkg-config

# Camera and image processing packages
sudo apt-get install -y \
    python3-picamera2 \
    python3-opencv \
    python3-numpy \
    python3-pil \
    python3-pil.imagetk

# Redis and networking packages
sudo apt-get install -y \
    redis-server \
    python3-redis \
    python3-requests \
    python3-urllib3

# System monitoring packages
sudo apt-get install -y \
    python3-psutil \
    python3-setuptools \
    python3-wheel

# Web server and API packages
sudo apt-get install -y \
    python3-flask \
    python3-flask-cors \
    python3-werkzeug

# Additional utilities
sudo apt-get install -y \
    python3-yaml \
    python3-json5 \
    python3-dateutil \
    python3-tz

# Development tools (optional)
print_warning "Install development tools? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    sudo apt-get install -y \
        python3-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libv4l-dev \
        libxvidcore-dev \
        libx264-dev \
        libgtk-3-dev \
        libatlas-base-dev \
        gfortran
fi

# Step 3: Configure Redis
print_status "Configuring Redis..."
sudo systemctl stop redis-server 2>/dev/null || true

# Create optimized Redis configuration
sudo tee /etc/redis/redis.conf > /dev/null <<'EOF'
# Redis configuration optimized for camera streaming
bind 127.0.0.1 169.254.0.1
port 6379
timeout 300
tcp-keepalive 60
databases 16

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

# AOF persistence
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Performance optimizations
tcp-backlog 511
databases 16
always-show-logo no
set-proc-title yes
proc-title-template "{title} {listen-addr} {server-mode}"
loglevel notice
logfile ""
syslog-enabled no
syslog-ident redis
syslog-facility local0
EOF

# Enable and start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Step 4: Configure system settings
print_status "Configuring system settings..."

# Enable camera interface
sudo raspi-config nonint do_camera 0

# Set GPU memory split (256MB for camera)
sudo raspi-config nonint do_memory_split 256

# Enable I2C
sudo raspi-config nonint do_i2c 0

# Enable SPI if needed
print_warning "Enable SPI interface? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    sudo raspi-config nonint do_spi 0
fi

# Configure network for static IP
print_warning "Configure static IP 169.254.0.1 for offline operation? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    sudo tee -a /etc/dhcpcd.conf > /dev/null <<'EOF'

# Static IP configuration for camera streaming
interface eth0
static ip_address=169.254.0.1/24
static domain_name_servers=8.8.8.8 8.8.4.4
EOF
    print_status "Static IP configured. Reboot required for network changes."
fi

# Step 5: Create service user
print_status "Creating service user..."
if ! id "edgecam" &>/dev/null; then
    sudo useradd -m -s /bin/bash edgecam
    sudo usermod -aG sudo edgecam
    print_status "User 'edgecam' created. Set password:"
    sudo passwd edgecam
else
    print_status "User 'edgecam' already exists"
fi

# Step 6: Create necessary directories
print_status "Creating directories..."
sudo mkdir -p /home/edgecam/projects
sudo mkdir -p /home/edgecam/images
sudo mkdir -p /home/edgecam/logs
sudo mkdir -p /home/edgecam/backups
sudo mkdir -p /var/log/camera-streaming

# Set permissions
sudo chown -R edgecam:edgecam /home/edgecam
sudo chown -R edgecam:edgecam /var/log/camera-streaming

# Step 7: Download project files
print_status "Downloading project files from GitHub..."

# Clone the repository
cd /home/edgecam/projects
sudo -u edgecam git clone $GITHUB_REPO knitting-rpi-gs
cd knitting-rpi-gs

# Switch to the correct branch
sudo -u edgecam git checkout $GITHUB_BRANCH

# Download additional files if needed
print_status "Downloading additional components..."

# Download Python packages requirements
sudo -u edgecam tee requirements.txt > /dev/null <<'EOF'
flask==2.3.3
flask-cors==4.0.0
redis==4.6.0
psutil==5.9.5
opencv-python==4.8.1.78
numpy==1.24.3
pillow==10.0.1
requests==2.31.0
pyyaml==6.0.1
python-dateutil==2.8.2
pytz==2023.3
EOF

# Step 8: Configure Python environment
print_status "Configuring Python environment..."
sudo -u edgecam python3 -m pip install --user --upgrade pip
sudo -u edgecam python3 -m pip install --user virtualenv

# Create virtual environment
sudo -u edgecam python3 -m venv /home/edgecam/venv
sudo -u edgecam /home/edgecam/venv/bin/pip install --upgrade pip

# Install Python packages in virtual environment
print_status "Installing Python packages in virtual environment..."
sudo -u edgecam /home/edgecam/venv/bin/pip install -r requirements.txt

# Step 9: Configure logrotate
print_status "Configuring log rotation..."
sudo tee /etc/logrotate.d/camera-streaming > /dev/null <<'EOF'
/home/edgecam/logs/*.log /var/log/camera-streaming/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 edgecam edgecam
    postrotate
        systemctl reload camera-streaming.service > /dev/null 2>&1 || true
    endscript
}
EOF

# Step 10: Configure system limits
print_status "Configuring system limits..."
sudo tee -a /etc/security/limits.conf > /dev/null <<'EOF'

# Camera streaming system limits
edgecam soft nofile 65536
edgecam hard nofile 65536
edgecam soft nproc 4096
edgecam hard nproc 4096
EOF

# Step 11: Configure sysctl for better performance
print_status "Configuring system performance..."
sudo tee -a /etc/sysctl.conf > /dev/null <<'EOF'

# Camera streaming system optimizations
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
vm.swappiness = 10
EOF

# Apply sysctl changes
sudo sysctl -p

# Step 12: Create systemd services
print_status "Creating systemd services..."

# Camera streaming service
sudo tee /etc/systemd/system/camera-streaming.service > /dev/null <<'EOF'
[Unit]
Description=Camera Streaming Service
After=network.target redis.service
Wants=redis.service

[Service]
Type=forking
User=edgecam
Group=edgecam
WorkingDirectory=/home/edgecam/projects/knitting-rpi-gs
ExecStart=/home/edgecam/projects/knitting-rpi-gs/run.sh
ExecStop=/bin/kill -TERM $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=camera-streaming

# Environment variables
Environment=PYTHONPATH=/home/edgecam/projects/knitting-rpi-gs
Environment=REDIS_HOST=169.254.0.1
Environment=REDIS_PORT=6379

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/home/edgecam/projects/knitting-rpi-gs /var/log /home/edgecam

[Install]
WantedBy=multi-user.target
EOF

# API service
sudo tee /etc/systemd/system/camera-api.service > /dev/null <<'EOF'
[Unit]
Description=Camera Streaming API Server
After=network.target redis.service camera-streaming.service
Wants=redis.service

[Service]
Type=simple
User=edgecam
Group=edgecam
WorkingDirectory=/home/edgecam/projects/knitting-rpi-gs
ExecStart=/home/edgecam/venv/bin/python3 /home/edgecam/projects/knitting-rpi-gs/api_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=camera-api

# Environment variables
Environment=PYTHONPATH=/home/edgecam/projects/knitting-rpi-gs
Environment=REDIS_HOST=169.254.0.1
Environment=REDIS_PORT=6379

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

# Step 13: Create startup script
print_status "Creating startup script..."
sudo -u edgecam tee "/home/edgecam/projects/knitting-rpi-gs/run.sh" > /dev/null <<'EOF'
#!/bin/bash
# Camera Streaming Startup Script

cd "/home/edgecam/projects/knitting-rpi-gs"

# Activate virtual environment
source /home/edgecam/venv/bin/activate

# Start the main camera streaming application
python3 cam1_stream.py &
CAM_PID=$!

# Start the monitoring system
python3 start.py &
MONITOR_PID=$!

# Wait for processes
wait $CAM_PID $MONITOR_PID
EOF

sudo chmod +x "/home/edgecam/projects/knitting-rpi-gs/run.sh"

# Step 14: Create health check script
print_status "Creating health check script..."
sudo -u edgecam tee "/home/edgecam/projects/knitting-rpi-gs/health_check.sh" > /dev/null <<'EOF'
#!/bin/bash
# Health check script for camera streaming system

cd "/home/edgecam/projects/knitting-rpi-gs"

# Check if services are running
if ! pgrep -f "cam1_stream.py" > /dev/null; then
    echo "ERROR: Camera streaming process not running"
    exit 1
fi

if ! pgrep -f "start.py" > /dev/null; then
    echo "ERROR: Monitoring process not running"
    exit 1
fi

# Check Redis connection
if ! python3 -c "import redis; r=redis.Redis(host='169.254.0.1', port=6379); r.ping()" 2>/dev/null; then
    echo "ERROR: Redis connection failed"
    exit 1
fi

echo "OK: All services running"
exit 0
EOF

sudo chmod +x "/home/edgecam/projects/knitting-rpi-gs/health_check.sh"

# Step 15: Create backup script
print_status "Creating backup script..."
sudo -u edgecam tee "/home/edgecam/projects/knitting-rpi-gs/backup.sh" > /dev/null <<'EOF'
#!/bin/bash
# Backup script for camera streaming system

BACKUP_FILE="/home/edgecam/backups/camera-system-$(date +%Y%m%d-%H%M%S).tar.gz"

cd "/home/edgecam/projects/knitting-rpi-gs"

# Create backup
tar -czf "$BACKUP_FILE" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='logs/*.log' \
    --exclude='images/*.jpg' \
    .

echo "Backup created: $BACKUP_FILE"

# Keep only last 5 backups
ls -t /home/edgecam/backups/camera-system-*.tar.gz | tail -n +6 | xargs rm -f
EOF

sudo chmod +x "/home/edgecam/projects/knitting-rpi-gs/backup.sh"

# Step 16: Configure crontab for monitoring
print_status "Configuring automated monitoring..."
sudo -u edgecam crontab -l 2>/dev/null | { cat; echo "*/5 * * * * /home/edgecam/projects/knitting-rpi-gs/health_check.sh > /dev/null 2>&1"; } | sudo -u edgecam crontab -
sudo -u edgecam crontab -l 2>/dev/null | { cat; echo "0 2 * * * /home/edgecam/projects/knitting-rpi-gs/backup.sh > /dev/null 2>&1"; } | sudo -u edgecam crontab -

# Step 17: Create test script
print_status "Creating test script..."
sudo -u edgecam tee "/home/edgecam/projects/knitting-rpi-gs/test_installation.sh" > /dev/null <<'EOF'
#!/bin/bash
# Test script for camera streaming system installation

echo "Testing camera streaming system installation..."

# Test 1: Check if all files exist
echo "1. Checking files..."
REQUIRED_FILES=(
    "cam1_stream.py"
    "start.py"
    "client.py"
    "config.py"
    "camera_manager.py"
    "api_server.py"
    "dashboard.html"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file (missing)"
        exit 1
    fi
done

# Test 2: Check Python syntax
echo "2. Checking Python syntax..."
source /home/edgecam/venv/bin/activate
python3 -m py_compile cam1_stream.py start.py client.py config.py camera_manager.py api_server.py
echo "   ✓ Python syntax OK"

# Test 3: Check Redis connection
echo "3. Testing Redis connection..."
if python3 -c "import redis; r=redis.Redis(host='169.254.0.1', port=6379); r.ping()" 2>/dev/null; then
    echo "   ✓ Redis connection OK"
else
    echo "   ✗ Redis connection failed"
    exit 1
fi

# Test 4: Check services
echo "4. Checking services..."
if sudo systemctl is-enabled camera-streaming.service > /dev/null; then
    echo "   ✓ Camera streaming service enabled"
else
    echo "   ✗ Camera streaming service not enabled"
fi

if sudo systemctl is-enabled camera-api.service > /dev/null; then
    echo "   ✓ API service enabled"
else
    echo "   ✗ API service not enabled"
fi

# Test 5: Check camera
echo "5. Checking camera..."
if vcgencmd get_camera | grep -q "detected=1"; then
    echo "   ✓ Camera detected"
else
    echo "   ✗ Camera not detected"
fi

echo "Installation test completed successfully!"
EOF

sudo chmod +x "/home/edgecam/projects/knitting-rpi-gs/test_installation.sh"

# Step 18: Enable services
print_status "Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable camera-streaming.service
sudo systemctl enable camera-api.service

# Step 19: Create log files
print_status "Creating log files..."
sudo -u edgecam touch /home/edgecam/logs/camera_system.log
sudo -u edgecam touch /home/edgecam/logs/errors.log
sudo -u edgecam touch /home/edgecam/logs/performance.log

# Step 20: Final configuration
print_status "Performing final configuration..."

# Set proper permissions
sudo chown -R edgecam:edgecam "/home/edgecam/projects/knitting-rpi-gs"
sudo chmod +x "/home/edgecam/projects/knitting-rpi-gs"/*.sh

print_status "Online installation completed successfully!"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Installation Summary${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "${BLUE}Project Directory:${NC} /home/edgecam/projects/knitting-rpi-gs"
echo -e "${BLUE}GitHub Repository:${NC} $GITHUB_REPO"
echo -e "${BLUE}Branch:${NC} $GITHUB_BRANCH"
echo -e "${BLUE}Virtual Environment:${NC} /home/edgecam/venv/"
echo -e "${BLUE}Dashboard URL:${NC} http://169.254.0.1:5000/dashboard.html"
echo -e "${BLUE}API Base URL:${NC} http://169.254.0.1:5000/api"
echo ""

print_status "Next steps:"
echo "1. Test the installation: cd /home/edgecam/projects/knitting-rpi-gs && ./test_installation.sh"
echo "2. Start services: sudo systemctl start camera-streaming camera-api"
echo "3. Access dashboard: http://169.254.0.1:5000/dashboard.html"
echo "4. Check system health: python3 health_check.py"

if grep -q "169.254.0.1" /etc/dhcpcd.conf; then
    print_warning "Static IP configured. Reboot required for network changes."
    print_warning "Run: sudo reboot"
fi

print_status "Online installation completed! Your camera streaming system is ready."
print_status "The system will work offline after initial setup."
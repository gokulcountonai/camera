#!/bin/bash
# Offline Package Installation Script for Pi 5
# Install required packages for camera streaming system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Pi 5 Package Installation Script${NC}"
echo -e "${BLUE}  Camera Streaming System${NC}"
echo -e "${BLUE}================================${NC}"

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
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Update package list
print_status "Updating package list..."
apt-get update

# Install required packages
print_status "Installing required packages..."

# Core system packages
apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    htop \
    vim \
    nano

# Camera and image processing packages
apt-get install -y \
    python3-picamera2 \
    python3-opencv \
    python3-numpy \
    python3-pil \
    python3-pil.imagetk

# Redis and networking packages
apt-get install -y \
    redis-server \
    python3-redis \
    python3-requests \
    python3-urllib3

# System monitoring packages
apt-get install -y \
    python3-psutil \
    python3-setuptools \
    python3-wheel

# Web server and API packages
apt-get install -y \
    python3-flask \
    python3-flask-cors \
    python3-werkzeug

# Additional utilities
apt-get install -y \
    python3-yaml \
    python3-json5 \
    python3-dateutil \
    python3-tz

# Development tools (optional)
print_warning "Install development tools? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    apt-get install -y \
        python3-dev \
        build-essential \
        cmake \
        pkg-config \
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

# Configure Redis
print_status "Configuring Redis..."
systemctl stop redis-server 2>/dev/null || true

# Create optimized Redis configuration for Pi 5
tee /etc/redis/redis.conf > /dev/null <<EOF
# Redis configuration optimized for Pi 5
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

# Performance optimizations for Pi 5
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
systemctl enable redis-server
systemctl start redis-server

# Configure system settings
print_status "Configuring system settings..."

# Enable camera interface
raspi-config nonint do_camera 0

# Set GPU memory split (256MB for camera)
raspi-config nonint do_memory_split 256

# Enable I2C
raspi-config nonint do_i2c 0

# Enable SPI if needed
print_warning "Enable SPI interface? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    raspi-config nonint do_spi 0
fi

# Configure network for static IP
print_warning "Configure static IP 169.254.0.1 for offline operation? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    tee -a /etc/dhcpcd.conf > /dev/null <<EOF

# Static IP configuration for camera streaming
interface eth0
static ip_address=169.254.0.1/24
static domain_name_servers=8.8.8.8 8.8.4.4
EOF
    print_status "Static IP configured. Reboot required for network changes."
fi

# Create service user
print_status "Creating service user..."
if ! id "edgecam" &>/dev/null; then
    useradd -m -s /bin/bash edgecam
    usermod -aG sudo edgecam
    print_status "User 'edgecam' created. Set password:"
    passwd edgecam
else
    print_status "User 'edgecam' already exists"
fi

# Create necessary directories
print_status "Creating directories..."
mkdir -p /home/edgecam/projects
mkdir -p /home/edgecam/images
mkdir -p /home/edgecam/logs
mkdir -p /home/edgecam/backups
mkdir -p /var/log/camera-streaming

# Set permissions
chown -R edgecam:edgecam /home/edgecam
chown -R edgecam:edgecam /var/log/camera-streaming

# Configure Python environment
print_status "Configuring Python environment..."
sudo -u edgecam python3 -m pip install --user --upgrade pip
sudo -u edgecam python3 -m pip install --user virtualenv

# Create virtual environment
sudo -u edgecam python3 -m venv /home/edgecam/venv
sudo -u edgecam /home/edgecam/venv/bin/pip install --upgrade pip

# Install Python packages in virtual environment
print_status "Installing Python packages in virtual environment..."
sudo -u edgecam /home/edgecam/venv/bin/pip install \
    flask \
    flask-cors \
    redis \
    psutil \
    opencv-python \
    numpy \
    pillow \
    requests \
    pyyaml \
    python-dateutil \
    pytz

# Configure logrotate
print_status "Configuring log rotation..."
tee /etc/logrotate.d/camera-streaming > /dev/null <<EOF
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

# Configure system limits
print_status "Configuring system limits..."
tee -a /etc/security/limits.conf > /dev/null <<EOF

# Camera streaming system limits
edgecam soft nofile 65536
edgecam hard nofile 65536
edgecam soft nproc 4096
edgecam hard nproc 4096
EOF

# Configure sysctl for better performance
print_status "Configuring system performance..."
tee -a /etc/sysctl.conf > /dev/null <<EOF

# Camera streaming system optimizations
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
vm.swappiness = 10
EOF

# Apply sysctl changes
sysctl -p

# Create startup script
print_status "Creating startup script..."
tee /home/edgecam/start_camera_system.sh > /dev/null <<EOF
#!/bin/bash
# Camera System Startup Script

cd /home/edgecam/projects/knitting-rpi-gs

# Activate virtual environment
source /home/edgecam/venv/bin/activate

# Start camera streaming
python3 cam1_stream.py &
CAM_PID=\$!

# Start monitoring
python3 start.py &
MONITOR_PID=\$!

# Start API server
python3 api_server.py &
API_PID=\$!

echo "Camera system started with PIDs: \$CAM_PID, \$MONITOR_PID, \$API_PID"

# Wait for processes
wait \$CAM_PID \$MONITOR_PID \$API_PID
EOF

chmod +x /home/edgecam/start_camera_system.sh
chown edgecam:edgecam /home/edgecam/start_camera_system.sh

# Create health check script
print_status "Creating health check script..."
tee /home/edgecam/health_check.sh > /dev/null <<EOF
#!/bin/bash
# Health check script

cd /home/edgecam/projects/knitting-rpi-gs

# Check if processes are running
if ! pgrep -f "cam1_stream.py" > /dev/null; then
    echo "ERROR: Camera streaming process not running"
    exit 1
fi

if ! pgrep -f "start.py" > /dev/null; then
    echo "ERROR: Monitoring process not running"
    exit 1
fi

if ! pgrep -f "api_server.py" > /dev/null; then
    echo "ERROR: API server not running"
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

chmod +x /home/edgecam/health_check.sh
chown edgecam:edgecam /home/edgecam/health_check.sh

# Configure crontab for monitoring
print_status "Configuring automated monitoring..."
sudo -u edgecam crontab -l 2>/dev/null | { cat; echo "*/5 * * * * /home/edgecam/health_check.sh > /dev/null 2>&1"; } | sudo -u edgecam crontab -

# Create test script
print_status "Creating test script..."
tee /home/edgecam/test_system.sh > /dev/null <<EOF
#!/bin/bash
# System test script

echo "Testing camera streaming system..."

# Test 1: Check Python packages
echo "1. Checking Python packages..."
cd /home/edgecam/projects/knitting-rpi-gs
source /home/edgecam/venv/bin/activate

python3 -c "import cv2; print('OpenCV version:', cv2.__version__)"
python3 -c "import redis; print('Redis package OK')"
python3 -c "import flask; print('Flask package OK')"
python3 -c "import psutil; print('psutil package OK')"

# Test 2: Check camera
echo "2. Checking camera..."
if vcgencmd get_camera | grep -q "detected=1"; then
    echo "   ✓ Camera detected"
else
    echo "   ✗ Camera not detected"
fi

# Test 3: Check Redis
echo "3. Checking Redis..."
if systemctl is-active --quiet redis-server; then
    echo "   ✓ Redis server running"
else
    echo "   ✗ Redis server not running"
fi

# Test 4: Check network
echo "4. Checking network..."
if ip addr show eth0 | grep -q "169.254.0.1"; then
    echo "   ✓ Static IP configured"
else
    echo "   ⚠ Static IP not configured"
fi

echo "System test completed!"
EOF

chmod +x /home/edgecam/test_system.sh
chown edgecam:edgecam /home/edgecam/test_system.sh

# Create README
print_status "Creating README..."
tee /home/edgecam/README_INSTALLATION.md > /dev/null <<EOF
# Pi 5 Camera Streaming System - Installation Complete

## What was installed:

### System Packages:
- Python 3 with pip and venv
- OpenCV and PiCamera2 for camera operations
- Redis server for data storage
- Flask for web API
- psutil for system monitoring
- Development tools (if selected)

### Configuration:
- Camera interface enabled
- GPU memory split set to 256MB
- I2C enabled
- Static IP 169.254.0.1 (if selected)
- Redis configured for offline operation
- Service user 'edgecam' created
- Log rotation configured
- System limits optimized

### Directories Created:
- /home/edgecam/projects/ (for your code)
- /home/edgecam/images/ (for captured images)
- /home/edgecam/logs/ (for application logs)
- /home/edgecam/backups/ (for system backups)
- /var/log/camera-streaming/ (for system logs)

## Next Steps:

1. **Copy your project files to:** /home/edgecam/projects/knitting-rpi-gs/
2. **Test the installation:** ./test_system.sh
3. **Start the system:** ./start_camera_system.sh
4. **Access dashboard:** http://169.254.0.1:5000/dashboard.html

## Useful Commands:

- **Check system health:** ./health_check.sh
- **View logs:** tail -f /home/edgecam/logs/camera_system.log
- **Check Redis:** sudo systemctl status redis-server
- **Check camera:** vcgencmd get_camera
- **Monitor system:** htop

## Troubleshooting:

- **Camera not working:** Check if camera interface is enabled
- **Redis connection failed:** Restart Redis with 'sudo systemctl restart redis-server'
- **Permission issues:** Check ownership with 'ls -la /home/edgecam/'
- **Network issues:** Reboot if static IP was configured

## Offline Operation:

This system is configured for offline operation:
- Redis bound to 169.254.0.1
- No internet dependencies
- Local dashboard and API
- Automatic recovery mechanisms
EOF

chown edgecam:edgecam /home/edgecam/README_INSTALLATION.md

print_status "Package installation completed successfully!"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Installation Summary${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "${BLUE}User:${NC} edgecam"
echo -e "${BLUE}Project Directory:${NC} /home/edgecam/projects/"
echo -e "${BLUE}Virtual Environment:${NC} /home/edgecam/venv/"
echo -e "${BLUE}Redis Configuration:${NC} /etc/redis/redis.conf"
echo -e "${BLUE}Static IP:${NC} 169.254.0.1 (if configured)"
echo ""

print_status "Next steps:"
echo "1. Switch to edgecam user: sudo su - edgecam"
echo "2. Copy your project files to: /home/edgecam/projects/knitting-rpi-gs/"
echo "3. Test installation: ./test_system.sh"
echo "4. Start system: ./start_camera_system.sh"

if grep -q "169.254.0.1" /etc/dhcpcd.conf; then
    print_warning "Static IP configured. Reboot required for network changes."
    print_warning "Run: sudo reboot"
fi

print_status "Installation completed! Your Pi 5 is ready for camera streaming."
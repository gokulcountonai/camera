#!/bin/bash
# Pi 5 Offline Installation Script for Camera Streaming System
# This script sets up the complete system without internet access

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
LOG_DIR="/var/log/camera-streaming"
BACKUP_DIR="/home/edgecam/backups"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Pi 5 Offline Installation Script${NC}"
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

# Check if we're on a Pi 5
if ! grep -q "Raspberry Pi 5" /proc/device-tree/model 2>/dev/null; then
    print_warning "This script is designed for Raspberry Pi 5. Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

print_status "Starting offline installation for Pi 5..."

# Step 1: Create necessary directories
print_status "Creating directories..."
sudo mkdir -p "$PROJECT_DIR"
sudo mkdir -p "$LOG_DIR"
sudo mkdir -p "$BACKUP_DIR"
sudo mkdir -p /home/edgecam/images
sudo mkdir -p /home/edgecam/logs

# Step 2: Set proper permissions
print_status "Setting permissions..."
sudo chown -R $SERVICE_USER:$SERVICE_GROUP "$PROJECT_DIR"
sudo chown -R $SERVICE_USER:$SERVICE_GROUP "$LOG_DIR"
sudo chown -R $SERVICE_USER:$SERVICE_GROUP "$BACKUP_DIR"
sudo chown -R $SERVICE_USER:$SERVICE_GROUP /home/edgecam/images
sudo chown -R $SERVICE_USER:$SERVICE_GROUP /home/edgecam/logs

# Step 3: Check for required packages (offline check)
print_status "Checking for required packages..."

# Check if packages are installed
PACKAGES_MISSING=()
if ! dpkg -l | grep -q "python3-picamera2"; then
    PACKAGES_MISSING+=("python3-picamera2")
fi
if ! dpkg -l | grep -q "python3-opencv"; then
    PACKAGES_MISSING+=("python3-opencv")
fi
if ! dpkg -l | grep -q "python3-redis"; then
    PACKAGES_MISSING+=("python3-redis")
fi
if ! dpkg -l | grep -q "python3-psutil"; then
    PACKAGES_MISSING+=("python3-psutil")
fi
if ! dpkg -l | grep -q "redis-server"; then
    PACKAGES_MISSING+=("redis-server")
fi
if ! dpkg -l | grep -q "python3-flask"; then
    PACKAGES_MISSING+=("python3-flask")
fi

if [ ${#PACKAGES_MISSING[@]} -ne 0 ]; then
    print_error "Missing required packages: ${PACKAGES_MISSING[*]}"
    print_error "Please install these packages before running this script:"
    echo "sudo apt-get update"
    echo "sudo apt-get install -y ${PACKAGES_MISSING[*]}"
    exit 1
fi

print_status "All required packages are installed"

# Step 4: Configure Redis for offline operation
print_status "Configuring Redis..."
sudo systemctl stop redis-server 2>/dev/null || true

# Create Redis configuration
sudo tee /etc/redis/redis.conf > /dev/null <<EOF
# Redis configuration for camera streaming system
bind 127.0.0.1 169.254.0.1
port 6379
timeout 300
tcp-keepalive 60
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
EOF

# Start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Step 5: Configure system settings
print_status "Configuring system settings..."

# Enable camera interface
sudo raspi-config nonint do_camera 0

# Set GPU memory split (256MB for camera)
sudo raspi-config nonint do_memory_split 256

# Enable I2C if needed
sudo raspi-config nonint do_i2c 0

# Configure network for static IP if needed
print_warning "Do you want to configure static IP for 169.254.0.1? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    sudo tee -a /etc/dhcpcd.conf > /dev/null <<EOF

# Static IP configuration for camera streaming
interface eth0
static ip_address=169.254.0.1/24
static domain_name_servers=8.8.8.8 8.8.4.4
EOF
    print_status "Static IP configured. Reboot required for network changes."
fi

# Step 6: Create systemd service
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/camera-streaming.service > /dev/null <<EOF
[Unit]
Description=Camera Streaming Service
After=network.target redis.service
Wants=redis.service

[Service]
Type=forking
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/run.sh
ExecStop=/bin/kill -TERM \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=camera-streaming

# Environment variables
Environment=PYTHONPATH=$PROJECT_DIR
Environment=REDIS_HOST=169.254.0.1
Environment=REDIS_PORT=6379

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$PROJECT_DIR /var/log /home/edgecam

[Install]
WantedBy=multi-user.target
EOF

# Create API service
sudo tee /etc/systemd/system/camera-api.service > /dev/null <<EOF
[Unit]
Description=Camera Streaming API Server
After=network.target redis.service camera-streaming.service
Wants=redis.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 $PROJECT_DIR/api_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=camera-api

# Environment variables
Environment=PYTHONPATH=$PROJECT_DIR
Environment=REDIS_HOST=169.254.0.1
Environment=REDIS_PORT=6379

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

# Step 7: Configure logging
print_status "Configuring logging..."
sudo tee /etc/logrotate.d/camera-streaming > /dev/null <<EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_GROUP
    postrotate
        systemctl reload camera-streaming.service > /dev/null 2>&1 || true
    endscript
}
EOF

# Step 8: Create startup script
print_status "Creating startup script..."
tee "$PROJECT_DIR/run.sh" > /dev/null <<EOF
#!/bin/bash
# Camera Streaming Startup Script

cd "$PROJECT_DIR"

# Start the main camera streaming application
python3 cam1_stream.py &
CAM_PID=\$!

# Start the monitoring system
python3 start.py &
MONITOR_PID=\$!

# Wait for processes
wait \$CAM_PID \$MONITOR_PID
EOF

chmod +x "$PROJECT_DIR/run.sh"

# Step 9: Create health check script
print_status "Creating health check script..."
tee "$PROJECT_DIR/health_check.sh" > /dev/null <<EOF
#!/bin/bash
# Health check script for camera streaming system

cd "$PROJECT_DIR"

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

chmod +x "$PROJECT_DIR/health_check.sh"

# Step 10: Create backup script
print_status "Creating backup script..."
tee "$PROJECT_DIR/backup.sh" > /dev/null <<EOF
#!/bin/bash
# Backup script for camera streaming system

BACKUP_FILE="$BACKUP_DIR/camera-system-\$(date +%Y%m%d-%H%M%S).tar.gz"

cd "$PROJECT_DIR"

# Create backup
tar -czf "\$BACKUP_FILE" \\
    --exclude='*.pyc' \\
    --exclude='__pycache__' \\
    --exclude='logs/*.log' \\
    --exclude='images/*.jpg' \\
    .

echo "Backup created: \$BACKUP_FILE"

# Keep only last 5 backups
ls -t "$BACKUP_DIR"/camera-system-*.tar.gz | tail -n +6 | xargs rm -f
EOF

chmod +x "$PROJECT_DIR/backup.sh"

# Step 11: Configure crontab for monitoring
print_status "Configuring automated monitoring..."
(crontab -l 2>/dev/null; echo "*/5 * * * * $PROJECT_DIR/health_check.sh > /dev/null 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "0 2 * * * $PROJECT_DIR/backup.sh > /dev/null 2>&1") | crontab -

# Step 12: Enable services
print_status "Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable camera-streaming.service
sudo systemctl enable camera-api.service

# Step 13: Create test script
print_status "Creating test script..."
tee "$PROJECT_DIR/test_installation.sh" > /dev/null <<EOF
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

for file in "\${REQUIRED_FILES[@]}"; do
    if [ -f "\$file" ]; then
        echo "   ✓ \$file"
    else
        echo "   ✗ \$file (missing)"
        exit 1
    fi
done

# Test 2: Check Python syntax
echo "2. Checking Python syntax..."
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

echo "Installation test completed successfully!"
EOF

chmod +x "$PROJECT_DIR/test_installation.sh"

# Step 14: Create README for Pi 5
print_status "Creating Pi 5 specific README..."
tee "$PROJECT_DIR/README_PI5.md" > /dev/null <<EOF
# Camera Streaming System - Pi 5 Installation

## Quick Start

1. **Start the system:**
   \`\`\`bash
   sudo systemctl start camera-streaming.service
   sudo systemctl start camera-api.service
   \`\`\`

2. **Access the dashboard:**
   Open your browser and go to: \`http://169.254.0.1:5000/dashboard.html\`

3. **Check system health:**
   \`\`\`bash
   python3 health_check.py
   \`\`\`

4. **Test the installation:**
   \`\`\`bash
   ./test_installation.sh
   \`\`\`

## Manual Commands

- **Start services:** \`sudo systemctl start camera-streaming camera-api\`
- **Stop services:** \`sudo systemctl stop camera-streaming camera-api\`
- **Check status:** \`sudo systemctl status camera-streaming camera-api\`
- **View logs:** \`sudo journalctl -u camera-streaming -f\`
- **Backup system:** \`./backup.sh\`
- **Health check:** \`./health_check.sh\`

## API Endpoints

- **Health:** \`http://169.254.0.1:5000/api/health\`
- **Dashboard:** \`http://169.254.0.1:5000/dashboard.html\`
- **Camera test:** \`curl -X POST http://169.254.0.1:5000/api/camera/test\`
- **Camera recover:** \`curl -X POST http://169.254.0.1:5000/api/camera/recover\`

## Troubleshooting

1. **Check if Redis is running:** \`sudo systemctl status redis-server\`
2. **Check camera interface:** \`vcgencmd get_camera\`
3. **Check system logs:** \`sudo journalctl -u camera-streaming -n 50\`
4. **Restart everything:** \`sudo systemctl restart camera-streaming camera-api redis-server\`

## Offline Operation

This system is configured for offline operation:
- Redis bound to 169.254.0.1
- No internet dependencies
- Local dashboard and API
- Automatic recovery mechanisms
EOF

# Step 15: Final configuration
print_status "Performing final configuration..."

# Set proper permissions
sudo chown -R $SERVICE_USER:$SERVICE_GROUP "$PROJECT_DIR"
sudo chmod +x "$PROJECT_DIR"/*.sh

# Create log files
touch /home/edgecam/logs/camera_system.log
touch /home/edgecam/logs/errors.log
touch /home/edgecam/logs/performance.log
sudo chown -R $SERVICE_USER:$SERVICE_GROUP /home/edgecam/logs

print_status "Installation completed successfully!"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Installation Summary${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "${BLUE}Project Directory:${NC} $PROJECT_DIR"
echo -e "${BLUE}Log Directory:${NC} $LOG_DIR"
echo -e "${BLUE}Backup Directory:${NC} $BACKUP_DIR"
echo -e "${BLUE}Dashboard URL:${NC} http://169.254.0.1:5000/dashboard.html"
echo -e "${BLUE}API Base URL:${NC} http://169.254.0.1:5000/api"
echo ""

print_status "Next steps:"
echo "1. Copy your project files to: $PROJECT_DIR"
echo "2. Run: ./test_installation.sh"
echo "3. Start services: sudo systemctl start camera-streaming camera-api"
echo "4. Access dashboard: http://169.254.0.1:5000/dashboard.html"

print_warning "If you configured static IP, reboot is required for network changes."
print_warning "After copying files, run: sudo systemctl start camera-streaming camera-api"
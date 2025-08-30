# Online Installation Guide
## Camera Streaming System - Internet-Based Setup

This guide provides step-by-step instructions for installing the camera streaming system on a Raspberry Pi 5 with internet access.

## 📋 **Prerequisites**

### **Hardware Requirements**
- Raspberry Pi 5 (4GB or 8GB recommended)
- Camera module (Pi Camera v2 or v3)
- MicroSD card (32GB+ recommended)
- Power supply (5V/3A minimum)
- Ethernet cable or WiFi connection
- Internet connection

### **Software Requirements**
- Raspberry Pi OS (Bookworm) - 64-bit recommended
- Basic Linux knowledge
- SSH access to Pi (optional but recommended)
- Git installed (will be installed by script)

## 🚀 **Quick Installation (One Command)**

### **Option 1: Direct Download and Install**
```bash
# Download and run the online installation script
curl -sSL https://raw.githubusercontent.com/lighthouseai/knitting-rpi-gs/main/install_online.sh | bash
```

### **Option 2: Download First, Then Install**
```bash
# Download the script
wget https://raw.githubusercontent.com/lighthouseai/knitting-rpi-gs/main/install_online.sh

# Make it executable
chmod +x install_online.sh

# Run the installation
./install_online.sh
```

## 📝 **Detailed Installation Process**

### **Step 1: Prepare Pi 5**

1. **Flash Raspberry Pi OS**
   ```bash
   # Download Raspberry Pi Imager
   # Flash Raspberry Pi OS Bookworm (64-bit) to microSD card
   # Enable SSH and set hostname during imaging
   ```

2. **Boot Pi 5 and connect**
   ```bash
   # Connect to Pi via SSH or directly
   ssh pi@raspberrypi.local
   # or
   ssh pi@<pi-ip-address>
   ```

3. **Verify internet connection**
   ```bash
   # Test internet connectivity
   ping -c 3 8.8.8.8
   
   # Test DNS resolution
   nslookup google.com
   ```

### **Step 2: Run Online Installation**

1. **Download the installation script**
   ```bash
   wget https://raw.githubusercontent.com/lighthouseai/knitting-rpi-gs/main/install_online.sh
   chmod +x install_online.sh
   ```

2. **Run the installation**
   ```bash
   ./install_online.sh
   ```

3. **Follow the prompts**
   - The script will ask if you want to install development tools
   - Choose whether to enable SPI interface
   - Decide if you want to configure static IP (recommended for offline operation)

### **Step 3: What the Script Does**

The online installation script performs the following steps automatically:

1. **System Updates**
   - Updates package list
   - Upgrades existing packages

2. **Package Installation**
   - Installs Python 3 and pip
   - Installs OpenCV and PiCamera2
   - Installs Redis server
   - Installs Flask and web components
   - Installs system monitoring tools

3. **System Configuration**
   - Enables camera interface
   - Sets GPU memory split to 256MB
   - Enables I2C interface
   - Configures Redis for offline operation
   - Sets up static IP (if selected)

4. **User and Directory Setup**
   - Creates service user 'edgecam'
   - Creates necessary directories
   - Sets proper permissions

5. **Project Deployment**
   - Clones the GitHub repository
   - Switches to the correct branch
   - Downloads all project files

6. **Python Environment**
   - Creates virtual environment
   - Installs all Python dependencies
   - Configures Python paths

7. **Service Configuration**
   - Creates systemd services
   - Enables automatic startup
   - Configures logging

8. **Monitoring Setup**
   - Creates health check scripts
   - Sets up automated monitoring
   - Configures backup system

### **Step 4: Verification**

1. **Test the installation**
   ```bash
   # Switch to edgecam user
   sudo su - edgecam
   
   # Test the installation
   cd /home/edgecam/projects/knitting-rpi-gs
   ./test_installation.sh
   ```

2. **Check system status**
   ```bash
   # Check all services
   sudo systemctl status camera-streaming camera-api redis-server
   
   # Check camera interface
   vcgencmd get_camera
   
   # Check network configuration
   ip addr show eth0
   ```

### **Step 5: Start the System**

1. **Start services**
   ```bash
   # Start camera streaming service
   sudo systemctl start camera-streaming.service
   
   # Start API server
   sudo systemctl start camera-api.service
   
   # Check status
   sudo systemctl status camera-streaming camera-api
   ```

2. **Access the dashboard**
   ```bash
   # Open browser and go to:
   http://169.254.0.1:5000/dashboard.html
   ```

## 🔧 **Configuration Details**

### **Network Configuration**
```bash
# Static IP configuration (if selected)
interface eth0
static ip_address=169.254.0.1/24
static domain_name_servers=8.8.8.8 8.8.4.4
```

### **Redis Configuration**
```bash
# Redis is configured for offline operation
bind 127.0.0.1 169.254.0.1
port 6379
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### **Python Virtual Environment**
```bash
# Virtual environment location
/home/edgecam/venv/

# Activate virtual environment
source /home/edgecam/venv/bin/activate

# Install additional packages (if needed)
pip install package_name
```

## 📊 **Verification Steps**

### **1. Check System Status**
```bash
# Check all services
sudo systemctl status camera-streaming camera-api redis-server

# Check camera interface
vcgencmd get_camera

# Check network
ip addr show eth0
```

### **2. Test API Endpoints**
```bash
# Test health endpoint
curl http://169.254.0.1:5000/api/health

# Test camera status
curl http://169.254.0.1:5000/api/camera/status

# Test camera functionality
curl -X POST http://169.254.0.1:5000/api/camera/test
```

### **3. Access Dashboard**
- Open browser: `http://169.254.0.1:5000/dashboard.html`
- Check all status indicators are green
- Test interactive controls

## 🛠️ **Maintenance Commands**

### **Daily Operations**
```bash
# Check system health
sudo su - edgecam
./health_check.sh

# View logs
tail -f /home/edgecam/logs/camera_system.log
sudo journalctl -u camera-streaming -f

# Monitor system
htop
```

### **Service Management**
```bash
# Start services
sudo systemctl start camera-streaming camera-api

# Stop services
sudo systemctl stop camera-streaming camera-api

# Restart services
sudo systemctl restart camera-streaming camera-api

# Check status
sudo systemctl status camera-streaming camera-api
```

### **Update System**
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
sudo su - edgecam
source /home/edgecam/venv/bin/activate
pip install --upgrade -r /home/edgecam/projects/knitting-rpi-gs/requirements.txt

# Update project files
cd /home/edgecam/projects/knitting-rpi-gs
git pull origin 2.4.2/greencam1
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Internet connection failed**
   ```bash
   # Check network connectivity
   ping -c 3 8.8.8.8
   
   # Check DNS
   nslookup github.com
   
   # Restart networking
   sudo systemctl restart networking
   ```

2. **Git clone failed**
   ```bash
   # Check if git is installed
   git --version
   
   # Install git if needed
   sudo apt install git
   
   # Try cloning again
   cd /home/edgecam/projects
   sudo -u edgecam git clone https://github.com/lighthouseai/knitting-rpi-gs
   ```

3. **Python package installation failed**
   ```bash
   # Check pip
   pip --version
   
   # Upgrade pip
   sudo -u edgecam python3 -m pip install --user --upgrade pip
   
   # Try installing packages again
   sudo -u edgecam /home/edgecam/venv/bin/pip install -r requirements.txt
   ```

4. **Camera not detected**
   ```bash
   # Check camera interface
   vcgencmd get_camera
   
   # Enable camera interface
   sudo raspi-config nonint do_camera 0
   sudo reboot
   ```

5. **Redis connection failed**
   ```bash
   # Check Redis status
   sudo systemctl status redis-server
   
   # Restart Redis
   sudo systemctl restart redis-server
   
   # Check Redis configuration
   sudo cat /etc/redis/redis.conf
   ```

### **Log Analysis**
```bash
# View recent errors
sudo journalctl -u camera-streaming --since "1 hour ago" | grep ERROR

# Check application logs
tail -f /home/edgecam/logs/camera_system.log
tail -f /home/edgecam/logs/errors.log

# Analyze logs
cd /home/edgecam/projects/knitting-rpi-gs
python3 log_analyzer.py --recent-errors --hours 1
```

## 🔒 **Security Considerations**

### **Network Security**
- System configured for offline operation after setup
- Redis bound to local interfaces only
- No external internet dependencies after installation
- Static IP prevents DHCP conflicts

### **Service Security**
- Services run as non-root user (edgecam)
- Limited file system access
- Resource limits configured
- Log rotation prevents disk space issues

### **Access Control**
- Dashboard accessible only on local network
- API endpoints for local use only
- No external authentication required for offline operation

## 📈 **Performance Optimization**

### **Pi 5 Specific Optimizations**
- GPU memory split: 256MB for camera
- CPU governor: performance mode
- Network buffer optimization
- Redis memory limits: 256MB

### **Monitoring and Alerts**
- Automated health checks every 5 minutes
- Daily backup at 2 AM
- Log rotation prevents disk space issues
- Performance metrics collection

## 🎯 **Success Criteria**

### **Installation Complete When:**
- ✅ All services start without errors
- ✅ Dashboard accessible at `http://169.254.0.1:5000/dashboard.html`
- ✅ Camera test successful via API
- ✅ Redis connection working
- ✅ Health check script passes
- ✅ Log files being created
- ✅ Backup script working

### **System Ready When:**
- ✅ Camera streaming operational
- ✅ API endpoints responding
- ✅ Dashboard showing green status
- ✅ Monitoring active
- ✅ Recovery mechanisms working

## 📞 **Support**

### **If Installation Fails:**
1. Check the troubleshooting section above
2. Review logs: `sudo journalctl -u camera-streaming -n 100`
3. Run test script: `./test_installation.sh`
4. Check system requirements and prerequisites

### **For Additional Help:**
- Review the complete system documentation
- Check the troubleshooting guides
- Verify all prerequisites are met
- Ensure Pi 5 compatibility

## 🔄 **Offline Operation After Installation**

Once the online installation is complete, the system is configured for offline operation:

- **No Internet Required** - All components installed locally
- **Static IP** - 169.254.0.1 for consistent access
- **Local Dashboard** - Web interface accessible on local network
- **Automatic Recovery** - Self-healing without external dependencies

---

**Your camera streaming system is now ready for production!** 🎉

The online installation provides a complete, production-ready system that works offline after initial setup.
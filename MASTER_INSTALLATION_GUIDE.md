# Master Installation Guide
## Camera Streaming System - Complete Setup Guide

This comprehensive guide covers both online and offline installation methods for the camera streaming system on Raspberry Pi 5.

## 📋 **Quick Start Options**

### **Option 1: Online Installation (Recommended)**
```bash
# One-command installation with internet
curl -sSL https://raw.githubusercontent.com/lighthouseai/knitting-rpi-gs/main/install_online.sh | bash
```

### **Option 2: Offline Installation**
```bash
# Download and run offline installer
wget https://raw.githubusercontent.com/lighthouseai/knitting-rpi-gs/main/install_pi5_offline.sh
chmod +x install_pi5_offline.sh
./install_pi5_offline.sh
```

### **Option 3: Package Installation Only**
```bash
# Install packages first, then configure
wget https://raw.githubusercontent.com/lighthouseai/knitting-rpi-gs/main/install_packages_offline.sh
chmod +x install_packages_offline.sh
sudo ./install_packages_offline.sh
```

## 🎯 **Installation Method Comparison**

| Feature | Online Installation | Offline Installation | Package Only |
|---------|-------------------|---------------------|--------------|
| **Internet Required** | ✅ Yes (initial) | ❌ No | ❌ No |
| **Speed** | ⚡ Fast | 🐌 Slower | 🐌 Slower |
| **Ease of Use** | 🌟 Easiest | ⭐ Easy | ⭐ Easy |
| **Complete Setup** | ✅ Full | ✅ Full | ⚠️ Partial |
| **GitHub Integration** | ✅ Auto | ❌ Manual | ❌ Manual |
| **Python Dependencies** | ✅ Auto | ❌ Manual | ❌ Manual |
| **Production Ready** | ✅ Yes | ✅ Yes | ⚠️ Needs config |

## 🚀 **Detailed Installation Methods**

### **Method 1: Online Installation (Recommended)**

**Best for:** First-time setup, development, or when internet is available.

**Advantages:**
- ✅ Automatic download of all project files
- ✅ Automatic installation of Python dependencies
- ✅ Complete setup in one command
- ✅ Latest version from GitHub
- ✅ Minimal manual intervention

**Steps:**
```bash
# 1. Prepare Pi 5 with internet connection
ssh pi@raspberrypi.local

# 2. Run online installation
curl -sSL https://raw.githubusercontent.com/lighthouseai/knitting-rpi-gs/main/install_online.sh | bash

# 3. Follow prompts and wait for completion
# 4. Test installation
sudo su - edgecam
cd /home/edgecam/projects/knitting-rpi-gs
./test_installation.sh

# 5. Start services
sudo systemctl start camera-streaming camera-api

# 6. Access dashboard
# Open browser: http://169.254.0.1:5000/dashboard.html
```

**What it installs:**
- All system packages (Python, OpenCV, Redis, Flask)
- Project files from GitHub
- Python virtual environment with dependencies
- Systemd services
- Monitoring and backup scripts
- Complete configuration

### **Method 2: Offline Installation**

**Best for:** Production deployment, air-gapped systems, or when internet is not available.

**Advantages:**
- ✅ Works without internet
- ✅ Secure for production environments
- ✅ Complete offline operation
- ✅ No external dependencies after setup

**Steps:**
```bash
# 1. Download installer (on a machine with internet)
wget https://raw.githubusercontent.com/lighthouseai/knitting-rpi-gs/main/install_pi5_offline.sh

# 2. Transfer to Pi 5 (USB, SCP, etc.)
scp install_pi5_offline.sh pi@raspberrypi.local:~/

# 3. Run offline installation
chmod +x install_pi5_offline.sh
./install_pi5_offline.sh

# 4. Copy project files manually
sudo cp -r /path/to/project/* /home/edgecam/projects/knitting-rpi-gs/

# 5. Test and start
sudo su - edgecam
cd /home/edgecam/projects/knitting-rpi-gs
./test_installation.sh
sudo systemctl start camera-streaming camera-api
```

**What it installs:**
- System packages (if available)
- System configuration
- Service setup
- Monitoring scripts
- Directory structure

### **Method 3: Package Installation Only**

**Best for:** When you want to install packages separately from configuration.

**Advantages:**
- ✅ Flexible installation process
- ✅ Can be done offline
- ✅ Step-by-step control

**Steps:**
```bash
# 1. Install packages
wget https://raw.githubusercontent.com/lighthouseai/knitting-rpi-gs/main/install_packages_offline.sh
chmod +x install_packages_offline.sh
sudo ./install_packages_offline.sh

# 2. Configure system manually or use offline installer
./install_pi5_offline.sh

# 3. Deploy project files
sudo cp -r /path/to/project/* /home/edgecam/projects/knitting-rpi-gs/

# 4. Test and start
sudo su - edgecam
cd /home/edgecam/projects/knitting-rpi-gs
./test_installation.sh
sudo systemctl start camera-streaming camera-api
```

## 🔧 **Prerequisites for All Methods**

### **Hardware Requirements**
- Raspberry Pi 5 (4GB or 8GB recommended)
- Camera module (Pi Camera v2 or v3)
- MicroSD card (32GB+ recommended)
- Power supply (5V/3A minimum)
- Ethernet cable or WiFi connection

### **Software Requirements**
- Raspberry Pi OS (Bookworm) - 64-bit recommended
- Basic Linux knowledge
- SSH access to Pi (optional but recommended)

### **Network Requirements**
- **Online Installation:** Internet connection required
- **Offline Installation:** No internet required
- **Package Installation:** Internet for initial package download

## 📊 **Installation Verification**

### **Quick Verification**
```bash
# Check all services
sudo systemctl status camera-streaming camera-api redis-server

# Check camera
vcgencmd get_camera

# Test API
curl http://169.254.0.1:5000/api/health

# Access dashboard
# Open: http://169.254.0.1:5000/dashboard.html
```

### **Comprehensive Testing**
```bash
# Run full test suite
sudo su - edgecam
cd /home/edgecam/projects/knitting-rpi-gs
./test_installation.sh

# Check system health
python3 health_check.py

# Test camera functionality
python3 camera_health_monitor.py --test
```

## 🛠️ **Post-Installation Configuration**

### **Network Configuration**
```bash
# Check current network
ip addr show eth0

# Configure static IP (if not done during installation)
sudo tee -a /etc/dhcpcd.conf > /dev/null <<EOF
interface eth0
static ip_address=169.254.0.1/24
static domain_name_servers=8.8.8.8 8.8.4.4
EOF

# Reboot for network changes
sudo reboot
```

### **Service Management**
```bash
# Enable services to start on boot
sudo systemctl enable camera-streaming camera-api redis-server

# Start services
sudo systemctl start camera-streaming camera-api

# Check status
sudo systemctl status camera-streaming camera-api
```

### **Monitoring Setup**
```bash
# Check automated monitoring
sudo su - edgecam
crontab -l

# Manual health check
./health_check.sh

# View logs
tail -f /home/edgecam/logs/camera_system.log
```

## 🚨 **Troubleshooting by Installation Method**

### **Online Installation Issues**

1. **Internet connection failed**
   ```bash
   # Check connectivity
   ping -c 3 8.8.8.8
   
   # Check DNS
   nslookup github.com
   
   # Restart networking
   sudo systemctl restart networking
   ```

2. **Git clone failed**
   ```bash
   # Check git installation
   git --version
   
   # Install git if needed
   sudo apt install git
   
   # Try manual clone
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

### **Offline Installation Issues**

1. **Missing packages**
   ```bash
   # Check installed packages
   dpkg -l | grep python3-picamera2
   
   # Install missing packages manually
   sudo apt install python3-picamera2 python3-opencv redis-server
   ```

2. **Project files missing**
   ```bash
   # Check project directory
   ls -la /home/edgecam/projects/knitting-rpi-gs/
   
   # Copy files manually
   sudo cp -r /path/to/project/* /home/edgecam/projects/knitting-rpi-gs/
   sudo chown -R edgecam:edgecam /home/edgecam/projects/knitting-rpi-gs/
   ```

3. **Python dependencies missing**
   ```bash
   # Check virtual environment
   source /home/edgecam/venv/bin/activate
   pip list
   
   # Install dependencies manually
   pip install flask redis psutil opencv-python numpy pillow
   ```

### **Package Installation Issues**

1. **Package installation failed**
   ```bash
   # Update package list
   sudo apt update
   
   # Install packages individually
   sudo apt install python3-picamera2
   sudo apt install python3-opencv
   sudo apt install redis-server
   ```

2. **Configuration not applied**
   ```bash
   # Run configuration script
   ./install_pi5_offline.sh
   
   # Or configure manually
   sudo raspi-config nonint do_camera 0
   sudo raspi-config nonint do_memory_split 256
   ```

## 📈 **Performance Optimization**

### **Pi 5 Specific Settings**
```bash
# GPU memory split (already set by installers)
sudo raspi-config nonint do_memory_split 256

# CPU governor
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Network optimization
echo 'net.core.rmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### **Redis Optimization**
```bash
# Check Redis configuration
sudo cat /etc/redis/redis.conf | grep maxmemory

# Optimize for Pi 5
sudo tee -a /etc/redis/redis.conf > /dev/null <<EOF
maxmemory 256mb
maxmemory-policy allkeys-lru
EOF

# Restart Redis
sudo systemctl restart redis-server
```

## 🔒 **Security Considerations**

### **Network Security**
- System configured for offline operation
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

## 📞 **Support and Next Steps**

### **If Installation Fails:**
1. Check the troubleshooting section for your installation method
2. Review logs: `sudo journalctl -u camera-streaming -n 100`
3. Run test script: `./test_installation.sh`
4. Check system requirements and prerequisites

### **After Successful Installation:**
1. **Access the dashboard:** http://169.254.0.1:5000/dashboard.html
2. **Monitor system health:** Use the built-in monitoring tools
3. **Configure alerts:** Set up email or webhook notifications
4. **Regular maintenance:** Run backups and updates as needed

### **For Additional Help:**
- Review the complete system documentation
- Check the troubleshooting guides
- Verify all prerequisites are met
- Ensure Pi 5 compatibility

---

**Choose the installation method that best fits your environment and requirements!** 🎉

- **Online Installation:** Best for development and first-time setup
- **Offline Installation:** Best for production and air-gapped systems
- **Package Installation:** Best for custom deployment scenarios
# Pi 5 Offline Installation Guide
## Camera Streaming System

This guide provides step-by-step instructions for installing the camera streaming system on a Raspberry Pi 5 without internet access.

## 📋 **Prerequisites**

### **Hardware Requirements**
- Raspberry Pi 5 (4GB or 8GB recommended)
- Camera module (Pi Camera v2 or v3)
- MicroSD card (32GB+ recommended)
- Power supply (5V/3A minimum)
- Ethernet cable (for network connection)

### **Software Requirements**
- Raspberry Pi OS (Bookworm) - 64-bit recommended
- Basic Linux knowledge
- SSH access to Pi (optional but recommended)

## 🚀 **Installation Process**

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

3. **Update system (if internet available)**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo reboot
   ```

### **Step 2: Install Required Packages**

**Option A: With Internet (Recommended for first-time setup)**
```bash
# Download and run package installation script
wget https://raw.githubusercontent.com/your-repo/install_packages_offline.sh
chmod +x install_packages_offline.sh
sudo ./install_packages_offline.sh
```

**Option B: Offline Installation**
```bash
# If you have the packages downloaded or on USB
# Copy packages to Pi and install manually
sudo dpkg -i *.deb
```

### **Step 3: Configure System**

1. **Run the offline installation script**
   ```bash
   # Download and run the main installation script
   wget https://raw.githubusercontent.com/your-repo/install_pi5_offline.sh
   chmod +x install_pi5_offline.sh
   ./install_pi5_offline.sh
   ```

2. **Follow the prompts**
   - Configure static IP (recommended: 169.254.0.1)
   - Set up service user (edgecam)
   - Configure Redis for offline operation

### **Step 4: Deploy Application Files**

1. **Copy project files**
   ```bash
   # Create project directory
   sudo mkdir -p /home/edgecam/projects/knitting-rpi-gs
   sudo chown edgecam:edgecam /home/edgecam/projects/knitting-rpi-gs
   
   # Copy your project files (via USB, SCP, or other method)
   sudo cp -r /path/to/your/project/* /home/edgecam/projects/knitting-rpi-gs/
   sudo chown -R edgecam:edgecam /home/edgecam/projects/knitting-rpi-gs/
   ```

2. **Test the installation**
   ```bash
   # Switch to edgecam user
   sudo su - edgecam
   
   # Test the installation
   cd /home/edgecam/projects/knitting-rpi-gs
   ./test_installation.sh
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

### **System Services**
```bash
# Camera streaming service
sudo systemctl enable camera-streaming.service
sudo systemctl start camera-streaming.service

# API server service
sudo systemctl enable camera-api.service
sudo systemctl start camera-api.service

# Redis service
sudo systemctl enable redis-server
sudo systemctl start redis-server
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

### **Backup and Recovery**
```bash
# Create backup
sudo su - edgecam
./backup.sh

# List backups
ls -la /home/edgecam/backups/

# Restore from backup (if needed)
tar -xzf /home/edgecam/backups/camera-system-YYYYMMDD-HHMMSS.tar.gz
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Camera not detected**
   ```bash
   # Check camera interface
   vcgencmd get_camera
   
   # Enable camera interface
   sudo raspi-config nonint do_camera 0
   sudo reboot
   ```

2. **Redis connection failed**
   ```bash
   # Check Redis status
   sudo systemctl status redis-server
   
   # Restart Redis
   sudo systemctl restart redis-server
   
   # Check Redis configuration
   sudo cat /etc/redis/redis.conf
   ```

3. **Permission issues**
   ```bash
   # Check ownership
   ls -la /home/edgecam/
   
   # Fix permissions
   sudo chown -R edgecam:edgecam /home/edgecam/
   ```

4. **Network issues**
   ```bash
   # Check network configuration
   ip addr show eth0
   
   # Test connectivity
   ping 169.254.0.1
   
   # Restart networking
   sudo systemctl restart networking
   ```

5. **Service won't start**
   ```bash
   # Check service logs
   sudo journalctl -u camera-streaming -n 50
   sudo journalctl -u camera-api -n 50
   
   # Check dependencies
   sudo systemctl list-dependencies camera-streaming
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
- System configured for offline operation
- Redis bound to local interfaces only
- No external internet dependencies
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

---

**Your Pi 5 camera streaming system is now ready for offline operation!** 🎉

The system will automatically handle camera issues, provide real-time monitoring, and maintain high availability without internet access.
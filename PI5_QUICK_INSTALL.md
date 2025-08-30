# Pi 5 Quick Installation Guide
## Camera Streaming System - Offline Deployment

## 🚀 **Quick Start (5 Steps)**

### **1. Prepare Pi 5**
```bash
# Flash Raspberry Pi OS Bookworm (64-bit)
# Enable SSH during imaging
# Boot and connect via SSH
ssh pi@raspberrypi.local
```

### **2. Install Packages (With Internet)**
```bash
# Download and run package installer
wget https://raw.githubusercontent.com/your-repo/install_packages_offline.sh
chmod +x install_packages_offline.sh
sudo ./install_packages_offline.sh
```

### **3. Configure System**
```bash
# Download and run main installer
wget https://raw.githubusercontent.com/your-repo/install_pi5_offline.sh
chmod +x install_pi5_offline.sh
./install_pi5_offline.sh
```

### **4. Deploy Files**
```bash
# Copy your project files
sudo cp -r /path/to/project/* /home/edgecam/projects/knitting-rpi-gs/
sudo chown -R edgecam:edgecam /home/edgecam/projects/knitting-rpi-gs/

# Test installation
sudo su - edgecam
cd /home/edgecam/projects/knitting-rpi-gs
./test_installation.sh
```

### **5. Start System**
```bash
# Start services
sudo systemctl start camera-streaming camera-api

# Access dashboard
# Open browser: http://169.254.0.1:5000/dashboard.html
```

## 📋 **Prerequisites Checklist**

- [ ] Raspberry Pi 5 (4GB+ RAM)
- [ ] Camera module connected
- [ ] MicroSD card (32GB+)
- [ ] Power supply (5V/3A)
- [ ] Ethernet cable
- [ ] Raspberry Pi OS Bookworm flashed
- [ ] SSH access configured

## 🔧 **Key Commands**

### **Service Management**
```bash
# Start/Stop/Restart
sudo systemctl start|stop|restart camera-streaming camera-api

# Check status
sudo systemctl status camera-streaming camera-api

# View logs
sudo journalctl -u camera-streaming -f
```

### **Health Checks**
```bash
# Quick health check
sudo su - edgecam
./health_check.sh

# Detailed health check
python3 health_check.py

# Test camera
python3 camera_health_monitor.py --test
```

### **API Testing**
```bash
# Test health
curl http://169.254.0.1:5000/api/health

# Test camera
curl -X POST http://169.254.0.1:5000/api/camera/test

# Recover camera
curl -X POST http://169.254.0.1:5000/api/camera/recover
```

## 🌐 **Access Points**

- **Dashboard:** http://169.254.0.1:5000/dashboard.html
- **API Base:** http://169.254.0.1:5000/api
- **Health Check:** http://169.254.0.1:5000/api/health
- **Camera Status:** http://169.254.0.1:5000/api/camera/status

## 🚨 **Quick Troubleshooting**

### **Camera Issues**
```bash
# Check camera
vcgencmd get_camera

# Enable camera interface
sudo raspi-config nonint do_camera 0
sudo reboot
```

### **Redis Issues**
```bash
# Check Redis
sudo systemctl status redis-server

# Restart Redis
sudo systemctl restart redis-server
```

### **Network Issues**
```bash
# Check IP
ip addr show eth0

# Test connectivity
ping 169.254.0.1
```

### **Service Issues**
```bash
# Check all services
sudo systemctl status camera-streaming camera-api redis-server

# View recent logs
sudo journalctl -u camera-streaming --since "10 minutes ago"
```

## 📊 **Verification Checklist**

- [ ] All services running: `sudo systemctl status camera-streaming camera-api`
- [ ] Camera detected: `vcgencmd get_camera`
- [ ] Redis connected: `redis-cli ping`
- [ ] Dashboard accessible: http://169.254.0.1:5000/dashboard.html
- [ ] API responding: `curl http://169.254.0.1:5000/api/health`
- [ ] Camera test working: `curl -X POST http://169.254.0.1:5000/api/camera/test`
- [ ] Health check passing: `./health_check.sh`

## 🎯 **Success Indicators**

✅ **Green Status** - All systems operational
✅ **Camera Capturing** - Frame capture working
✅ **API Responding** - All endpoints accessible
✅ **Dashboard Loading** - Web interface functional
✅ **Logs Clean** - No critical errors
✅ **Recovery Working** - Automatic recovery functional

## 📞 **Emergency Commands**

```bash
# Emergency restart
sudo systemctl restart camera-streaming camera-api redis-server

# Force camera recovery
curl -X POST http://169.254.0.1:5000/api/camera/recover

# Check system health
python3 health_check.py --json

# View recent errors
python3 log_analyzer.py --recent-errors --hours 1
```

## 🔒 **Offline Operation**

- **No Internet Required** - System works completely offline
- **Static IP** - 169.254.0.1 for consistent access
- **Local Dashboard** - Web interface accessible on local network
- **Automatic Recovery** - Self-healing without external dependencies

---

**Your Pi 5 camera streaming system is ready for production!** 🎉

For detailed documentation, see `PI5_INSTALLATION_GUIDE.md`
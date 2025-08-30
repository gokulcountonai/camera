# API Server & Production Safeguards System

## 🎯 **Overview**

This comprehensive monitoring and management system provides:

1. **Real-time API Server** - RESTful API for system monitoring and control
2. **Web Dashboard** - Beautiful, responsive web interface
3. **Production Safeguards** - Advanced safety measures and early warning systems
4. **Automated Issue Detection** - Proactive problem identification and resolution

## 🚀 **API Server Features**

### **Real-time Health Monitoring**
- System resources (CPU, memory, disk, temperature)
- Camera status and health metrics
- Redis connection monitoring
- Process status tracking
- Network connectivity checks
- Performance metrics collection

### **Comprehensive Data Collection**
- Health history (last 1000 records)
- Alert management
- Log analysis
- Performance trends
- System information

### **RESTful API Endpoints**

#### **Health & Status Endpoints**
```bash
# Get comprehensive health data
GET /api/health

# Get health summary for dashboard
GET /api/health/summary

# Get camera status
GET /api/camera/status

# Get recent alerts
GET /api/alerts

# Get recent logs
GET /api/logs/recent?type=errors&limit=50

# Get performance metrics
GET /api/metrics/performance

# Get health history
GET /api/metrics/history?hours=24

# Get complete dashboard data
GET /api/dashboard
```

#### **Control Endpoints**
```bash
# Test camera functionality
POST /api/camera/test

# Attempt camera recovery
POST /api/camera/recover

# Restart services
POST /api/system/restart-services

# Trigger system reboot
POST /api/system/reboot
```

#### **Status Endpoints**
```bash
# Get API server status
GET /api/status
```

## 🖥️ **Web Dashboard**

### **Features**
- **Real-time Monitoring** - Auto-refresh every 30 seconds
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Interactive Charts** - Performance metrics visualization
- **Status Indicators** - Color-coded health status
- **Control Buttons** - Direct system control from dashboard
- **Alert Management** - Real-time alert display

### **Dashboard Sections**
1. **System Resources** - CPU, memory, disk usage
2. **Camera Status** - Health score, failures, frame metrics
3. **Redis Status** - Connection status and performance
4. **Process Status** - Running/stopped process indicators
5. **Performance Chart** - CPU and memory trends
6. **Recent Alerts** - Latest system alerts
7. **System Information** - Hostname, uptime, temperature
8. **Recent Logs** - Latest log entries

### **Access Dashboard**
```bash
# Start API server
python3 api_server.py

# Access dashboard in browser
http://your-pi-ip:5000/dashboard.html
```

## 🛡️ **Production Safeguards**

### **Automatic Monitoring**
The production safeguards system continuously monitors:

#### **Resource Monitoring**
- **CPU Usage** - Warning at 85%, critical at 95%
- **Memory Usage** - Warning at 90%, critical at 95%
- **Disk Usage** - Warning at 90%, critical at 95%
- **Temperature** - Warning at 70°C, critical at 80°C

#### **Camera Safety Monitoring**
- **Consecutive Failures** - Warning at 5, critical at 10
- **Frame Capture Timeouts** - Detects stuck camera
- **Health Score Tracking** - Monitors camera performance

#### **Redis Health Monitoring**
- **Connection Status** - Detects disconnections
- **Response Time** - Monitors performance
- **Automatic Recovery** - Attempts reconnection

#### **Process Watchdog**
- **Critical Process Monitoring** - `cam1_stream.py`, `start.py`
- **Automatic Restart** - Restarts dead processes
- **Failure Tracking** - Counts restart attempts

### **Emergency Actions**

#### **Emergency Mode Activation**
When critical conditions are detected:
- Reduces system load
- Kills non-critical processes
- Clears memory caches
- Activates resource conservation

#### **Emergency Recovery Actions**
- **CPU/Memory Critical** → Emergency mode activation
- **Disk Critical** → Aggressive cleanup
- **Camera Critical** → Force recovery or reboot
- **Redis Disconnected** → Service restart
- **Process Dead** → Service restart

#### **System Reboot (Last Resort)**
- Triggered when all recovery attempts fail
- Uses kill file mechanism
- Logs critical events before reboot

### **Automatic Cleanup**
- **Log Rotation** - Prevents disk space issues
- **Image Cleanup** - Removes old images
- **Temp File Cleanup** - Clears temporary files
- **Cache Clearing** - Frees memory

## 📊 **Usage Examples**

### **Start the Complete System**
```bash
# Start API server with production safeguards
python3 api_server.py &

# Access dashboard
open http://your-pi-ip:5000/dashboard.html

# Monitor via command line
curl http://your-pi-ip:5000/api/health/summary
```

### **API Usage Examples**

#### **Check System Health**
```bash
# Get comprehensive health data
curl http://your-pi-ip:5000/api/health | jq '.'

# Get health summary
curl http://your-pi-ip:5000/api/health/summary | jq '.'

# Check camera status
curl http://your-pi-ip:5000/api/camera/status | jq '.'
```

#### **Control System**
```bash
# Test camera
curl -X POST http://your-pi-ip:5000/api/camera/test

# Recover camera
curl -X POST http://your-pi-ip:5000/api/camera/recover

# Restart services
curl -X POST http://your-pi-ip:5000/api/system/restart-services

# Reboot system (use with caution)
curl -X POST http://your-pi-ip:5000/api/system/reboot
```

#### **Monitor Logs**
```bash
# Get recent errors
curl "http://your-pi-ip:5000/api/logs/recent?type=errors&limit=10"

# Get camera issues
curl "http://your-pi-ip:5000/api/logs/recent?type=camera&limit=20"

# Get all recent logs
curl "http://your-pi-ip:5000/api/logs/recent?limit=50"
```

### **Dashboard Features**

#### **Real-time Monitoring**
- Auto-refresh every 30 seconds
- Color-coded status indicators
- Performance charts
- Alert notifications

#### **Interactive Controls**
- Test camera functionality
- Trigger camera recovery
- Restart services
- View detailed metrics

#### **Alert Management**
- Real-time alert display
- Severity-based color coding
- Timestamp tracking
- Action history

## 🔧 **Configuration**

### **API Server Configuration**
```python
# In config.py
API_SERVER_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': False,
    'threaded': True,
    'health_collection_interval': 30,  # seconds
    'max_health_history': 1000,
    'max_alert_history': 500
}
```

### **Production Safeguards Configuration**
```python
# Safety thresholds
SAFEGUARD_THRESHOLDS = {
    'cpu_critical': 95,
    'cpu_warning': 85,
    'memory_critical': 95,
    'memory_warning': 90,
    'disk_critical': 95,
    'disk_warning': 90,
    'temperature_critical': 80,
    'temperature_warning': 70,
    'camera_failures_critical': 10,
    'camera_failures_warning': 5,
    'process_restart_threshold': 3,
    'emergency_cleanup_interval': 3600
}
```

## 🚨 **Alert System**

### **Alert Types**
- **Warning** - Non-critical issues requiring attention
- **Critical** - Serious issues requiring immediate action
- **Emergency** - System-threatening issues

### **Alert Categories**
- **Resource Alerts** - CPU, memory, disk, temperature
- **Camera Alerts** - Failures, stuck camera, health issues
- **Redis Alerts** - Connection issues, performance problems
- **Process Alerts** - Dead processes, restart failures
- **System Alerts** - General system issues

### **Alert Actions**
- **Logging** - All alerts are logged with timestamps
- **Dashboard Display** - Real-time alert display
- **API Access** - Programmatic alert access
- **Notification** - Future: email, SMS, webhook support

## 📈 **Performance Benefits**

### **Proactive Issue Detection**
- **Real-time Monitoring** - Issues detected within 30 seconds
- **Early Warning System** - Warnings before critical conditions
- **Trend Analysis** - Performance pattern recognition
- **Predictive Maintenance** - Identify issues before they occur

### **Automated Recovery**
- **Self-healing System** - Automatic issue resolution
- **Progressive Recovery** - Multiple recovery strategies
- **Graceful Degradation** - Maintain functionality during issues
- **Emergency Safeguards** - Prevent system failure

### **Operational Benefits**
- **Zero Downtime** - Continuous operation with automatic recovery
- **Reduced Manual Intervention** - Automated problem resolution
- **Comprehensive Monitoring** - Complete system visibility
- **Easy Troubleshooting** - Detailed logs and metrics

## 🔒 **Security Considerations**

### **API Security**
- **CORS Enabled** - Cross-origin requests supported
- **Error Handling** - Secure error responses
- **Input Validation** - Request parameter validation
- **Rate Limiting** - Future: implement rate limiting

### **Production Security**
- **Process Isolation** - Isolated monitoring processes
- **Resource Limits** - Prevent resource exhaustion
- **Emergency Controls** - Safe emergency actions
- **Audit Logging** - Complete action logging

## 🚀 **Deployment**

### **Installation**
```bash
# Install dependencies
pip3 install flask flask-cors psutil redis

# Start API server
python3 api_server.py

# Access dashboard
http://your-pi-ip:5000/dashboard.html
```

### **Systemd Service**
```bash
# Create service file
sudo nano /etc/systemd/system/camera-api.service

[Unit]
Description=Camera Streaming API Server
After=network.target

[Service]
Type=simple
User=edgecam
WorkingDirectory=/home/edgecam/projects/knitting-rpi-gs
ExecStart=/usr/bin/python3 api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl enable camera-api.service
sudo systemctl start camera-api.service
```

### **Monitoring Setup**
```bash
# Add to crontab for automated monitoring
*/5 * * * * curl -s http://localhost:5000/api/health/summary > /dev/null

# Monitor API server
sudo journalctl -u camera-api.service -f
```

## 🎯 **Expected Results**

### **Before Implementation**
- ❌ Manual issue detection and resolution
- ❌ No real-time monitoring
- ❌ Reactive problem solving
- ❌ Limited system visibility

### **After Implementation**
- ✅ Real-time issue detection and resolution
- ✅ Comprehensive monitoring dashboard
- ✅ Proactive problem prevention
- ✅ Complete system visibility and control

This API server and production safeguards system provides enterprise-grade monitoring, control, and safety features for your camera streaming system!
#!/usr/bin/env python3
"""
Comprehensive API Server for Camera Streaming System
Provides real-time monitoring, health collection, and issue detection.
"""

import time
import json
import threading
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import redis
import psutil
import os
import subprocess
from collections import defaultdict, deque
import queue
import signal
import sys

# Import our custom modules
from config import *
from camera_manager import get_camera_manager
from monitoring import system_monitor

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

class SystemHealthCollector:
    """Collects comprehensive system health data."""
    
    def __init__(self):
        self.health_history = deque(maxlen=1000)  # Keep last 1000 health records
        self.alert_history = deque(maxlen=500)    # Keep last 500 alerts
        self.performance_metrics = defaultdict(list)
        self.last_collection = time.time()
        self.collection_interval = 30  # Collect every 30 seconds
        
        # Start background health collection
        self.collection_thread = threading.Thread(target=self._background_collection, daemon=True)
        self.collection_thread.start()
    
    def _background_collection(self):
        """Background thread for continuous health collection."""
        while True:
            try:
                health_data = self.collect_comprehensive_health()
                self.health_history.append(health_data)
                
                # Check for critical issues
                self._check_critical_issues(health_data)
                
                time.sleep(self.collection_interval)
            except Exception as e:
                logging.error(f"Health collection error: {e}")
                time.sleep(5)
    
    def collect_comprehensive_health(self):
        """Collect comprehensive system health data."""
        try:
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'system_resources': self._get_system_resources(),
                'camera_status': self._get_camera_status(),
                'redis_status': self._get_redis_status(),
                'process_status': self._get_process_status(),
                'network_status': self._get_network_status(),
                'disk_status': self._get_disk_status(),
                'memory_status': self._get_memory_status(),
                'performance_metrics': self._get_performance_metrics(),
                'log_analysis': self._get_log_analysis(),
                'alerts': self._get_active_alerts(),
                'system_uptime': self._get_system_uptime(),
                'temperature': self._get_temperature(),
                'power_status': self._get_power_status()
            }
            
            return health_data
            
        except Exception as e:
            logging.error(f"Error collecting health data: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def _get_system_resources(self):
        """Get system resource usage."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
                'disk_percent': psutil.disk_usage('/').percent,
                'disk_free_gb': round(psutil.disk_usage('/').free / (1024**3), 2),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_camera_status(self):
        """Get camera status."""
        try:
            camera_manager = get_camera_manager()
            return camera_manager.get_camera_status()
        except Exception as e:
            return {'error': str(e)}
    
    def _get_redis_status(self):
        """Get Redis connection status."""
        try:
            client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, socket_timeout=5)
            ping_result = client.ping()
            client.close()
            
            return {
                'connected': ping_result,
                'host': REDIS_HOST,
                'port': REDIS_PORT,
                'response_time_ms': 0  # Could be enhanced with actual ping time
            }
        except Exception as e:
            return {'connected': False, 'error': str(e)}
    
    def _get_process_status(self):
        """Get status of key processes."""
        try:
            processes = ['cam1_stream.py', 'start.py', 'client.py']
            status = {}
            
            for proc_name in processes:
                try:
                    result = subprocess.run(['pgrep', '-f', proc_name], 
                                          capture_output=True, text=True)
                    pids = result.stdout.strip().split('\n') if result.stdout.strip() else []
                    
                    status[proc_name] = {
                        'running': len(pids) > 0,
                        'pid_count': len(pids),
                        'pids': pids if pids[0] else []
                    }
                except Exception as e:
                    status[proc_name] = {'running': False, 'error': str(e)}
            
            return status
        except Exception as e:
            return {'error': str(e)}
    
    def _get_network_status(self):
        """Get network connectivity status."""
        try:
            # Check internet connectivity
            internet_connected = False
            try:
                subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                             capture_output=True, timeout=5)
                internet_connected = True
            except:
                pass
            
            # Check local network
            local_network = False
            try:
                subprocess.run(['ping', '-c', '1', REDIS_HOST], 
                             capture_output=True, timeout=5)
                local_network = True
            except:
                pass
            
            return {
                'internet_connected': internet_connected,
                'local_network_connected': local_network,
                'redis_host_reachable': local_network
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_disk_status(self):
        """Get detailed disk status."""
        try:
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            return {
                'total_gb': round(disk_usage.total / (1024**3), 2),
                'used_gb': round(disk_usage.used / (1024**3), 2),
                'free_gb': round(disk_usage.free / (1024**3), 2),
                'percent_used': disk_usage.percent,
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0,
                'read_count': disk_io.read_count if disk_io else 0,
                'write_count': disk_io.write_count if disk_io else 0
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_memory_status(self):
        """Get detailed memory status."""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'percent_used': memory.percent,
                'swap_total_gb': round(swap.total / (1024**3), 2),
                'swap_used_gb': round(swap.used / (1024**3), 2),
                'swap_percent_used': swap.percent
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_performance_metrics(self):
        """Get performance metrics from logs."""
        try:
            metrics = {}
            
            # Read performance log if available
            if os.path.exists('logs/performance.log'):
                with open('logs/performance.log', 'r') as f:
                    lines = f.readlines()[-50:]  # Last 50 lines
                    
                    for line in lines:
                        if 'PERF:' in line:
                            try:
                                json_start = line.find('{')
                                if json_start != -1:
                                    data = json.loads(line[json_start:])
                                    metric_name = data.get('metric', 'unknown')
                                    if metric_name not in metrics:
                                        metrics[metric_name] = []
                                    metrics[metric_name].append(data)
                            except:
                                continue
            
            return metrics
        except Exception as e:
            return {'error': str(e)}
    
    def _get_log_analysis(self):
        """Get recent log analysis."""
        try:
            analysis = {
                'recent_errors': [],
                'recent_warnings': [],
                'camera_issues': [],
                'redis_issues': []
            }
            
            # Read recent logs
            log_files = ['logs/camera_system.log', 'logs/errors.log', 'greencam.log']
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()[-100:]  # Last 100 lines
                            
                            for line in lines:
                                if 'ERROR' in line:
                                    analysis['recent_errors'].append(line.strip())
                                elif 'WARNING' in line:
                                    analysis['recent_warnings'].append(line.strip())
                                elif 'CAMERA_ISSUE' in line:
                                    analysis['camera_issues'].append(line.strip())
                                elif 'REDIS' in line and ('ERROR' in line or 'WARNING' in line):
                                    analysis['redis_issues'].append(line.strip())
                    except:
                        continue
            
            # Keep only recent entries
            for key in analysis:
                analysis[key] = analysis[key][-10:]  # Last 10 entries
            
            return analysis
        except Exception as e:
            return {'error': str(e)}
    
    def _get_active_alerts(self):
        """Get currently active alerts."""
        try:
            alerts = []
            
            # Check for critical conditions
            health_data = self.collect_comprehensive_health()
            
            # CPU alert
            if health_data.get('system_resources', {}).get('cpu_percent', 0) > 80:
                alerts.append({
                    'type': 'high_cpu',
                    'severity': 'warning',
                    'message': f"High CPU usage: {health_data['system_resources']['cpu_percent']}%",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Memory alert
            if health_data.get('system_resources', {}).get('memory_percent', 0) > 85:
                alerts.append({
                    'type': 'high_memory',
                    'severity': 'warning',
                    'message': f"High memory usage: {health_data['system_resources']['memory_percent']}%",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Disk alert
            if health_data.get('system_resources', {}).get('disk_percent', 0) > 90:
                alerts.append({
                    'type': 'high_disk',
                    'severity': 'critical',
                    'message': f"High disk usage: {health_data['system_resources']['disk_percent']}%",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Camera alert
            camera_status = health_data.get('camera_status', {})
            if camera_status.get('should_reboot', False):
                alerts.append({
                    'type': 'camera_critical',
                    'severity': 'critical',
                    'message': "Camera requires system reboot",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Redis alert
            if not health_data.get('redis_status', {}).get('connected', True):
                alerts.append({
                    'type': 'redis_disconnected',
                    'severity': 'critical',
                    'message': "Redis connection lost",
                    'timestamp': datetime.now().isoformat()
                })
            
            return alerts
        except Exception as e:
            return [{'type': 'alert_error', 'severity': 'error', 'message': str(e)}]
    
    def _get_system_uptime(self):
        """Get system uptime."""
        try:
            uptime_seconds = time.time() - psutil.boot_time()
            return {
                'uptime_seconds': uptime_seconds,
                'uptime_formatted': str(timedelta(seconds=int(uptime_seconds))),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_temperature(self):
        """Get system temperature (Raspberry Pi specific)."""
        try:
            # Try to read CPU temperature
            if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp_celsius = int(f.read().strip()) / 1000
                return {
                    'cpu_temp_celsius': temp_celsius,
                    'cpu_temp_fahrenheit': (temp_celsius * 9/5) + 32
                }
            else:
                return {'error': 'Temperature sensor not available'}
        except Exception as e:
            return {'error': str(e)}
    
    def _get_power_status(self):
        """Get power status (Raspberry Pi specific)."""
        try:
            # Try to read power status
            if os.path.exists('/sys/class/power_supply/battery/voltage_now'):
                with open('/sys/class/power_supply/battery/voltage_now', 'r') as f:
                    voltage_mv = int(f.read().strip())
                return {
                    'voltage_mv': voltage_mv,
                    'voltage_v': voltage_mv / 1000
                }
            else:
                return {'error': 'Power sensor not available'}
        except Exception as e:
            return {'error': str(e)}
    
    def _check_critical_issues(self, health_data):
        """Check for critical issues and log alerts."""
        try:
            # Check for critical conditions
            if health_data.get('system_resources', {}).get('disk_percent', 0) > 95:
                self._log_alert('critical', 'disk_full', 'Disk usage critical (>95%)')
            
            if health_data.get('system_resources', {}).get('memory_percent', 0) > 95:
                self._log_alert('critical', 'memory_full', 'Memory usage critical (>95%)')
            
            if health_data.get('camera_status', {}).get('should_reboot', False):
                self._log_alert('critical', 'camera_reboot_needed', 'Camera requires system reboot')
            
            if not health_data.get('redis_status', {}).get('connected', True):
                self._log_alert('critical', 'redis_disconnected', 'Redis connection lost')
            
        except Exception as e:
            logging.error(f"Error checking critical issues: {e}")
    
    def _log_alert(self, severity, alert_type, message):
        """Log an alert."""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity,
            'type': alert_type,
            'message': message
        }
        self.alert_history.append(alert)
        logging.warning(f"ALERT: {severity.upper()} - {alert_type}: {message}")

# Global health collector
health_collector = SystemHealthCollector()

# API Routes
@app.route('/api/health', methods=['GET'])
def get_health():
    """Get current system health."""
    try:
        health_data = health_collector.collect_comprehensive_health()
        return jsonify(health_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health/summary', methods=['GET'])
def get_health_summary():
    """Get health summary for dashboard."""
    try:
        health_data = health_collector.collect_comprehensive_health()
        
        # Create summary
        summary = {
            'timestamp': health_data['timestamp'],
            'overall_status': 'healthy',
            'issues_count': 0,
            'critical_issues': 0,
            'warnings': 0,
            'components': {}
        }
        
        # Check system resources
        resources = health_data.get('system_resources', {})
        if resources.get('cpu_percent', 0) > 80:
            summary['warnings'] += 1
        if resources.get('memory_percent', 0) > 85:
            summary['warnings'] += 1
        if resources.get('disk_percent', 0) > 90:
            summary['critical_issues'] += 1
        
        # Check camera
        camera = health_data.get('camera_status', {})
        if camera.get('should_reboot', False):
            summary['critical_issues'] += 1
        summary['components']['camera'] = {
            'status': 'healthy' if camera.get('is_capturing') else 'unhealthy',
            'health_score': camera.get('health_status', {}).get('health_score', 0)
        }
        
        # Check Redis
        redis_status = health_data.get('redis_status', {})
        if not redis_status.get('connected', True):
            summary['critical_issues'] += 1
        summary['components']['redis'] = {
            'status': 'connected' if redis_status.get('connected') else 'disconnected'
        }
        
        # Check processes
        processes = health_data.get('process_status', {})
        summary['components']['processes'] = {}
        for proc_name, status in processes.items():
            summary['components']['processes'][proc_name] = {
                'status': 'running' if status.get('running') else 'stopped'
            }
            if not status.get('running'):
                summary['issues_count'] += 1
        
        # Set overall status
        if summary['critical_issues'] > 0:
            summary['overall_status'] = 'critical'
        elif summary['warnings'] > 0 or summary['issues_count'] > 0:
            summary['overall_status'] = 'warning'
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/camera/status', methods=['GET'])
def get_camera_status():
    """Get detailed camera status."""
    try:
        camera_manager = get_camera_manager()
        status = camera_manager.get_camera_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/camera/test', methods=['POST'])
def test_camera():
    """Test camera functionality."""
    try:
        camera_manager = get_camera_manager()
        success, frame = camera_manager.capture_frame_with_timeout(timeout=10)
        
        result = {
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'frame_size': frame.shape if success and frame is not None else None
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/camera/recover', methods=['POST'])
def recover_camera():
    """Attempt camera recovery."""
    try:
        camera_manager = get_camera_manager()
        success = camera_manager.attempt_camera_recovery()
        
        result = {
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'message': 'Camera recovery successful' if success else 'Camera recovery failed'
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get recent alerts."""
    try:
        alerts = list(health_collector.alert_history)
        return jsonify(alerts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/recent', methods=['GET'])
def get_recent_logs():
    """Get recent log entries."""
    try:
        log_type = request.args.get('type', 'all')  # all, errors, camera, redis
        limit = int(request.args.get('limit', 50))
        
        logs = []
        log_files = ['logs/camera_system.log', 'logs/errors.log', 'greencam.log']
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()[-limit:]
                        
                        for line in lines:
                            if log_type == 'all' or log_type.upper() in line.upper():
                                logs.append(line.strip())
                except:
                    continue
        
        return jsonify(logs[-limit:])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/reboot', methods=['POST'])
def reboot_system():
    """Trigger system reboot."""
    try:
        # Log the reboot request
        logging.critical("System reboot requested via API")
        
        # Set kill file to trigger reboot
        with open(KILL_FILE, "r+") as f:
            content = f.read().strip()
            if content == "0":
                f.seek(0)
                f.write("1")
                f.truncate()
        
        return jsonify({
            'success': True,
            'message': 'System reboot initiated',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/restart-services', methods=['POST'])
def restart_services():
    """Restart camera streaming services."""
    try:
        # Stop services
        subprocess.run(['pkill', '-f', 'cam1_stream.py'], capture_output=True)
        subprocess.run(['pkill', '-f', 'start.py'], capture_output=True)
        time.sleep(2)
        
        # Start services
        subprocess.Popen(['python3', 'start.py'])
        
        return jsonify({
            'success': True,
            'message': 'Services restarted',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/performance', methods=['GET'])
def get_performance_metrics():
    """Get performance metrics."""
    try:
        health_data = health_collector.collect_comprehensive_health()
        return jsonify(health_data.get('performance_metrics', {}))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/history', methods=['GET'])
def get_health_history():
    """Get health history."""
    try:
        hours = int(request.args.get('hours', 24))
        cutoff_time = time.time() - (hours * 3600)
        
        history = []
        for record in health_collector.health_history:
            try:
                record_time = datetime.fromisoformat(record['timestamp']).timestamp()
                if record_time >= cutoff_time:
                    history.append(record)
            except:
                continue
        
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get comprehensive dashboard data."""
    try:
        # Get current health
        health_data = health_collector.collect_comprehensive_health()
        
        # Get recent alerts
        alerts = list(health_collector.alert_history)[-10:]  # Last 10 alerts
        
        # Get health history for charts
        history = list(health_collector.health_history)[-100:]  # Last 100 records
        
        dashboard_data = {
            'current_health': health_data,
            'recent_alerts': alerts,
            'health_history': history,
            'system_info': {
                'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown',
                'platform': os.uname().sysname if hasattr(os, 'uname') else 'unknown',
                'uptime': health_data.get('system_uptime', {}),
                'temperature': health_data.get('temperature', {}),
                'power_status': health_data.get('power_status', {})
            }
        }
        
        return jsonify(dashboard_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_api_status():
    """Get API server status."""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - health_collector.last_collection,
        'version': '1.0.0'
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logging.info("API server shutting down...")
    sys.exit(0)

if __name__ == '__main__':
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/api_server.log'),
            logging.StreamHandler()
        ]
    )
    
    logging.info("Starting API server...")
    
    # Run the API server
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
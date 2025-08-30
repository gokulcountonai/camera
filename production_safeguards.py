#!/usr/bin/env python3
"""
Production Safeguards and Advanced Monitoring
Provides additional safety measures and early warning systems for production environments.
"""

import time
import threading
import logging
import json
import os
import subprocess
import smtplib
import requests
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psutil
import signal
import sys
from config import *

class ProductionSafeguards:
    """Advanced production safeguards and monitoring."""
    
    def __init__(self):
        self.safeguards_enabled = True
        self.alert_history = deque(maxlen=1000)
        self.threshold_violations = defaultdict(int)
        self.last_cleanup = time.time()
        self.emergency_mode = False
        
        # Safety thresholds
        self.thresholds = {
            'cpu_critical': 95,
            'cpu_warning': 85,
            'memory_critical': 95,
            'memory_warning': 90,
            'disk_critical': 95,
            'disk_warning': 90,
            'temperature_critical': 80,  # Celsius
            'temperature_warning': 70,
            'camera_failures_critical': 10,
            'camera_failures_warning': 5,
            'redis_disconnection_time': 60,  # seconds
            'process_restart_threshold': 3,
            'emergency_cleanup_interval': 3600  # 1 hour
        }
        
        # Start monitoring threads
        self.start_monitoring()
    
    def start_monitoring(self):
        """Start all monitoring threads."""
        threads = [
            threading.Thread(target=self._resource_monitor, daemon=True),
            threading.Thread(target=self._camera_safety_monitor, daemon=True),
            threading.Thread(target=self._redis_health_monitor, daemon=True),
            threading.Thread(target=self._process_watchdog, daemon=True),
            threading.Thread(target=self._emergency_cleanup, daemon=True),
            threading.Thread(target=self._alert_manager, daemon=True)
        ]
        
        for thread in threads:
            thread.start()
        
        logging.info("Production safeguards monitoring started")
    
    def _resource_monitor(self):
        """Monitor system resources continuously."""
        while self.safeguards_enabled:
            try:
                # CPU monitoring
                cpu_percent = psutil.cpu_percent(interval=5)
                if cpu_percent > self.thresholds['cpu_critical']:
                    self._trigger_emergency_action('cpu_critical', f"CPU usage critical: {cpu_percent}%")
                elif cpu_percent > self.thresholds['cpu_warning']:
                    self._log_warning('cpu_high', f"CPU usage high: {cpu_percent}%")
                
                # Memory monitoring
                memory = psutil.virtual_memory()
                if memory.percent > self.thresholds['memory_critical']:
                    self._trigger_emergency_action('memory_critical', f"Memory usage critical: {memory.percent}%")
                elif memory.percent > self.thresholds['memory_warning']:
                    self._log_warning('memory_high', f"Memory usage high: {memory.percent}%")
                
                # Disk monitoring
                disk = psutil.disk_usage('/')
                if disk.percent > self.thresholds['disk_critical']:
                    self._trigger_emergency_action('disk_critical', f"Disk usage critical: {disk.percent}%")
                elif disk.percent > self.thresholds['disk_warning']:
                    self._log_warning('disk_high', f"Disk usage high: {disk.percent}%")
                
                # Temperature monitoring (Raspberry Pi)
                temp = self._get_cpu_temperature()
                if temp and temp > self.thresholds['temperature_critical']:
                    self._trigger_emergency_action('temperature_critical', f"CPU temperature critical: {temp}°C")
                elif temp and temp > self.thresholds['temperature_warning']:
                    self._log_warning('temperature_high', f"CPU temperature high: {temp}°C")
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logging.error(f"Resource monitor error: {e}")
                time.sleep(60)
    
    def _camera_safety_monitor(self):
        """Monitor camera safety and performance."""
        while self.safeguards_enabled:
            try:
                from camera_manager import get_camera_manager
                camera_manager = get_camera_manager()
                status = camera_manager.get_camera_status()
                
                # Check consecutive failures
                failures = status.get('health_status', {}).get('consecutive_failures', 0)
                if failures >= self.thresholds['camera_failures_critical']:
                    self._trigger_emergency_action('camera_critical', f"Camera failures critical: {failures}")
                elif failures >= self.thresholds['camera_failures_warning']:
                    self._log_warning('camera_failures', f"Camera failures high: {failures}")
                
                # Check if camera is stuck
                last_frame_age = status.get('last_frame_age', 0)
                if last_frame_age > 300:  # 5 minutes without frame
                    self._trigger_emergency_action('camera_stuck', f"Camera appears stuck: {last_frame_age}s since last frame")
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logging.error(f"Camera safety monitor error: {e}")
                time.sleep(120)
    
    def _redis_health_monitor(self):
        """Monitor Redis connection health."""
        while self.safeguards_enabled:
            try:
                import redis
                client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, socket_timeout=5)
                
                start_time = time.time()
                ping_result = client.ping()
                response_time = time.time() - start_time
                client.close()
                
                if not ping_result:
                    self._trigger_emergency_action('redis_disconnected', "Redis connection lost")
                elif response_time > 2:  # Slow response
                    self._log_warning('redis_slow', f"Redis response slow: {response_time:.2f}s")
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logging.error(f"Redis health monitor error: {e}")
                time.sleep(60)
    
    def _process_watchdog(self):
        """Monitor critical processes and restart if needed."""
        while self.safeguards_enabled:
            try:
                critical_processes = ['cam1_stream.py', 'start.py']
                
                for process_name in critical_processes:
                    if not self._is_process_running(process_name):
                        self.threshold_violations[f'process_{process_name}'] += 1
                        
                        if self.threshold_violations[f'process_{process_name}'] >= self.thresholds['process_restart_threshold']:
                            self._trigger_emergency_action('process_dead', f"Critical process dead: {process_name}")
                        else:
                            self._log_warning('process_restart', f"Restarting process: {process_name}")
                            self._restart_process(process_name)
                    else:
                        # Reset violation counter if process is running
                        self.threshold_violations[f'process_{process_name}'] = 0
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logging.error(f"Process watchdog error: {e}")
                time.sleep(120)
    
    def _emergency_cleanup(self):
        """Perform emergency cleanup operations."""
        while self.safeguards_enabled:
            try:
                current_time = time.time()
                
                # Cleanup old logs
                if current_time - self.last_cleanup > self.thresholds['emergency_cleanup_interval']:
                    self._cleanup_old_logs()
                    self._cleanup_old_images()
                    self._cleanup_temp_files()
                    self.last_cleanup = current_time
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logging.error(f"Emergency cleanup error: {e}")
                time.sleep(600)
    
    def _alert_manager(self):
        """Manage and send alerts."""
        while self.safeguards_enabled:
            try:
                # Process pending alerts
                while len(self.alert_history) > 0:
                    alert = self.alert_history.popleft()
                    self._send_alert(alert)
                
                time.sleep(10)  # Process alerts every 10 seconds
                
            except Exception as e:
                logging.error(f"Alert manager error: {e}")
                time.sleep(30)
    
    def _trigger_emergency_action(self, action_type, message):
        """Trigger emergency actions based on critical conditions."""
        try:
            logging.critical(f"EMERGENCY ACTION TRIGGERED: {action_type} - {message}")
            
            # Log emergency action
            alert = {
                'timestamp': datetime.now().isoformat(),
                'type': action_type,
                'severity': 'critical',
                'message': message,
                'action_taken': 'emergency_mode_activated'
            }
            self.alert_history.append(alert)
            
            # Take emergency actions
            if action_type in ['cpu_critical', 'memory_critical', 'temperature_critical']:
                self._activate_emergency_mode()
            
            elif action_type == 'disk_critical':
                self._emergency_disk_cleanup()
            
            elif action_type in ['camera_critical', 'camera_stuck']:
                self._emergency_camera_recovery()
            
            elif action_type == 'redis_disconnected':
                self._emergency_redis_recovery()
            
            elif action_type == 'process_dead':
                self._emergency_process_recovery()
            
            # Send immediate notification
            self._send_emergency_notification(action_type, message)
            
        except Exception as e:
            logging.error(f"Emergency action error: {e}")
    
    def _activate_emergency_mode(self):
        """Activate emergency mode to reduce system load."""
        try:
            self.emergency_mode = True
            logging.critical("EMERGENCY MODE ACTIVATED - Reducing system load")
            
            # Reduce camera frame rate
            from camera_manager import get_camera_manager
            camera_manager = get_camera_manager()
            # Could implement frame rate reduction here
            
            # Kill non-critical processes
            self._kill_non_critical_processes()
            
            # Clear memory caches
            os.system('sync')  # Flush filesystem buffers
            os.system('echo 3 > /proc/sys/vm/drop_caches')  # Clear page cache
            
        except Exception as e:
            logging.error(f"Emergency mode activation error: {e}")
    
    def _emergency_disk_cleanup(self):
        """Emergency disk cleanup."""
        try:
            logging.critical("EMERGENCY DISK CLEANUP - Freeing disk space")
            
            # Remove old log files
            self._cleanup_old_logs(aggressive=True)
            
            # Remove old images
            self._cleanup_old_images(aggressive=True)
            
            # Remove temporary files
            self._cleanup_temp_files()
            
            # Clear Redis cache if possible
            try:
                import redis
                client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
                client.flushdb()
                client.close()
            except:
                pass
            
        except Exception as e:
            logging.error(f"Emergency disk cleanup error: {e}")
    
    def _emergency_camera_recovery(self):
        """Emergency camera recovery."""
        try:
            logging.critical("EMERGENCY CAMERA RECOVERY - Attempting recovery")
            
            from camera_manager import get_camera_manager
            camera_manager = get_camera_manager()
            
            # Force camera recovery
            success = camera_manager.attempt_camera_recovery()
            
            if not success:
                # If recovery fails, trigger system reboot
                logging.critical("Camera recovery failed - triggering system reboot")
                self._trigger_system_reboot()
            
        except Exception as e:
            logging.error(f"Emergency camera recovery error: {e}")
    
    def _emergency_redis_recovery(self):
        """Emergency Redis recovery."""
        try:
            logging.critical("EMERGENCY REDIS RECOVERY - Attempting reconnection")
            
            # Try to restart Redis service
            subprocess.run(['sudo', 'systemctl', 'restart', 'redis'], capture_output=True)
            time.sleep(5)
            
            # Test connection
            import redis
            client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, socket_timeout=10)
            if not client.ping():
                logging.critical("Redis recovery failed - triggering system reboot")
                self._trigger_system_reboot()
            client.close()
            
        except Exception as e:
            logging.error(f"Emergency Redis recovery error: {e}")
    
    def _emergency_process_recovery(self):
        """Emergency process recovery."""
        try:
            logging.critical("EMERGENCY PROCESS RECOVERY - Restarting services")
            
            # Restart camera streaming services
            subprocess.run(['pkill', '-f', 'cam1_stream.py'], capture_output=True)
            subprocess.run(['pkill', '-f', 'start.py'], capture_output=True)
            time.sleep(2)
            
            # Start services
            subprocess.Popen(['python3', 'start.py'])
            
        except Exception as e:
            logging.error(f"Emergency process recovery error: {e}")
    
    def _trigger_system_reboot(self):
        """Trigger system reboot as last resort."""
        try:
            logging.critical("TRIGGERING SYSTEM REBOOT - Last resort recovery")
            
            # Set kill file to trigger reboot
            with open(KILL_FILE, "r+") as f:
                content = f.read().strip()
                if content == "0":
                    f.seek(0)
                    f.write("1")
                    f.truncate()
            
            # Wait and force reboot
            time.sleep(10)
            os.system(REBOOT_COMMAND)
            
        except Exception as e:
            logging.error(f"System reboot trigger error: {e}")
    
    def _log_warning(self, warning_type, message):
        """Log a warning."""
        logging.warning(f"SAFEGUARD WARNING: {warning_type} - {message}")
        
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': warning_type,
            'severity': 'warning',
            'message': message
        }
        self.alert_history.append(alert)
    
    def _get_cpu_temperature(self):
        """Get CPU temperature."""
        try:
            if os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    return int(f.read().strip()) / 1000
        except:
            pass
        return None
    
    def _is_process_running(self, process_name):
        """Check if a process is running."""
        try:
            result = subprocess.run(['pgrep', '-f', process_name], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def _restart_process(self, process_name):
        """Restart a specific process."""
        try:
            if process_name == 'cam1_stream.py':
                subprocess.run(['pkill', '-f', process_name], capture_output=True)
                time.sleep(2)
                subprocess.Popen(['python3', process_name])
            elif process_name == 'start.py':
                subprocess.run(['pkill', '-f', process_name], capture_output=True)
                time.sleep(2)
                subprocess.Popen(['python3', process_name])
        except Exception as e:
            logging.error(f"Process restart error: {e}")
    
    def _kill_non_critical_processes(self):
        """Kill non-critical processes to free resources."""
        try:
            non_critical = ['python3', 'node', 'npm']
            for process in psutil.process_iter(['pid', 'name']):
                try:
                    if process.info['name'] in non_critical:
                        process.terminate()
                except:
                    pass
        except Exception as e:
            logging.error(f"Kill non-critical processes error: {e}")
    
    def _cleanup_old_logs(self, aggressive=False):
        """Clean up old log files."""
        try:
            log_files = ['logs/camera_system.log', 'logs/errors.log', 'logs/performance.log', 'greencam.log']
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    size_mb = os.path.getsize(log_file) / (1024 * 1024)
                    
                    if aggressive or size_mb > 50:  # 50MB threshold
                        # Truncate log file
                        with open(log_file, 'r+') as f:
                            f.seek(-10 * 1024 * 1024, 2)  # Keep last 10MB
                            content = f.read()
                            f.seek(0)
                            f.write(content)
                            f.truncate()
                        
                        logging.info(f"Cleaned up log file: {log_file}")
        except Exception as e:
            logging.error(f"Log cleanup error: {e}")
    
    def _cleanup_old_images(self, aggressive=False):
        """Clean up old image files."""
        try:
            if os.path.exists('images'):
                # Remove images older than 24 hours (or 1 hour if aggressive)
                cutoff_hours = 1 if aggressive else 24
                cutoff_time = time.time() - (cutoff_hours * 3600)
                
                for filename in os.listdir('images'):
                    filepath = os.path.join('images', filename)
                    if os.path.isfile(filepath):
                        if os.path.getmtime(filepath) < cutoff_time:
                            os.remove(filepath)
                            logging.info(f"Removed old image: {filename}")
        except Exception as e:
            logging.error(f"Image cleanup error: {e}")
    
    def _cleanup_temp_files(self):
        """Clean up temporary files."""
        try:
            # Clean up Python cache
            subprocess.run(['find', '.', '-name', '*.pyc', '-delete'], capture_output=True)
            subprocess.run(['find', '.', '-name', '__pycache__', '-type', 'd', '-exec', 'rm', '-rf', '{}', '+'], capture_output=True)
            
            # Clean up temporary files
            subprocess.run(['find', '/tmp', '-name', '*.tmp', '-mtime', '+1', '-delete'], capture_output=True)
        except Exception as e:
            logging.error(f"Temp file cleanup error: {e}")
    
    def _send_alert(self, alert):
        """Send alert via configured method."""
        try:
            # Log alert
            logging.warning(f"ALERT: {alert['type']} - {alert['message']}")
            
            # Could implement email, SMS, or webhook notifications here
            # For now, just log to file
            
        except Exception as e:
            logging.error(f"Alert sending error: {e}")
    
    def _send_emergency_notification(self, action_type, message):
        """Send emergency notification."""
        try:
            # Log emergency notification
            logging.critical(f"EMERGENCY NOTIFICATION: {action_type} - {message}")
            
            # Could implement immediate notification methods here
            # Email, SMS, Slack, etc.
            
        except Exception as e:
            logging.error(f"Emergency notification error: {e}")
    
    def get_safeguard_status(self):
        """Get current safeguard status."""
        return {
            'enabled': self.safeguards_enabled,
            'emergency_mode': self.emergency_mode,
            'threshold_violations': dict(self.threshold_violations),
            'last_cleanup': self.last_cleanup,
            'alert_count': len(self.alert_history),
            'thresholds': self.thresholds
        }
    
    def disable_safeguards(self):
        """Disable production safeguards (use with caution)."""
        self.safeguards_enabled = False
        logging.warning("Production safeguards disabled")
    
    def enable_safeguards(self):
        """Enable production safeguards."""
        self.safeguards_enabled = True
        logging.info("Production safeguards enabled")

# Global safeguards instance
production_safeguards = None

def get_production_safeguards():
    """Get or create the global production safeguards instance."""
    global production_safeguards
    if production_safeguards is None:
        production_safeguards = ProductionSafeguards()
    return production_safeguards

def disable_safeguards():
    """Disable production safeguards."""
    global production_safeguards
    if production_safeguards:
        production_safeguards.disable_safeguards()

def enable_safeguards():
    """Enable production safeguards."""
    global production_safeguards
    if production_safeguards:
        production_safeguards.enable_safeguards()
"""
Comprehensive monitoring and logging system for the camera streaming application.
Provides centralized logging, performance monitoring, and issue tracking.
"""

import logging
import time
import os
import json
import threading
import traceback
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from collections import defaultdict, deque
import queue
from config import *

# Optional psutil import for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. System resource monitoring will be limited.")

class SystemMonitor:
    """System-wide monitoring and logging."""
    
    def __init__(self):
        self.start_time = time.time()
        self.issue_counters = defaultdict(int)
        self.performance_metrics = deque(maxlen=1000)
        self.connection_status = {
            'redis_connected': False,
            'camera_active': False,
            'last_redis_check': 0,
            'last_camera_check': 0
        }
        self.setup_logging()
        
    def setup_logging(self):
        """Setup comprehensive logging system."""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Main application log
        self.logger = logging.getLogger('camera_system')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Main log file with rotation
        main_handler = RotatingFileHandler(
            'logs/camera_system.log',
            maxBytes=50*1024*1024,  # 50MB
            backupCount=5
        )
        main_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(main_handler)
        
        # Error log file (errors only)
        error_handler = RotatingFileHandler(
            'logs/errors.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        ))
        self.logger.addHandler(error_handler)
        
        # Performance log file
        perf_handler = TimedRotatingFileHandler(
            'logs/performance.log',
            when='midnight',
            interval=1,
            backupCount=7
        )
        perf_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        self.perf_logger = logging.getLogger('performance')
        self.perf_logger.addHandler(perf_handler)
        self.perf_logger.setLevel(logging.INFO)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(console_handler)
        
    def log_issue(self, issue_type, message, severity='WARNING', context=None):
        """Log an issue with context and increment counter."""
        self.issue_counters[issue_type] += 1
        
        log_data = {
            'issue_type': issue_type,
            'message': message,
            'severity': severity,
            'count': self.issue_counters[issue_type],
            'uptime': time.time() - self.start_time,
            'context': context or {}
        }
        
        if severity == 'ERROR':
            self.logger.error(f"ISSUE: {json.dumps(log_data)}")
        elif severity == 'WARNING':
            self.logger.warning(f"ISSUE: {json.dumps(log_data)}")
        else:
            self.logger.info(f"ISSUE: {json.dumps(log_data)}")
            
    def log_performance(self, metric_name, value, unit=None):
        """Log performance metrics."""
        metric_data = {
            'metric': metric_name,
            'value': value,
            'unit': unit,
            'timestamp': time.time(),
            'uptime': time.time() - self.start_time
        }
        
        self.performance_metrics.append(metric_data)
        self.perf_logger.info(f"PERF: {json.dumps(metric_data)}")
        
    def log_connection_status(self, service, status, details=None):
        """Log connection status changes."""
        self.connection_status[f'{service}_connected'] = status
        self.connection_status[f'last_{service}_check'] = time.time()
        
        status_data = {
            'service': service,
            'status': status,
            'details': details,
            'uptime': time.time() - self.start_time
        }
        
        if status:
            self.logger.info(f"CONNECTION: {json.dumps(status_data)}")
        else:
            self.logger.warning(f"CONNECTION_LOST: {json.dumps(status_data)}")
            
    def get_system_health(self):
        """Get current system health status."""
        try:
            health_data = {
                'uptime': time.time() - self.start_time,
                'connection_status': self.connection_status.copy(),
                'issue_counts': dict(self.issue_counters),
                'active_threads': threading.active_count()
            }
            
            if PSUTIL_AVAILABLE:
                try:
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    
                    health_data.update({
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory.percent,
                        'memory_available': memory.available,
                        'disk_percent': disk.percent,
                        'disk_free': disk.free
                    })
                except Exception as e:
                    self.log_issue('psutil_health_check_failed', str(e), 'WARNING')
            else:
                health_data.update({
                    'cpu_percent': None,
                    'memory_percent': None,
                    'memory_available': None,
                    'disk_percent': None,
                    'disk_free': None
                })
            
            return health_data
        except Exception as e:
            self.log_issue('system_health_check_failed', str(e), 'ERROR')
            return None
            
    def log_system_health(self):
        """Log current system health."""
        health = self.get_system_health()
        if health:
            self.log_performance('system_health', health)
            
    def get_issue_summary(self):
        """Get summary of all issues."""
        return {
            'total_issues': sum(self.issue_counters.values()),
            'issue_breakdown': dict(self.issue_counters),
            'uptime': time.time() - self.start_time
        }

# Global monitor instance
system_monitor = SystemMonitor()

class PerformanceTracker:
    """Track performance metrics for specific operations."""
    
    def __init__(self, operation_name):
        self.operation_name = operation_name
        self.start_time = None
        self.count = 0
        self.total_time = 0
        self.min_time = float('inf')
        self.max_time = 0
        
    def start(self):
        """Start timing an operation."""
        self.start_time = time.time()
        
    def end(self):
        """End timing an operation and log metrics."""
        if self.start_time is None:
            return
            
        duration = time.time() - self.start_time
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        
        # Log individual operation time
        system_monitor.log_performance(f"{self.operation_name}_duration", duration, 'seconds')
        
        # Log aggregated metrics every 10 operations
        if self.count % 10 == 0:
            avg_time = self.total_time / self.count
            system_monitor.log_performance(f"{self.operation_name}_avg_duration", avg_time, 'seconds')
            system_monitor.log_performance(f"{self.operation_name}_min_duration", self.min_time, 'seconds')
            system_monitor.log_performance(f"{self.operation_name}_max_duration", self.max_time, 'seconds')
            system_monitor.log_performance(f"{self.operation_name}_count", self.count, 'operations')
            
        self.start_time = None

class ConnectionMonitor:
    """Monitor Redis and camera connections."""
    
    def __init__(self):
        self.last_redis_check = 0
        self.last_camera_check = 0
        self.redis_failures = 0
        self.camera_failures = 0
        
    def check_redis_connection(self, redis_client, pubsub_client=None):
        """Check Redis connection health."""
        try:
            if not redis_client.ping():
                self.redis_failures += 1
                system_monitor.log_connection_status('redis', False, {'failures': self.redis_failures})
                return False
                
            if pubsub_client and not pubsub_client.connection:
                self.redis_failures += 1
                system_monitor.log_connection_status('redis_pubsub', False, {'failures': self.redis_failures})
                return False
                
            system_monitor.log_connection_status('redis', True, {'failures': self.redis_failures})
            return True
            
        except Exception as e:
            self.redis_failures += 1
            system_monitor.log_issue('redis_connection_check_failed', str(e), 'ERROR')
            system_monitor.log_connection_status('redis', False, {'failures': self.redis_failures, 'error': str(e)})
            return False
            
    def check_camera_connection(self, camera):
        """Check camera connection health."""
        try:
            if camera is None:
                self.camera_failures += 1
                system_monitor.log_connection_status('camera', False, {'failures': self.camera_failures})
                return False
                
            # Try to get camera status
            # This is a basic check - you might need to adjust based on your camera library
            system_monitor.log_connection_status('camera', True, {'failures': self.camera_failures})
            return True
            
        except Exception as e:
            self.camera_failures += 1
            system_monitor.log_issue('camera_connection_check_failed', str(e), 'ERROR')
            system_monitor.log_connection_status('camera', False, {'failures': self.camera_failures, 'error': str(e)})
            return False

# Global connection monitor
connection_monitor = ConnectionMonitor()

def log_function_call(func_name, success=True, duration=None, error=None, context=None):
    """Decorator to log function calls and their outcomes."""
    if success:
        system_monitor.logger.info(f"FUNCTION_SUCCESS: {func_name} - Duration: {duration:.3f}s")
    else:
        system_monitor.log_issue('function_failure', f"Function {func_name} failed", 'ERROR', {
            'duration': duration,
            'error': str(error) if error else None,
            'context': context or {}
        })

def monitor_function(func):
    """Decorator to monitor function performance and errors."""
    def wrapper(*args, **kwargs):
        tracker = PerformanceTracker(func.__name__)
        tracker.start()
        
        try:
            result = func(*args, **kwargs)
            tracker.end()
            log_function_call(func.__name__, True, tracker.total_time / tracker.count if tracker.count > 0 else 0)
            return result
        except Exception as e:
            tracker.end()
            log_function_call(func.__name__, False, tracker.total_time / tracker.count if tracker.count > 0 else 0, e)
            raise
    return wrapper
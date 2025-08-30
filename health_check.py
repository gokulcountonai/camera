#!/usr/bin/env python3
"""
Health check script for the camera streaming system.
Provides easy monitoring and status checking capabilities.
"""

import json
import time
import os
import sys
from datetime import datetime
from monitoring import system_monitor, connection_monitor
from config import *

def check_log_files():
    """Check if log files exist and are accessible."""
    log_files = [
        'logs/camera_system.log',
        'logs/errors.log',
        'logs/performance.log',
        'greencam.log'
    ]
    
    results = {}
    for log_file in log_files:
        try:
            if os.path.exists(log_file):
                size = os.path.getsize(log_file)
                modified = datetime.fromtimestamp(os.path.getmtime(log_file))
                results[log_file] = {
                    'exists': True,
                    'size_bytes': size,
                    'size_mb': round(size / (1024 * 1024), 2),
                    'last_modified': modified.isoformat()
                }
            else:
                results[log_file] = {'exists': False}
        except Exception as e:
            results[log_file] = {'exists': False, 'error': str(e)}
    
    return results

def check_process_status():
    """Check if main processes are running."""
    try:
        import psutil
        
        processes = ['cam1_stream.py', 'start.py', 'client.py']
        results = {}
        
        for proc_name in processes:
            try:
                found_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                    try:
                        if proc.info['cmdline'] and any(proc_name in cmd for cmd in proc.info['cmdline']):
                            found_processes.append({
                                'pid': proc.info['pid'],
                                'cpu_percent': proc.info['cpu_percent'],
                                'memory_percent': proc.info['memory_percent'],
                                'cmdline': ' '.join(proc.info['cmdline'])
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                results[proc_name] = {
                    'running': len(found_processes) > 0,
                    'count': len(found_processes),
                    'processes': found_processes
                }
            except Exception as e:
                results[proc_name] = {'running': False, 'error': str(e)}
        
        return results
    except ImportError:
        return {
            'cam1_stream.py': {'running': False, 'error': 'psutil not available'},
            'start.py': {'running': False, 'error': 'psutil not available'},
            'client.py': {'running': False, 'error': 'psutil not available'}
        }

def check_redis_connection():
    """Check Redis connection status."""
    try:
        import redis
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, socket_timeout=5)
        ping_result = client.ping()
        client.close()
        
        return {
            'connected': ping_result,
            'host': REDIS_HOST,
            'port': REDIS_PORT,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'connected': False,
            'error': str(e),
            'host': REDIS_HOST,
            'port': REDIS_PORT,
            'timestamp': datetime.now().isoformat()
        }

def check_system_resources():
    """Check system resource usage."""
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': round(memory.available / (1024**3), 2),
            'disk_percent': disk.percent,
            'disk_free_gb': round(disk.free / (1024**3), 2),
            'timestamp': datetime.now().isoformat()
        }
    except ImportError:
        return {
            'cpu_percent': None,
            'memory_percent': None,
            'memory_available_gb': None,
            'disk_percent': None,
            'disk_free_gb': None,
            'timestamp': datetime.now().isoformat(),
            'note': 'psutil not available'
        }
    except Exception as e:
        return {'error': str(e)}

def get_recent_errors():
    """Get recent error messages from logs."""
    errors = []
    
    try:
        if os.path.exists('logs/errors.log'):
            with open('logs/errors.log', 'r') as f:
                lines = f.readlines()
                # Get last 10 error lines
                for line in lines[-10:]:
                    if line.strip():
                        errors.append(line.strip())
    except Exception as e:
        errors.append(f"Error reading error log: {e}")
    
    return errors

def get_performance_summary():
    """Get performance summary from logs."""
    try:
        if os.path.exists('logs/performance.log'):
            with open('logs/performance.log', 'r') as f:
                lines = f.readlines()
                # Get last 20 performance lines
                return [line.strip() for line in lines[-20:] if line.strip()]
    except Exception as e:
        return [f"Error reading performance log: {e}"]
    
    return []

def print_health_report():
    """Print a comprehensive health report."""
    print("=" * 60)
    print("CAMERA STREAMING SYSTEM HEALTH REPORT")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # System Resources
    print("SYSTEM RESOURCES:")
    print("-" * 20)
    resources = check_system_resources()
    if 'error' not in resources:
        print(f"CPU Usage: {resources['cpu_percent']}%")
        print(f"Memory Usage: {resources['memory_percent']}%")
        print(f"Memory Available: {resources['memory_available_gb']} GB")
        print(f"Disk Usage: {resources['disk_percent']}%")
        print(f"Disk Free: {resources['disk_free_gb']} GB")
    else:
        print(f"Error checking resources: {resources['error']}")
    print()
    
    # Redis Connection
    print("REDIS CONNECTION:")
    print("-" * 20)
    redis_status = check_redis_connection()
    if redis_status['connected']:
        print(f"✅ Connected to {redis_status['host']}:{redis_status['port']}")
    else:
        print(f"❌ Not connected to {redis_status['host']}:{redis_status['port']}")
        if 'error' in redis_status:
            print(f"   Error: {redis_status['error']}")
    print()
    
    # Process Status
    print("PROCESS STATUS:")
    print("-" * 20)
    processes = check_process_status()
    for proc_name, status in processes.items():
        if status['running']:
            print(f"✅ {proc_name}: {status['count']} process(es) running")
            for proc in status['processes']:
                print(f"   PID {proc['pid']}: CPU {proc['cpu_percent']}%, Memory {proc['memory_percent']}%")
        else:
            print(f"❌ {proc_name}: Not running")
            if 'error' in status:
                print(f"   Error: {status['error']}")
    print()
    
    # Log Files
    print("LOG FILES:")
    print("-" * 20)
    log_status = check_log_files()
    for log_file, status in log_status.items():
        if status['exists']:
            print(f"✅ {log_file}: {status['size_mb']} MB")
        else:
            print(f"❌ {log_file}: Not found")
    print()
    
    # Recent Errors
    print("RECENT ERRORS:")
    print("-" * 20)
    errors = get_recent_errors()
    if errors:
        for error in errors[-5:]:  # Show last 5 errors
            print(f"❌ {error}")
    else:
        print("✅ No recent errors found")
    print()
    
    print("=" * 60)

def print_json_report():
    """Print health report in JSON format."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'system_resources': check_system_resources(),
        'redis_connection': check_redis_connection(),
        'process_status': check_process_status(),
        'log_files': check_log_files(),
        'recent_errors': get_recent_errors()[-5:],  # Last 5 errors
        'performance_summary': get_performance_summary()[-10:]  # Last 10 performance entries
    }
    
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        print_json_report()
    else:
        print_health_report()
# Monitoring and Debugging System

## Overview

This document describes the comprehensive monitoring and debugging system implemented for the camera streaming application. The system provides real-time monitoring, detailed logging, performance tracking, and easy issue identification.

## Components

### 1. Centralized Monitoring System (`monitoring.py`)

The monitoring system provides:
- **Structured Logging**: Multiple log files with different purposes
- **Performance Tracking**: Automatic timing and metrics collection
- **Issue Tracking**: Categorized issue logging with counters
- **Connection Monitoring**: Real-time Redis and camera connection status
- **System Health**: CPU, memory, and disk usage monitoring

#### Log Files Created:
- `logs/camera_system.log` - Main application log (50MB rotation)
- `logs/errors.log` - Error-only log (10MB rotation)
- `logs/performance.log` - Performance metrics (daily rotation)
- `greencam.log` - Legacy log file (maintained for compatibility)

### 2. Health Check Script (`health_check.py`)

Provides easy system status checking:

```bash
# Basic health report
python3 health_check.py

# JSON format output
python3 health_check.py --json
```

**Checks:**
- System resources (CPU, memory, disk)
- Redis connection status
- Process status (cam1_stream.py, start.py, client.py)
- Log file status and sizes
- Recent errors

### 3. Log Analysis Script (`log_analyzer.py`)

Advanced log analysis and pattern recognition:

```bash
# Analyze all logs
python3 log_analyzer.py

# Analyze specific log file
python3 log_analyzer.py --file logs/errors.log

# Show recent errors only
python3 log_analyzer.py --recent-errors

# JSON output
python3 log_analyzer.py --json

# Custom time range
python3 log_analyzer.py --hours 6
```

**Features:**
- Pattern recognition (errors, warnings, connections, issues)
- Hourly activity distribution
- Error type categorization
- Issue type analysis
- Performance trend analysis

### 4. Graceful Shutdown Handler (`graceful_shutdown.py`)

Ensures proper resource cleanup:
- Signal handling (SIGINT, SIGTERM)
- Cleanup handler registration
- Resource cleanup on shutdown

## Additional Bugs Fixed

### 1. Memory Leaks
- **Thread Management**: Added proper thread cleanup with daemon threads
- **Image Storage**: Added memory cleanup after image writing
- **Queue Operations**: Added timeouts to prevent blocking

### 2. Resource Management
- **Connection Cleanup**: Proper Redis connection cleanup
- **File Handles**: Proper file handle management
- **Thread Safety**: Improved thread synchronization

### 3. Error Handling
- **Queue Timeouts**: Added timeouts to prevent deadlocks
- **Exception Propagation**: Better exception handling and logging
- **Resource Cleanup**: Automatic cleanup on errors

## Monitoring Features

### 1. Real-time Monitoring

#### System Health Metrics:
- CPU usage percentage
- Memory usage and availability
- Disk usage and free space
- Active thread count
- Uptime tracking

#### Connection Status:
- Redis connection health
- Camera connection status
- Pubsub subscription status
- Connection failure tracking

#### Performance Metrics:
- Function execution times
- Operation latencies
- Throughput measurements
- Resource utilization

### 2. Issue Tracking

#### Categorized Issues:
- `redis_connection_failed`
- `camera_connection_failed`
- `function_failure`
- `system_health_check_failed`
- `pickle_error`
- `thread_timeout`

#### Issue Context:
- Timestamp and uptime
- Error details and stack traces
- Related system state
- Issue frequency tracking

### 3. Performance Analysis

#### Metrics Tracked:
- Function execution times
- Redis operation latencies
- Image processing times
- Queue processing rates
- Memory usage patterns

#### Performance Alerts:
- Slow function execution
- High memory usage
- Queue overflow
- Connection timeouts

## Usage Examples

### 1. Quick System Status

```bash
# Check system health
python3 health_check.py

# Check specific components
python3 health_check.py --json | jq '.redis_connection'
python3 health_check.py --json | jq '.process_status'
```

### 2. Error Investigation

```bash
# Find recent errors
python3 log_analyzer.py --recent-errors --hours 2

# Analyze error patterns
python3 log_analyzer.py --file logs/errors.log

# Get error summary
python3 log_analyzer.py --json | jq '.logs/errors.log.error_types'
```

### 3. Performance Analysis

```bash
# Check performance logs
python3 log_analyzer.py --file logs/performance.log

# Get performance summary
python3 log_analyzer.py --json | jq '.logs/performance.log.performance'
```

### 4. Connection Monitoring

```bash
# Check connection status
python3 health_check.py --json | jq '.redis_connection'

# Analyze connection events
python3 log_analyzer.py --json | jq '.logs/camera_system.log.connections'
```

## Log File Structure

### 1. Main Log (`logs/camera_system.log`)
```
2024-01-15 10:30:15,123 - camera_system - INFO - CONNECTION: {"service": "redis", "status": true, "details": {"failures": 0}, "uptime": 3600.5}
2024-01-15 10:30:15,124 - camera_system - WARNING - ISSUE: {"issue_type": "thread_timeout", "message": "Thread timeout in fetch_image", "severity": "WARNING", "count": 1, "uptime": 3600.5, "context": {}}
```

### 2. Error Log (`logs/errors.log`)
```
2024-01-15 10:30:15,123 - camera_system - ERROR - fetch_image:123 - Redis connection failed: Connection refused
2024-01-15 10:30:15,124 - camera_system - ERROR - main:456 - Function fetch_image failed
```

### 3. Performance Log (`logs/performance.log`)
```
2024-01-15 10:30:15,123 - PERF: {"metric": "fetch_image_duration", "value": 0.045, "unit": "seconds", "timestamp": 1705312215.123, "uptime": 3600.5}
2024-01-15 10:30:15,124 - PERF: {"metric": "system_health", "value": {"cpu_percent": 25.5, "memory_percent": 45.2}, "unit": null, "timestamp": 1705312215.124, "uptime": 3600.5}
```

## Configuration

### Monitoring Settings (`config.py`)
```python
# Monitoring Configuration
HEALTH_CHECK_INTERVAL = 60  # seconds
PERFORMANCE_LOG_INTERVAL = 300  # seconds
LOG_ROTATION_SIZE = 50 * 1024 * 1024  # 50MB
ERROR_LOG_ROTATION_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5
```

## Troubleshooting

### 1. High Memory Usage
```bash
# Check memory usage
python3 health_check.py --json | jq '.system_resources.memory_percent'

# Analyze memory patterns
python3 log_analyzer.py --file logs/performance.log | grep memory
```

### 2. Connection Issues
```bash
# Check Redis connection
python3 health_check.py --json | jq '.redis_connection'

# Analyze connection events
python3 log_analyzer.py --recent-errors --hours 1 | grep -i connection
```

### 3. Performance Issues
```bash
# Check performance metrics
python3 log_analyzer.py --file logs/performance.log

# Find slow operations
python3 log_analyzer.py --json | jq '.logs/performance.log.performance' | grep duration
```

### 4. Process Issues
```bash
# Check process status
python3 health_check.py --json | jq '.process_status'

# Find process errors
python3 log_analyzer.py --recent-errors --hours 1 | grep -E "(cam1_stream|start|client)"
```

## Best Practices

### 1. Regular Monitoring
- Run health checks every 5-10 minutes
- Monitor log file sizes
- Check for error patterns
- Track performance trends

### 2. Log Management
- Rotate logs regularly
- Archive old logs
- Monitor disk space
- Set up log alerts

### 3. Issue Response
- Use log analysis for root cause identification
- Monitor issue frequency
- Set up automated alerts
- Document resolution procedures

### 4. Performance Optimization
- Monitor function execution times
- Track resource usage patterns
- Identify bottlenecks
- Optimize based on metrics

## Integration with External Monitoring

The monitoring system can be integrated with external monitoring tools:

### 1. Prometheus Integration
- Export metrics via HTTP endpoint
- Use custom exporters
- Set up alerting rules

### 2. Grafana Dashboards
- Create custom dashboards
- Visualize performance trends
- Set up alerts

### 3. ELK Stack
- Send logs to Elasticsearch
- Use Logstash for processing
- Create Kibana dashboards

### 4. Custom Alerts
- Email notifications
- Slack integration
- SMS alerts
- Webhook notifications
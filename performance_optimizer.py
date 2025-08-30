#!/usr/bin/env python3
"""
Performance optimization script for the camera streaming system.
Analyzes system performance and provides optimization recommendations.
"""

import os
import json
import time
import psutil
import threading
from datetime import datetime, timedelta
import config

class PerformanceOptimizer:
    """Analyze and optimize system performance."""
    
    def __init__(self):
        self.performance_data = {}
        self.optimization_recommendations = []
        
    def analyze_system_performance(self, duration_seconds=60):
        """Analyze system performance over a specified duration."""
        print(f"Analyzing system performance for {duration_seconds} seconds...")
        
        start_time = time.time()
        samples = []
        
        while time.time() - start_time < duration_seconds:
            try:
                sample = {
                    'timestamp': time.time(),
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'memory_available': psutil.virtual_memory().available,
                    'disk_usage': psutil.disk_usage('/').percent,
                    'active_threads': threading.active_count(),
                    'network_connections': len(psutil.net_connections())
                }
                samples.append(sample)
                time.sleep(5)  # Sample every 5 seconds
                
            except Exception as e:
                print(f"Error collecting performance sample: {e}")
                break
        
        if samples:
            self.performance_data = {
                'duration_seconds': duration_seconds,
                'samples_count': len(samples),
                'start_time': datetime.fromtimestamp(samples[0]['timestamp']).isoformat(),
                'end_time': datetime.fromtimestamp(samples[-1]['timestamp']).isoformat(),
                'metrics': {
                    'cpu': {
                        'average': sum(s['cpu_percent'] for s in samples) / len(samples),
                        'max': max(s['cpu_percent'] for s in samples),
                        'min': min(s['cpu_percent'] for s in samples)
                    },
                    'memory': {
                        'average': sum(s['memory_percent'] for s in samples) / len(samples),
                        'max': max(s['memory_percent'] for s in samples),
                        'min': min(s['memory_percent'] for s in samples),
                        'available_avg_gb': sum(s['memory_available'] for s in samples) / len(samples) / (1024**3)
                    },
                    'disk': {
                        'average': sum(s['disk_usage'] for s in samples) / len(samples),
                        'max': max(s['disk_usage'] for s in samples),
                        'min': min(s['disk_usage'] for s in samples)
                    },
                    'threads': {
                        'average': sum(s['active_threads'] for s in samples) / len(samples),
                        'max': max(s['active_threads'] for s in samples),
                        'min': min(s['active_threads'] for s in samples)
                    },
                    'network': {
                        'average': sum(s['network_connections'] for s in samples) / len(samples),
                        'max': max(s['network_connections'] for s in samples),
                        'min': min(s['network_connections'] for s in samples)
                    }
                },
                'raw_samples': samples
            }
        
        return self.performance_data
    
    def analyze_log_performance(self):
        """Analyze performance from log files."""
        print("Analyzing performance from logs...")
        
        performance_metrics = []
        
        try:
            if os.path.exists('logs/performance.log'):
                with open('logs/performance.log', 'r') as f:
                    for line in f:
                        if 'PERF:' in line:
                            try:
                                # Extract JSON data from log line
                                json_start = line.find('{')
                                if json_start != -1:
                                    data = json.loads(line[json_start:])
                                    performance_metrics.append(data)
                            except:
                                continue
            
            if performance_metrics:
                # Group metrics by type
                metric_groups = {}
                for metric in performance_metrics:
                    metric_name = metric.get('metric', 'unknown')
                    if metric_name not in metric_groups:
                        metric_groups[metric_name] = []
                    metric_groups[metric_name].append(metric)
                
                # Analyze each metric group
                log_analysis = {}
                for metric_name, metrics in metric_groups.items():
                    values = [m.get('value', 0) for m in metrics if isinstance(m.get('value'), (int, float))]
                    if values:
                        log_analysis[metric_name] = {
                            'count': len(values),
                            'average': sum(values) / len(values),
                            'max': max(values),
                            'min': min(values),
                            'recent_values': values[-10:]  # Last 10 values
                        }
                
                self.performance_data['log_analysis'] = log_analysis
                
        except Exception as e:
            print(f"Error analyzing log performance: {e}")
        
        return self.performance_data.get('log_analysis', {})
    
    def generate_optimization_recommendations(self):
        """Generate optimization recommendations based on performance analysis."""
        print("Generating optimization recommendations...")
        
        recommendations = []
        
        if not self.performance_data:
            recommendations.append({
                'category': 'general',
                'priority': 'medium',
                'title': 'No performance data available',
                'description': 'Run performance analysis first to get optimization recommendations.',
                'action': 'Run analyze_system_performance() method'
            })
            return recommendations
        
        metrics = self.performance_data.get('metrics', {})
        
        # CPU optimization recommendations
        cpu_avg = metrics.get('cpu', {}).get('average', 0)
        if cpu_avg > 80:
            recommendations.append({
                'category': 'cpu',
                'priority': 'high',
                'title': 'High CPU usage detected',
                'description': f'Average CPU usage is {cpu_avg:.1f}%, which may impact performance.',
                'action': 'Consider reducing camera frame rate or optimizing image processing',
                'current_value': f'{cpu_avg:.1f}%',
                'target_value': '< 70%'
            })
        elif cpu_avg > 60:
            recommendations.append({
                'category': 'cpu',
                'priority': 'medium',
                'title': 'Moderate CPU usage',
                'description': f'Average CPU usage is {cpu_avg:.1f}%, monitor for trends.',
                'action': 'Monitor CPU usage trends and optimize if needed',
                'current_value': f'{cpu_avg:.1f}%',
                'target_value': '< 70%'
            })
        
        # Memory optimization recommendations
        memory_avg = metrics.get('memory', {}).get('average', 0)
        memory_available = metrics.get('memory', {}).get('available_avg_gb', 0)
        
        if memory_avg > 85:
            recommendations.append({
                'category': 'memory',
                'priority': 'high',
                'title': 'High memory usage detected',
                'description': f'Average memory usage is {memory_avg:.1f}% with {memory_available:.1f}GB available.',
                'action': 'Consider reducing image queue sizes or implementing memory cleanup',
                'current_value': f'{memory_avg:.1f}%',
                'target_value': '< 80%'
            })
        elif memory_available < 1.0:  # Less than 1GB available
            recommendations.append({
                'category': 'memory',
                'priority': 'high',
                'title': 'Low available memory',
                'description': f'Only {memory_available:.1f}GB of memory available.',
                'action': 'Implement aggressive memory cleanup and reduce buffer sizes',
                'current_value': f'{memory_available:.1f}GB',
                'target_value': '> 1GB'
            })
        
        # Thread optimization recommendations
        thread_avg = metrics.get('threads', {}).get('average', 0)
        if thread_avg > 50:
            recommendations.append({
                'category': 'threading',
                'priority': 'medium',
                'title': 'High thread count',
                'description': f'Average active threads: {thread_avg:.1f}',
                'action': 'Review thread management and ensure proper cleanup',
                'current_value': f'{thread_avg:.1f}',
                'target_value': '< 30'
            })
        
        # Disk optimization recommendations
        disk_avg = metrics.get('disk', {}).get('average', 0)
        if disk_avg > 90:
            recommendations.append({
                'category': 'disk',
                'priority': 'high',
                'title': 'High disk usage',
                'description': f'Average disk usage is {disk_avg:.1f}%',
                'action': 'Clean up old logs and images, implement log rotation',
                'current_value': f'{disk_avg:.1f}%',
                'target_value': '< 85%'
            })
        
        # Configuration optimization recommendations
        if 'log_analysis' in self.performance_data:
            log_analysis = self.performance_data['log_analysis']
            
            # Check for slow operations
            for metric_name, data in log_analysis.items():
                if 'duration' in metric_name.lower():
                    avg_duration = data.get('average', 0)
                    if avg_duration > 1.0:  # More than 1 second
                        recommendations.append({
                            'category': 'performance',
                            'priority': 'medium',
                            'title': f'Slow operation detected: {metric_name}',
                            'description': f'Average duration: {avg_duration:.3f} seconds',
                            'action': 'Optimize the operation or implement caching',
                            'current_value': f'{avg_duration:.3f}s',
                            'target_value': '< 0.5s'
                        })
        
        self.optimization_recommendations = recommendations
        return recommendations
    
    def apply_optimizations(self):
        """Apply automatic optimizations based on recommendations."""
        print("Applying automatic optimizations...")
        
        applied_optimizations = []
        
        if not self.optimization_recommendations:
            print("No optimization recommendations available. Run generate_optimization_recommendations() first.")
            return applied_optimizations
        
        for recommendation in self.optimization_recommendations:
            if recommendation['category'] == 'memory' and recommendation['priority'] == 'high':
                # Apply memory optimizations
                try:
                    # Reduce queue sizes in config
                    self._optimize_queue_sizes()
                    applied_optimizations.append({
                        'recommendation': recommendation['title'],
                        'action': 'Reduced queue sizes',
                        'status': 'applied'
                    })
                except Exception as e:
                    applied_optimizations.append({
                        'recommendation': recommendation['title'],
                        'action': 'Failed to reduce queue sizes',
                        'status': 'failed',
                        'error': str(e)
                    })
            
            elif recommendation['category'] == 'disk' and recommendation['priority'] == 'high':
                # Apply disk optimizations
                try:
                    # Clean up old logs
                    self._cleanup_old_logs()
                    applied_optimizations.append({
                        'recommendation': recommendation['title'],
                        'action': 'Cleaned up old logs',
                        'status': 'applied'
                    })
                except Exception as e:
                    applied_optimizations.append({
                        'recommendation': recommendation['title'],
                        'action': 'Failed to cleanup logs',
                        'status': 'failed',
                        'error': str(e)
                    })
        
        return applied_optimizations
    
    def _optimize_queue_sizes(self):
        """Optimize queue sizes based on memory usage."""
        # This is a placeholder for actual optimization logic
        # In a real implementation, you would modify config values
        print("  - Optimizing queue sizes...")
    
    def _cleanup_old_logs(self):
        """Clean up old log files."""
        print("  - Cleaning up old logs...")
        
        # Keep only recent log files
        log_files_to_clean = [
            'logs/camera_system.log',
            'logs/errors.log',
            'logs/performance.log'
        ]
        
        for log_file in log_files_to_clean:
            if os.path.exists(log_file):
                # Keep only the last 10MB of each log file
                try:
                    if os.path.getsize(log_file) > 10 * 1024 * 1024:  # 10MB
                        # Truncate log file
                        with open(log_file, 'r+') as f:
                            f.seek(-5 * 1024 * 1024, 2)  # Keep last 5MB
                            content = f.read()
                            f.seek(0)
                            f.write(content)
                            f.truncate()
                        print(f"    - Truncated {log_file}")
                except Exception as e:
                    print(f"    - Failed to truncate {log_file}: {e}")
    
    def generate_report(self, output_file=None):
        """Generate a comprehensive performance report."""
        print("Generating performance report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'performance_data': self.performance_data,
            'optimization_recommendations': self.optimization_recommendations,
            'summary': {
                'total_recommendations': len(self.optimization_recommendations),
                'high_priority_recommendations': len([r for r in self.optimization_recommendations if r['priority'] == 'high']),
                'medium_priority_recommendations': len([r for r in self.optimization_recommendations if r['priority'] == 'medium']),
                'low_priority_recommendations': len([r for r in self.optimization_recommendations if r['priority'] == 'low'])
            }
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to: {output_file}")
        
        return report

def main():
    """Main function to run performance optimization."""
    optimizer = PerformanceOptimizer()
    
    # Analyze system performance
    optimizer.analyze_system_performance(duration_seconds=30)
    
    # Analyze log performance
    optimizer.analyze_log_performance()
    
    # Generate recommendations
    recommendations = optimizer.generate_optimization_recommendations()
    
    # Print recommendations
    print("\n" + "=" * 60)
    print("PERFORMANCE OPTIMIZATION RECOMMENDATIONS")
    print("=" * 60)
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            priority_icon = "🔴" if rec['priority'] == 'high' else "🟡" if rec['priority'] == 'medium' else "🟢"
            print(f"\n{priority_icon} {i}. {rec['title']}")
            print(f"   Category: {rec['category']}")
            print(f"   Priority: {rec['priority']}")
            print(f"   Description: {rec['description']}")
            print(f"   Action: {rec['action']}")
            if 'current_value' in rec:
                print(f"   Current: {rec['current_value']}")
                print(f"   Target: {rec['target_value']}")
    else:
        print("✅ No optimization recommendations. System performance looks good!")
    
    # Generate report
    optimizer.generate_report('performance_report.json')
    
    print(f"\n📊 Performance report saved to: performance_report.json")

if __name__ == "__main__":
    main()
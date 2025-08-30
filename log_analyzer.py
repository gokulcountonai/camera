#!/usr/bin/env python3
"""
Log analysis script for the camera streaming system.
Helps identify patterns, issues, and performance trends in the logs.
"""

import re
import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import argparse

class LogAnalyzer:
    """Analyze log files for patterns and issues."""
    
    def __init__(self):
        self.log_patterns = {
            'error': r'ERROR.*',
            'warning': r'WARNING.*',
            'connection': r'CONNECTION.*',
            'connection_lost': r'CONNECTION_LOST.*',
            'issue': r'ISSUE.*',
            'performance': r'PERF.*',
            'function_success': r'FUNCTION_SUCCESS.*',
            'function_failure': r'FUNCTION_FAILURE.*'
        }
        
    def parse_log_line(self, line):
        """Parse a log line and extract structured data."""
        try:
            # Try to parse JSON data
            if line.startswith('ISSUE:') or line.startswith('PERF:') or line.startswith('CONNECTION:'):
                json_start = line.find('{')
                if json_start != -1:
                    json_data = json.loads(line[json_start:])
                    return {
                        'type': line.split(':')[0],
                        'data': json_data,
                        'raw': line
                    }
            
            # Parse timestamp and message
            timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
            if timestamp_match:
                timestamp = timestamp_match.group(1)
                message = line[len(timestamp):].strip()
                return {
                    'timestamp': timestamp,
                    'message': message,
                    'raw': line
                }
            
            return {'raw': line}
            
        except Exception as e:
            return {'raw': line, 'parse_error': str(e)}
    
    def analyze_log_file(self, log_file, hours_back=24):
        """Analyze a log file for patterns and issues."""
        if not os.path.exists(log_file):
            print(f"Log file not found: {log_file}")
            return None
            
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        analysis = {
            'file': log_file,
            'total_lines': 0,
            'parsed_lines': 0,
            'errors': [],
            'warnings': [],
            'connections': [],
            'issues': [],
            'performance': [],
            'function_calls': [],
            'patterns': defaultdict(int),
            'hourly_distribution': defaultdict(int),
            'error_types': Counter(),
            'issue_types': Counter()
        }
        
        try:
            with open(log_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    analysis['total_lines'] += 1
                    parsed = self.parse_log_line(line)
                    
                    if 'timestamp' in parsed:
                        analysis['parsed_lines'] += 1
                        
                        # Check if within time range
                        try:
                            log_time = datetime.strptime(parsed['timestamp'], '%Y-%m-%d %H:%M:%S,%f')
                            if log_time < cutoff_time:
                                continue
                                
                            hour_key = log_time.strftime('%Y-%m-%d %H:00')
                            analysis['hourly_distribution'][hour_key] += 1
                        except:
                            pass
                    
                    # Categorize by patterns
                    for pattern_name, pattern in self.log_patterns.items():
                        if re.search(pattern, line, re.IGNORECASE):
                            analysis['patterns'][pattern_name] += 1
                            break
                    
                    # Extract specific data
                    if 'ISSUE:' in line:
                        analysis['issues'].append(parsed)
                        if 'data' in parsed and 'issue_type' in parsed['data']:
                            analysis['issue_types'][parsed['data']['issue_type']] += 1
                            
                    elif 'ERROR' in line:
                        analysis['errors'].append(parsed)
                        # Try to extract error type
                        error_match = re.search(r'ERROR.*?(\w+):', line)
                        if error_match:
                            analysis['error_types'][error_match.group(1)] += 1
                            
                    elif 'CONNECTION:' in line or 'CONNECTION_LOST:' in line:
                        analysis['connections'].append(parsed)
                        
                    elif 'PERF:' in line:
                        analysis['performance'].append(parsed)
                        
                    elif 'FUNCTION_SUCCESS:' in line or 'FUNCTION_FAILURE:' in line:
                        analysis['function_calls'].append(parsed)
                        
        except Exception as e:
            print(f"Error analyzing {log_file}: {e}")
            return None
            
        return analysis
    
    def print_analysis_summary(self, analysis):
        """Print a summary of log analysis."""
        if not analysis:
            return
            
        print(f"\n{'='*60}")
        print(f"LOG ANALYSIS: {analysis['file']}")
        print(f"{'='*60}")
        print(f"Total lines: {analysis['total_lines']}")
        print(f"Parsed lines: {analysis['parsed_lines']}")
        print(f"Analysis period: Last 24 hours")
        print()
        
        # Pattern summary
        print("PATTERN SUMMARY:")
        print("-" * 20)
        for pattern, count in sorted(analysis['patterns'].items()):
            print(f"{pattern.upper()}: {count}")
        print()
        
        # Error summary
        if analysis['errors']:
            print("ERROR SUMMARY:")
            print("-" * 20)
            print(f"Total errors: {len(analysis['errors'])}")
            if analysis['error_types']:
                print("Error types:")
                for error_type, count in analysis['error_types'].most_common(5):
                    print(f"  {error_type}: {count}")
            print()
        
        # Issue summary
        if analysis['issues']:
            print("ISSUE SUMMARY:")
            print("-" * 20)
            print(f"Total issues: {len(analysis['issues'])}")
            if analysis['issue_types']:
                print("Issue types:")
                for issue_type, count in analysis['issue_types'].most_common(5):
                    print(f"  {issue_type}: {count}")
            print()
        
        # Connection summary
        if analysis['connections']:
            print("CONNECTION SUMMARY:")
            print("-" * 20)
            connection_events = len(analysis['connections'])
            connection_lost = sum(1 for c in analysis['connections'] if 'CONNECTION_LOST' in c.get('raw', ''))
            connection_restored = connection_events - connection_lost
            print(f"Connection events: {connection_events}")
            print(f"Connection lost: {connection_lost}")
            print(f"Connection restored: {connection_restored}")
            print()
        
        # Performance summary
        if analysis['performance']:
            print("PERFORMANCE SUMMARY:")
            print("-" * 20)
            print(f"Performance metrics logged: {len(analysis['performance'])}")
            print()
        
        # Hourly distribution
        if analysis['hourly_distribution']:
            print("HOURLY ACTIVITY:")
            print("-" * 20)
            for hour, count in sorted(analysis['hourly_distribution'].items())[-6:]:  # Last 6 hours
                print(f"{hour}: {count} events")
            print()
    
    def find_recent_errors(self, log_file, hours_back=1):
        """Find recent errors in the log file."""
        if not os.path.exists(log_file):
            return []
            
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_errors = []
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if 'ERROR' in line:
                        timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
                        if timestamp_match:
                            try:
                                log_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S,%f')
                                if log_time >= cutoff_time:
                                    recent_errors.append(line.strip())
                            except:
                                recent_errors.append(line.strip())
        except Exception as e:
            print(f"Error reading log file: {e}")
            
        return recent_errors
    
    def analyze_all_logs(self, hours_back=24):
        """Analyze all log files."""
        log_files = [
            'logs/camera_system.log',
            'logs/errors.log',
            'logs/performance.log',
            'greencam.log'
        ]
        
        all_analyses = {}
        for log_file in log_files:
            if os.path.exists(log_file):
                analysis = self.analyze_log_file(log_file, hours_back)
                if analysis:
                    all_analyses[log_file] = analysis
                    self.print_analysis_summary(analysis)
        
        return all_analyses

def main():
    parser = argparse.ArgumentParser(description='Analyze camera system logs')
    parser.add_argument('--file', help='Specific log file to analyze')
    parser.add_argument('--hours', type=int, default=24, help='Hours back to analyze (default: 24)')
    parser.add_argument('--recent-errors', action='store_true', help='Show recent errors only')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    analyzer = LogAnalyzer()
    
    if args.recent_errors:
        log_file = args.file or 'logs/errors.log'
        errors = analyzer.find_recent_errors(log_file, args.hours)
        if args.json:
            print(json.dumps({'recent_errors': errors}, indent=2))
        else:
            print(f"Recent errors in {log_file} (last {args.hours} hours):")
            for error in errors:
                print(error)
    elif args.file:
        analysis = analyzer.analyze_log_file(args.file, args.hours)
        if args.json:
            print(json.dumps(analysis, indent=2))
        else:
            analyzer.print_analysis_summary(analysis)
    else:
        analyses = analyzer.analyze_all_logs(args.hours)
        if args.json:
            print(json.dumps(analyses, indent=2))

if __name__ == "__main__":
    main()
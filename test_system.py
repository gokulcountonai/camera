#!/usr/bin/env python3
"""
Automated testing script for the camera streaming system.
Tests various components and provides a comprehensive test report.
"""

import time
import json
import subprocess
import sys
import os
from datetime import datetime
import config

class SystemTester:
    """Test various components of the camera streaming system."""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
    def test_imports(self):
        """Test if all required modules can be imported."""
        print("Testing module imports...")
        
        modules_to_test = [
            'cv2',
            'redis',
            'pickle',
            'threading',
            'queue',
            'logging',
            'psutil'
        ]
        
        results = {}
        for module in modules_to_test:
            try:
                __import__(module)
                results[module] = {'status': 'PASS', 'error': None}
                print(f"  ✅ {module}")
            except ImportError as e:
                results[module] = {'status': 'FAIL', 'error': str(e)}
                print(f"  ❌ {module}: {e}")
        
        self.test_results['imports'] = results
        return all(r['status'] == 'PASS' for r in results.values())
    
    def test_config(self):
        """Test configuration file."""
        print("Testing configuration...")
        
        try:
            import config
            required_configs = [
                'REDIS_HOST', 'REDIS_PORT', 'REDIS_DB',
                'REQUEST_TOPIC_GREENCAM1', 'STREAM_TOPIC_GREENCAM1',
                'CAMERA_WIDTH', 'CAMERA_HEIGHT', 'LOG_FILE'
            ]
            
            results = {}
            for config_name in required_configs:
                if hasattr(config, config_name):
                    results[config_name] = {'status': 'PASS', 'value': getattr(config, config_name)}
                    print(f"  ✅ {config_name}: {getattr(config, config_name)}")
                else:
                    results[config_name] = {'status': 'FAIL', 'error': 'Missing'}
                    print(f"  ❌ {config_name}: Missing")
            
            self.test_results['config'] = results
            return all(r['status'] == 'PASS' for r in results.values())
            
        except Exception as e:
            print(f"  ❌ Configuration test failed: {e}")
            self.test_results['config'] = {'status': 'FAIL', 'error': str(e)}
            return False
    
    def test_redis_connection(self):
        """Test Redis connection."""
        print("Testing Redis connection...")
        
        try:
            import redis
            import config
            client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB, socket_timeout=5)
            ping_result = client.ping()
            client.close()
            
            if ping_result:
                print(f"  ✅ Redis connection to {config.REDIS_HOST}:{config.REDIS_PORT}")
                self.test_results['redis'] = {'status': 'PASS', 'host': config.REDIS_HOST, 'port': config.REDIS_PORT}
                return True
            else:
                print(f"  ❌ Redis ping failed")
                self.test_results['redis'] = {'status': 'FAIL', 'error': 'Ping failed'}
                return False
                
        except Exception as e:
            print(f"  ❌ Redis connection failed: {e}")
            self.test_results['redis'] = {'status': 'FAIL', 'error': str(e)}
            return False
    
    def test_file_permissions(self):
        """Test file permissions and accessibility."""
        print("Testing file permissions...")
        
        files_to_test = [
            'cam1_stream.py',
            'start.py',
            'client.py',
            'src/sendData.py',
            'storeimages.py',
            'config.py',
            'run.sh'
        ]
        
        results = {}
        for file_path in files_to_test:
            try:
                if os.path.exists(file_path):
                    # Test if file is readable
                    with open(file_path, 'r') as f:
                        f.read(1)
                    
                    # Test if file is executable (for .sh files)
                    if file_path.endswith('.sh'):
                        if os.access(file_path, os.X_OK):
                            results[file_path] = {'status': 'PASS', 'permissions': 'readable, executable'}
                            print(f"  ✅ {file_path}: readable, executable")
                        else:
                            results[file_path] = {'status': 'FAIL', 'error': 'Not executable'}
                            print(f"  ❌ {file_path}: not executable")
                    else:
                        results[file_path] = {'status': 'PASS', 'permissions': 'readable'}
                        print(f"  ✅ {file_path}: readable")
                else:
                    results[file_path] = {'status': 'FAIL', 'error': 'File not found'}
                    print(f"  ❌ {file_path}: not found")
                    
            except Exception as e:
                results[file_path] = {'status': 'FAIL', 'error': str(e)}
                print(f"  ❌ {file_path}: {e}")
        
        self.test_results['file_permissions'] = results
        return all(r['status'] == 'PASS' for r in results.values())
    
    def test_directory_structure(self):
        """Test directory structure and create missing directories."""
        print("Testing directory structure...")
        
        directories = [
            'logs',
            'images',
            'src'
        ]
        
        results = {}
        for directory in directories:
            try:
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    print(f"  ✅ Created directory: {directory}")
                else:
                    print(f"  ✅ Directory exists: {directory}")
                
                # Test if directory is writable
                test_file = os.path.join(directory, '.test_write')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                
                results[directory] = {'status': 'PASS', 'writable': True}
                
            except Exception as e:
                results[directory] = {'status': 'FAIL', 'error': str(e)}
                print(f"  ❌ {directory}: {e}")
        
        self.test_results['directory_structure'] = results
        return all(r['status'] == 'PASS' for r in results.values())
    
    def test_syntax(self):
        """Test Python syntax of all Python files."""
        print("Testing Python syntax...")
        
        python_files = [
            'cam1_stream.py',
            'start.py',
            'client.py',
            'src/sendData.py',
            'storeimages.py',
            'config.py',
            'monitoring.py',
            'health_check.py',
            'log_analyzer.py',
            'graceful_shutdown.py'
        ]
        
        results = {}
        for file_path in python_files:
            try:
                if os.path.exists(file_path):
                    result = subprocess.run([sys.executable, '-m', 'py_compile', file_path], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        results[file_path] = {'status': 'PASS'}
                        print(f"  ✅ {file_path}")
                    else:
                        results[file_path] = {'status': 'FAIL', 'error': result.stderr}
                        print(f"  ❌ {file_path}: {result.stderr}")
                else:
                    results[file_path] = {'status': 'FAIL', 'error': 'File not found'}
                    print(f"  ❌ {file_path}: not found")
                    
            except Exception as e:
                results[file_path] = {'status': 'FAIL', 'error': str(e)}
                print(f"  ❌ {file_path}: {e}")
        
        self.test_results['syntax'] = results
        return all(r['status'] == 'PASS' for r in results.values())
    
    def test_monitoring_tools(self):
        """Test monitoring tools."""
        print("Testing monitoring tools...")
        
        results = {}
        
        # Test health check script
        try:
            result = subprocess.run([sys.executable, 'health_check.py', '--json'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                results['health_check'] = {'status': 'PASS'}
                print("  ✅ health_check.py")
            else:
                results['health_check'] = {'status': 'FAIL', 'error': result.stderr}
                print(f"  ❌ health_check.py: {result.stderr}")
        except subprocess.TimeoutExpired:
            results['health_check'] = {'status': 'FAIL', 'error': 'Timeout'}
            print("  ❌ health_check.py: timeout")
        except Exception as e:
            results['health_check'] = {'status': 'FAIL', 'error': str(e)}
            print(f"  ❌ health_check.py: {e}")
        
        # Test log analyzer script
        try:
            result = subprocess.run([sys.executable, 'log_analyzer.py', '--recent-errors'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                results['log_analyzer'] = {'status': 'PASS'}
                print("  ✅ log_analyzer.py")
            else:
                results['log_analyzer'] = {'status': 'FAIL', 'error': result.stderr}
                print(f"  ❌ log_analyzer.py: {result.stderr}")
        except subprocess.TimeoutExpired:
            results['log_analyzer'] = {'status': 'FAIL', 'error': 'Timeout'}
            print("  ❌ log_analyzer.py: timeout")
        except Exception as e:
            results['log_analyzer'] = {'status': 'FAIL', 'error': str(e)}
            print(f"  ❌ log_analyzer.py: {e}")
        
        self.test_results['monitoring_tools'] = results
        return all(r['status'] == 'PASS' for r in results.values())
    
    def run_all_tests(self):
        """Run all tests and generate report."""
        print("=" * 60)
        print("CAMERA STREAMING SYSTEM TEST SUITE")
        print("=" * 60)
        print(f"Test started at: {datetime.now().isoformat()}")
        print()
        
        tests = [
            ('Module Imports', self.test_imports),
            ('Configuration', self.test_config),
            ('Redis Connection', self.test_redis_connection),
            ('File Permissions', self.test_file_permissions),
            ('Directory Structure', self.test_directory_structure),
            ('Python Syntax', self.test_syntax),
            ('Monitoring Tools', self.test_monitoring_tools)
        ]
        
        overall_results = {}
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            print("-" * len(test_name))
            try:
                result = test_func()
                overall_results[test_name] = {'status': 'PASS' if result else 'FAIL'}
            except Exception as e:
                print(f"  ❌ Test failed with exception: {e}")
                overall_results[test_name] = {'status': 'FAIL', 'error': str(e)}
        
        # Generate summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in overall_results.values() if r['status'] == 'PASS')
        total = len(overall_results)
        
        for test_name, result in overall_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_icon} {test_name}: {result['status']}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! System is ready.")
        else:
            print("⚠️  Some tests failed. Please review the results above.")
        
        # Save detailed results
        self.test_results['summary'] = {
            'total_tests': total,
            'passed_tests': passed,
            'failed_tests': total - passed,
            'test_duration': time.time() - self.start_time,
            'timestamp': datetime.now().isoformat()
        }
        
        with open('test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\nDetailed results saved to: test_results.json")
        return passed == total

def main():
    """Main function to run the test suite."""
    tester = SystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
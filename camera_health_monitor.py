#!/usr/bin/env python3
"""
Standalone Camera Health Monitor
Monitors camera health and provides detailed status reports.
Can be run independently to check camera status.
"""

import time
import json
import argparse
import sys
from datetime import datetime
from camera_manager import get_camera_manager, reset_camera_manager

def print_camera_status(status, detailed=False):
    """Print camera status in a readable format."""
    print("=" * 60)
    print("CAMERA HEALTH STATUS")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Basic status
    print("📷 BASIC STATUS:")
    print("-" * 20)
    print(f"Initialized: {'✅' if status['is_initialized'] else '❌'}")
    print(f"Capturing: {'✅' if status['is_capturing'] else '❌'}")
    print(f"Recovery in Progress: {'⚠️' if status['recovery_in_progress'] else '✅'}")
    print(f"Should Reboot: {'🔴' if status['should_reboot'] else '✅'}")
    print()
    
    # Camera state
    camera_state = status['camera_state']
    print("📊 CAMERA STATE:")
    print("-" * 20)
    print(f"Total Frames Captured: {camera_state['total_frames_captured']}")
    print(f"Total Frames Failed: {camera_state['total_frames_failed']}")
    print(f"Last Frame Age: {status['last_frame_age']:.1f} seconds")
    print()
    
    # Health status
    health = status['health_status']
    print("🏥 HEALTH STATUS:")
    print("-" * 20)
    print(f"Health Score: {health['health_score']}/100")
    print(f"Consecutive Failures: {health['consecutive_failures']}")
    print(f"Recovery Attempts: {health['recovery_attempts']}")
    print(f"Total Camera Errors: {health['total_camera_errors']}")
    print(f"Total Buffer Errors: {health['total_buffer_errors']}")
    print(f"Total Connection Errors: {health['total_connection_errors']}")
    print(f"Uptime Since Last Success: {health['uptime_since_last_success']:.1f} seconds")
    print()
    
    if detailed:
        print("🔍 DETAILED INFORMATION:")
        print("-" * 20)
        print(f"Last Successful Capture: {datetime.fromtimestamp(health['last_successful_capture']).isoformat()}")
        print(f"Camera State: {json.dumps(camera_state, indent=2)}")
        print(f"Health Status: {json.dumps(health, indent=2)}")

def test_camera_capture(camera_manager, num_tests=5):
    """Test camera capture functionality."""
    print(f"🧪 Testing camera capture ({num_tests} attempts)...")
    print("-" * 40)
    
    successful_captures = 0
    failed_captures = 0
    capture_times = []
    
    for i in range(num_tests):
        print(f"Test {i+1}/{num_tests}: ", end="")
        
        start_time = time.time()
        success, frame = camera_manager.capture_frame_with_timeout(timeout=10)
        capture_time = time.time() - start_time
        
        if success and frame is not None:
            print(f"✅ Success ({capture_time:.3f}s)")
            successful_captures += 1
            capture_times.append(capture_time)
        else:
            print(f"❌ Failed ({capture_time:.3f}s)")
            failed_captures += 1
        
        time.sleep(0.5)  # Brief pause between tests
    
    print()
    print("📈 CAPTURE TEST RESULTS:")
    print("-" * 30)
    print(f"Successful Captures: {successful_captures}/{num_tests}")
    print(f"Failed Captures: {failed_captures}/{num_tests}")
    print(f"Success Rate: {(successful_captures/num_tests)*100:.1f}%")
    
    if capture_times:
        avg_time = sum(capture_times) / len(capture_times)
        min_time = min(capture_times)
        max_time = max(capture_times)
        print(f"Average Capture Time: {avg_time:.3f}s")
        print(f"Min Capture Time: {min_time:.3f}s")
        print(f"Max Capture Time: {max_time:.3f}s")
    
    return successful_captures > 0

def attempt_camera_recovery(camera_manager):
    """Attempt camera recovery and report results."""
    print("🔄 Attempting camera recovery...")
    print("-" * 40)
    
    initial_status = camera_manager.get_camera_status()
    print(f"Initial consecutive failures: {initial_status['health_status']['consecutive_failures']}")
    
    # Attempt recovery
    success = camera_manager.attempt_camera_recovery()
    
    # Check status after recovery
    final_status = camera_manager.get_camera_status()
    print(f"Final consecutive failures: {final_status['health_status']['consecutive_failures']}")
    
    if success:
        print("✅ Camera recovery successful!")
    else:
        print("❌ Camera recovery failed!")
    
    return success

def monitor_camera_continuously(camera_manager, duration_minutes=5, interval_seconds=10):
    """Monitor camera continuously for a specified duration."""
    print(f"📺 Continuous monitoring for {duration_minutes} minutes (checking every {interval_seconds}s)...")
    print("-" * 60)
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    check_count = 0
    
    while time.time() < end_time:
        check_count += 1
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Get status
        status = camera_manager.get_camera_status()
        health = status['health_status']
        
        # Print status line
        status_icon = "✅" if status['is_capturing'] else "❌"
        health_icon = "🟢" if health['health_score'] > 70 else "🟡" if health['health_score'] > 30 else "🔴"
        
        print(f"[{current_time}] Check {check_count}: {status_icon} Capturing | {health_icon} Health: {health['health_score']} | Failures: {health['consecutive_failures']} | Last Frame: {status['last_frame_age']:.1f}s")
        
        # Check if recovery is needed
        if camera_manager.health_monitor.should_attempt_recovery():
            print(f"[{current_time}] ⚠️  Recovery needed - attempting...")
            recovery_success = camera_manager.attempt_camera_recovery()
            if recovery_success:
                print(f"[{current_time}] ✅ Recovery successful")
            else:
                print(f"[{current_time}] ❌ Recovery failed")
        
        # Check if reboot is needed
        if status['should_reboot']:
            print(f"[{current_time}] 🔴 SYSTEM REBOOT NEEDED!")
            break
        
        time.sleep(interval_seconds)
    
    print(f"\n📊 Monitoring completed. Total checks: {check_count}")

def main():
    parser = argparse.ArgumentParser(description='Camera Health Monitor')
    parser.add_argument('--status', action='store_true', help='Show current camera status')
    parser.add_argument('--detailed', action='store_true', help='Show detailed status information')
    parser.add_argument('--test', action='store_true', help='Test camera capture functionality')
    parser.add_argument('--recover', action='store_true', help='Attempt camera recovery')
    parser.add_argument('--monitor', action='store_true', help='Monitor camera continuously')
    parser.add_argument('--duration', type=int, default=5, help='Monitoring duration in minutes (default: 5)')
    parser.add_argument('--interval', type=int, default=10, help='Monitoring interval in seconds (default: 10)')
    parser.add_argument('--json', action='store_true', help='Output status in JSON format')
    parser.add_argument('--reset', action='store_true', help='Reset camera manager (useful for testing)')
    
    args = parser.parse_args()
    
    try:
        # Reset camera manager if requested
        if args.reset:
            print("🔄 Resetting camera manager...")
            reset_camera_manager()
        
        # Get camera manager
        camera_manager = get_camera_manager()
        
        # Get current status
        status = camera_manager.get_camera_status()
        
        # JSON output
        if args.json:
            print(json.dumps(status, indent=2))
            return
        
        # Show status
        if args.status or not any([args.test, args.recover, args.monitor]):
            print_camera_status(status, args.detailed)
        
        # Test camera
        if args.test:
            print()
            test_camera_capture(camera_manager)
        
        # Attempt recovery
        if args.recover:
            print()
            attempt_camera_recovery(camera_manager)
        
        # Monitor continuously
        if args.monitor:
            print()
            monitor_camera_continuously(camera_manager, args.duration, args.interval)
        
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
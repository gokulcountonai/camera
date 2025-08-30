#!/usr/bin/env python3
"""
Robust Camera Manager for handling camera disconnection, buffer issues, and automatic recovery.
Provides comprehensive camera health monitoring and automatic recovery mechanisms.
"""

import time
import threading
import logging
import traceback
import os
from datetime import datetime, timedelta
from collections import deque
import cv2
import numpy as np
from picamera2 import Picamera2
from config import *

class CameraHealthMonitor:
    """Monitor camera health and detect issues."""
    
    def __init__(self):
        self.issue_history = deque(maxlen=100)  # Keep last 100 issues
        self.last_successful_capture = time.time()
        self.consecutive_failures = 0
        self.camera_errors = 0
        self.buffer_errors = 0
        self.connection_errors = 0
        self.recovery_attempts = 0
        
    def log_issue(self, issue_type, error_msg, severity='WARNING'):
        """Log a camera issue."""
        issue = {
            'timestamp': time.time(),
            'type': issue_type,
            'message': error_msg,
            'severity': severity,
            'consecutive_failures': self.consecutive_failures
        }
        self.issue_history.append(issue)
        
        if issue_type == 'capture_failure':
            self.consecutive_failures += 1
        elif issue_type == 'camera_error':
            self.camera_errors += 1
        elif issue_type == 'buffer_error':
            self.buffer_errors += 1
        elif issue_type == 'connection_error':
            self.connection_errors += 1
            
        logging.warning(f"CAMERA_ISSUE: {issue_type} - {error_msg} (Failures: {self.consecutive_failures})")
    
    def log_success(self):
        """Log successful capture."""
        self.last_successful_capture = time.time()
        if self.consecutive_failures > 0:
            logging.info(f"CAMERA_RECOVERY: Successful capture after {self.consecutive_failures} failures")
        self.consecutive_failures = 0
    
    def should_attempt_recovery(self):
        """Determine if recovery should be attempted."""
        # Attempt recovery after 3 consecutive failures
        if self.consecutive_failures >= 3:
            return True
        
        # Attempt recovery if no successful capture in 30 seconds
        if time.time() - self.last_successful_capture > 30:
            return True
            
        return False
    
    def should_reboot_system(self):
        """Determine if system reboot is needed."""
        # Reboot after 10 consecutive failures
        if self.consecutive_failures >= 10:
            return True
        
        # Reboot if multiple recovery attempts failed
        if self.recovery_attempts >= 5:
            return True
            
        return False
    
    def get_health_status(self):
        """Get current camera health status."""
        return {
            'last_successful_capture': self.last_successful_capture,
            'consecutive_failures': self.consecutive_failures,
            'total_camera_errors': self.camera_errors,
            'total_buffer_errors': self.buffer_errors,
            'total_connection_errors': self.connection_errors,
            'recovery_attempts': self.recovery_attempts,
            'uptime_since_last_success': time.time() - self.last_successful_capture,
            'health_score': max(0, 100 - (self.consecutive_failures * 10))
        }

class RobustCameraManager:
    """Robust camera manager with automatic recovery capabilities."""
    
    def __init__(self, camera_config=None):
        self.camera = None
        self.camera_config = camera_config or {
            'width': CAMERA_WIDTH,
            'height': CAMERA_HEIGHT,
            'format': CAMERA_FORMAT,
            'exposure_time': EXPOSURE_TIME,
            'analogue_gain': ANALOGUE_GAIN,
            'frame_rate': FRAME_RATE
        }
        self.health_monitor = CameraHealthMonitor()
        self.camera_lock = threading.Lock()
        self.is_initialized = False
        self.last_frame_time = 0
        self.frame_timeout = 5.0  # 5 seconds timeout for frame capture
        self.recovery_in_progress = False
        
        # Camera state tracking
        self.camera_state = {
            'initialized': False,
            'started': False,
            'capturing': False,
            'last_frame_timestamp': 0,
            'total_frames_captured': 0,
            'total_frames_failed': 0
        }
        
        # Initialize camera
        self.initialize_camera()
    
    def initialize_camera(self):
        """Initialize the camera with error handling."""
        try:
            with self.camera_lock:
                if self.camera:
                    self._cleanup_camera()
                
                logging.info("Initializing camera...")
                self.camera = Picamera2()
                
                # Create configuration
                config = self.camera.create_preview_configuration(
                    queue=False,
                    main={
                        "size": (self.camera_config['width'], self.camera_config['height']),
                        "format": self.camera_config['format']
                    }
                )
                self.camera.configure(config)
                
                # Set camera controls
                self.camera.set_controls({
                    "ExposureTime": self.camera_config['exposure_time'],
                    "AnalogueGain": self.camera_config['analogue_gain'],
                    "FrameRate": self.camera_config['frame_rate']
                })
                
                self.is_initialized = True
                self.camera_state['initialized'] = True
                logging.info("Camera initialized successfully")
                
        except Exception as e:
            error_msg = f"Failed to initialize camera: {str(e)}"
            logging.error(error_msg)
            self.health_monitor.log_issue('camera_error', error_msg, 'ERROR')
            self.is_initialized = False
            self.camera_state['initialized'] = False
            raise
    
    def start_camera(self):
        """Start the camera with error handling."""
        try:
            with self.camera_lock:
                if not self.is_initialized:
                    self.initialize_camera()
                
                if not self.camera_state['started']:
                    logging.info("Starting camera...")
                    self.camera.start()
                    self.camera_state['started'] = True
                    self.camera_state['capturing'] = True
                    logging.info("Camera started successfully")
                    
        except Exception as e:
            error_msg = f"Failed to start camera: {str(e)}"
            logging.error(error_msg)
            self.health_monitor.log_issue('camera_error', error_msg, 'ERROR')
            self.camera_state['started'] = False
            self.camera_state['capturing'] = False
            raise
    
    def stop_camera(self):
        """Stop the camera safely."""
        try:
            with self.camera_lock:
                if self.camera and self.camera_state['started']:
                    logging.info("Stopping camera...")
                    self.camera.stop()
                    self.camera_state['started'] = False
                    self.camera_state['capturing'] = False
                    logging.info("Camera stopped successfully")
                    
        except Exception as e:
            logging.error(f"Error stopping camera: {str(e)}")
    
    def _cleanup_camera(self):
        """Clean up camera resources."""
        try:
            if self.camera:
                if self.camera_state['started']:
                    self.camera.stop()
                self.camera.close()
                self.camera = None
                self.is_initialized = False
                self.camera_state = {
                    'initialized': False,
                    'started': False,
                    'capturing': False,
                    'last_frame_timestamp': 0,
                    'total_frames_captured': 0,
                    'total_frames_failed': 0
                }
        except Exception as e:
            logging.error(f"Error cleaning up camera: {str(e)}")
    
    def capture_frame_with_timeout(self, timeout=None):
        """Capture a frame with timeout and error handling."""
        if timeout is None:
            timeout = self.frame_timeout
            
        try:
            with self.camera_lock:
                if not self.is_initialized or not self.camera_state['started']:
                    raise Exception("Camera not ready")
                
                # Check if camera is responsive
                if time.time() - self.last_frame_time > 30:  # No frame for 30 seconds
                    self.health_monitor.log_issue('connection_error', 'Camera appears unresponsive', 'WARNING')
                
                # Attempt to capture frame
                start_time = time.time()
                frame = self.camera.capture_array("main")
                capture_time = time.time() - start_time
                
                # Validate frame
                if frame is None or frame.size == 0:
                    raise Exception("Captured frame is empty or None")
                
                # Check frame dimensions
                expected_shape = (self.camera_config['height'], self.camera_config['width'], 3)
                if frame.shape != expected_shape:
                    raise Exception(f"Frame shape mismatch: expected {expected_shape}, got {frame.shape}")
                
                # Update statistics
                self.last_frame_time = time.time()
                self.camera_state['last_frame_timestamp'] = self.last_frame_time
                self.camera_state['total_frames_captured'] += 1
                
                # Log success
                self.health_monitor.log_success()
                
                if capture_time > 1.0:  # Log slow captures
                    logging.warning(f"Slow frame capture: {capture_time:.3f}s")
                
                return True, frame
                
        except Exception as e:
            error_msg = f"Frame capture failed: {str(e)}"
            logging.error(error_msg)
            self.health_monitor.log_issue('capture_failure', error_msg, 'WARNING')
            self.camera_state['total_frames_failed'] += 1
            
            # Check if this is a buffer-related error
            if 'buffer' in str(e).lower() or 'timeout' in str(e).lower():
                self.health_monitor.log_issue('buffer_error', f"Buffer issue detected: {str(e)}", 'WARNING')
            
            return False, None
    
    def attempt_camera_recovery(self):
        """Attempt to recover camera functionality."""
        if self.recovery_in_progress:
            logging.info("Camera recovery already in progress")
            return False
            
        self.recovery_in_progress = True
        self.health_monitor.recovery_attempts += 1
        
        try:
            logging.info(f"Attempting camera recovery (attempt {self.health_monitor.recovery_attempts})")
            
            # Step 1: Stop camera
            self.stop_camera()
            time.sleep(2)  # Wait for camera to fully stop
            
            # Step 2: Clean up resources
            self._cleanup_camera()
            time.sleep(1)
            
            # Step 3: Reinitialize camera
            self.initialize_camera()
            time.sleep(1)
            
            # Step 4: Start camera
            self.start_camera()
            time.sleep(2)  # Wait for camera to stabilize
            
            # Step 5: Test capture
            success, frame = self.capture_frame_with_timeout(timeout=10)
            
            if success:
                logging.info("Camera recovery successful")
                self.health_monitor.recovery_attempts = 0  # Reset recovery attempts
                return True
            else:
                logging.error("Camera recovery failed - test capture unsuccessful")
                return False
                
        except Exception as e:
            logging.error(f"Camera recovery failed: {str(e)}")
            return False
        finally:
            self.recovery_in_progress = False
    
    def force_system_reboot(self):
        """Force system reboot when all recovery attempts fail."""
        try:
            logging.critical("All camera recovery attempts failed. Forcing system reboot...")
            
            # Send reboot signal via kill file
            with open(KILL_FILE, "r+") as f:
                content = f.read().strip()
                if content == "0":
                    f.seek(0)
                    f.write("1")
                    f.truncate()
            
            # Wait a moment for the signal to be processed
            time.sleep(5)
            
            # If still running, force reboot
            logging.critical("Executing system reboot...")
            os.system(REBOOT_COMMAND)
            
        except Exception as e:
            logging.error(f"Failed to initiate system reboot: {str(e)}")
    
    def get_camera_status(self):
        """Get comprehensive camera status."""
        return {
            'camera_state': self.camera_state.copy(),
            'health_status': self.health_monitor.get_health_status(),
            'is_initialized': self.is_initialized,
            'is_capturing': self.camera_state['capturing'],
            'last_frame_age': time.time() - self.last_frame_time,
            'recovery_in_progress': self.recovery_in_progress,
            'should_reboot': self.health_monitor.should_reboot_system()
        }
    
    def monitor_and_recover(self):
        """Monitor camera health and attempt recovery if needed."""
        status = self.get_camera_status()
        
        # Check if recovery is needed
        if self.health_monitor.should_attempt_recovery():
            logging.warning("Camera recovery needed - attempting recovery...")
            if not self.attempt_camera_recovery():
                logging.error("Camera recovery failed")
                
                # Check if system reboot is needed
                if self.health_monitor.should_reboot_system():
                    logging.critical("Maximum recovery attempts reached - initiating system reboot")
                    self.force_system_reboot()
        
        return status
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self._cleanup_camera()
        except:
            pass

# Global camera manager instance
camera_manager = None

def get_camera_manager():
    """Get or create the global camera manager instance."""
    global camera_manager
    if camera_manager is None:
        camera_manager = RobustCameraManager()
    return camera_manager

def reset_camera_manager():
    """Reset the global camera manager (useful for testing)."""
    global camera_manager
    if camera_manager:
        camera_manager._cleanup_camera()
    camera_manager = None
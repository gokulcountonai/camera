"""
Graceful shutdown handler for the camera streaming application.
Ensures proper cleanup of resources when the application is terminated.
"""

import signal
import sys
import threading
import time
import logging
from monitoring import system_monitor

class GracefulShutdown:
    """Handle graceful shutdown of the application."""
    
    def __init__(self):
        self.shutdown_event = threading.Event()
        self.cleanup_handlers = []
        self.setup_signal_handlers()
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        system_monitor.logger.info(f"Received shutdown signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()
        
    def add_cleanup_handler(self, handler_func, name="unknown"):
        """Add a cleanup handler function."""
        self.cleanup_handlers.append((handler_func, name))
        
    def cleanup(self):
        """Execute all cleanup handlers."""
        system_monitor.logger.info("Starting cleanup process...")
        
        for handler_func, name in self.cleanup_handlers:
            try:
                system_monitor.logger.info(f"Executing cleanup handler: {name}")
                handler_func()
                system_monitor.logger.info(f"Cleanup handler {name} completed successfully")
            except Exception as e:
                system_monitor.logger.error(f"Error in cleanup handler {name}: {e}")
                
        system_monitor.logger.info("Cleanup process completed")
        
    def wait_for_shutdown(self, timeout=None):
        """Wait for shutdown signal."""
        try:
            self.shutdown_event.wait(timeout)
            return True
        except KeyboardInterrupt:
            return True
            
    def is_shutdown_requested(self):
        """Check if shutdown has been requested."""
        return self.shutdown_event.is_set()

# Global shutdown handler
shutdown_handler = GracefulShutdown()

def register_cleanup_handler(handler_func, name="unknown"):
    """Register a cleanup handler function."""
    shutdown_handler.add_cleanup_handler(handler_func, name)
    
def is_shutdown_requested():
    """Check if shutdown has been requested."""
    return shutdown_handler.is_shutdown_requested()
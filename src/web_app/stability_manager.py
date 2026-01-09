"""
Web Application Stability Improvements

This file contains patches and improvements for the Flask web application
to prevent crashes and improve stability.
"""

import logging
import psutil
import gc
import threading
import time
from functools import wraps
from flask import request

logger = logging.getLogger(__name__)

class WebStabilityManager:
    """
    Manages web application stability through enhanced error handling,
    memory management, and request monitoring.
    """
    
    def __init__(self, app, max_memory_mb=1024):
        self.app = app
        self.max_memory_mb = max_memory_mb
        self.request_count = 0
        self.active_requests = 0
        self.max_concurrent_requests = 10
        self._monitoring_thread = None
        self._shutdown_flag = threading.Event()
        
        # Apply stability improvements
        self._setup_error_handlers()
        self._setup_memory_monitoring()
        self._setup_request_limiting()
        
    def _setup_error_handlers(self):
        """Setup comprehensive error handling"""
        
        @self.app.errorhandler(500)
        def handle_internal_error(error):
            logger.error(f"Internal server error: {error}")
            gc.collect()  # Force garbage collection on errors
            return {
                'status': 'error',
                'message': 'Internal server error',
                'timestamp': time.time()
            }, 500
            
        @self.app.errorhandler(404)
        def handle_not_found(error):
            return {
                'status': 'error', 
                'message': 'Resource not found',
                'timestamp': time.time()
            }, 404
            
        @self.app.errorhandler(Exception)
        def handle_unexpected_error(error):
            logger.error(f"Unexpected error: {error}", exc_info=True)
            gc.collect()
            return {
                'status': 'error',
                'message': 'An unexpected error occurred',
                'timestamp': time.time()
            }, 500
    
    def _setup_memory_monitoring(self):
        """Setup memory monitoring and cleanup"""
        
        def memory_monitor():
            """Background thread to monitor memory usage"""
            while not self._shutdown_flag.is_set():
                try:
                    memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                    
                    if memory_mb > self.max_memory_mb:
                        logger.warning(f"High memory usage: {memory_mb:.1f}MB")
                        gc.collect()  # Force garbage collection
                        
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    logger.error(f"Memory monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error
                    
        self._monitoring_thread = threading.Thread(target=memory_monitor, daemon=True)
        self._monitoring_thread.start()
        
    def _setup_request_limiting(self):
        """Setup request limiting to prevent overload"""
        
        @self.app.before_request
        def before_request():
            self.request_count += 1
            self.active_requests += 1
            
            if self.active_requests > self.max_concurrent_requests:
                logger.warning(f"Too many concurrent requests: {self.active_requests}")
                return {
                    'status': 'error',
                    'message': 'Server busy, please try again later',
                    'timestamp': time.time()
                }, 503
                
        @self.app.after_request
        def after_request(response):
            self.active_requests = max(0, self.active_requests - 1)
            
            # Trigger garbage collection periodically
            if self.request_count % 100 == 0:
                gc.collect()
                
            return response
            
    def shutdown(self):
        """Clean shutdown of monitoring"""
        self._shutdown_flag.set()
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
            
    def get_stability_stats(self):
        """Get current stability statistics"""
        try:
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            cpu_percent = psutil.Process().cpu_percent()
            
            return {
                'memory_mb': round(memory_mb, 1),
                'cpu_percent': round(cpu_percent, 1),
                'total_requests': self.request_count,
                'active_requests': self.active_requests,
                'memory_limit_mb': self.max_memory_mb,
                'status': 'healthy' if memory_mb < self.max_memory_mb else 'high_memory'
            }
        except Exception as e:
            logger.error(f"Error getting stability stats: {e}")
            return {'status': 'error', 'message': str(e)}

def create_stability_decorator(stability_manager):
    """
    Create a decorator for API endpoints to add stability monitoring
    """
    def stability_monitor(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Execute the original function
                result = f(*args, **kwargs)
                
                # Log successful request
                duration = time.time() - start_time
                if duration > 5.0:  # Log slow requests
                    logger.warning(f"Slow request: {request.endpoint} took {duration:.2f}s")
                    
                return result
                
            except Exception as e:
                # Log and handle errors
                duration = time.time() - start_time
                logger.error(f"Request failed: {request.endpoint} after {duration:.2f}s - {e}")
                
                # Force garbage collection on errors
                gc.collect()
                
                # Return standardized error response
                return {
                    'status': 'error',
                    'endpoint': request.endpoint,
                    'message': str(e),
                    'duration_seconds': round(duration, 2),
                    'timestamp': time.time()
                }, 500
                
        return decorated_function
    return stability_monitor

# Utility functions for web stability

def safe_json_response(data, status_code=200):
    """
    Create a safe JSON response with error handling
    """
    try:
        from flask import jsonify
        
        # Ensure data is serializable
        if hasattr(data, 'to_dict'):
            data = data.to_dict()
            
        return jsonify(data), status_code
        
    except Exception as e:
        logger.error(f"JSON serialization error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Response serialization failed',
            'timestamp': time.time()
        }), 500

def monitor_request_memory(func):
    """
    Decorator to monitor memory usage of individual requests
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            result = func(*args, **kwargs)
            
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_delta = end_memory - start_memory
            
            if memory_delta > 50:  # Log if request used > 50MB
                logger.warning(f"High memory request: {func.__name__} used {memory_delta:.1f}MB")
                
            return result
            
        except Exception as e:
            # Clean up memory on errors
            gc.collect()
            raise e
            
    return wrapper

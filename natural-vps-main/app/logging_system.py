"""
Natural VPS - Advanced Logging & Debugging System
Comprehensive logging with error tracking and performance monitoring
"""

import logging
import traceback
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import request, g
from app.database import db
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AdvancedLogger:
    """Advanced logging system with error tracking"""
    
    @staticmethod
    def log_event(event_type, user_id=None, data=None, severity='info'):
        """Log important events"""
        try:
            db.execute("""
                INSERT INTO event_logs (event_type, user_id, data, severity, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (event_type, user_id, json.dumps(data), severity, datetime.now().isoformat()))
            
            logger.log(
                getattr(logging, severity.upper(), logging.INFO),
                f"Event: {event_type} | User: {user_id} | Data: {data}"
            )
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
    
    @staticmethod
    def log_error(error, error_type='exception', user_id=None, context=None):
        """Log errors with full context"""
        try:
            error_data = {
                'error_message': str(error),
                'error_type': error_type,
                'traceback': traceback.format_exc(),
                'context': context
            }
            
            db.execute("""
                INSERT INTO error_logs (error_type, user_id, error_message, traceback, context, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (error_type, user_id, str(error), traceback.format_exc(), 
                  json.dumps(context), datetime.now().isoformat()))
            
            logger.error(f"Error [{error_type}]: {error}\n{traceback.format_exc()}")
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    @staticmethod
    def log_performance(operation, duration_ms, status='success', details=None):
        """Log performance metrics"""
        try:
            db.execute("""
                INSERT INTO performance_logs (operation, duration_ms, status, details, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (operation, duration_ms, status, json.dumps(details), datetime.now().isoformat()))
            
            if duration_ms > 1000:  # Alert on slow operations
                logger.warning(f"Slow operation: {operation} took {duration_ms}ms")
        except Exception as e:
            logger.error(f"Failed to log performance: {e}")

def track_performance(f):
    """Decorator to track function performance"""
    @wraps(f)
    def decorated(*args, **kwargs):
        start = time.time()
        try:
            result = f(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            AdvancedLogger.log_performance(f.__name__, duration_ms, 'success')
            return result
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            AdvancedLogger.log_performance(f.__name__, duration_ms, 'error', str(e))
            raise
    return decorated

def safe_execute(f):
    """Decorator for safe execution with error handling"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            AdvancedLogger.log_error(e, error_type=type(e).__name__)
            raise
    return decorated

class DebugHelper:
    """Helper functions for debugging"""
    
    @staticmethod
    def get_error_logs(limit=100):
        """Retrieve recent error logs"""
        logs = db.fetchall("""
            SELECT * FROM error_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        return logs
    
    @staticmethod
    def get_performance_summary(hours=24):
        """Get performance summary"""
        summary = db.fetchone("""
            SELECT 
                AVG(duration_ms) as avg_duration,
                MAX(duration_ms) as max_duration,
                MIN(duration_ms) as min_duration,
                COUNT(*) as total_operations
            FROM performance_logs 
            WHERE timestamp > ?
        """, ((datetime.now() - timedelta(hours=hours)).isoformat(),))
        
        return dict(summary) if summary else {}
    
    @staticmethod
    def get_slowest_operations(limit=10):
        """Find slowest operations"""
        ops = db.fetchall("""
            SELECT operation, duration_ms, status, timestamp
            FROM performance_logs 
            ORDER BY duration_ms DESC 
            LIMIT ?
        """, (limit,))
        return ops
    
    @staticmethod
    def get_system_diagnostics():
        """Get comprehensive system diagnostics"""
        from datetime import timedelta
        
        now = datetime.now()
        
        return {
            'timestamp': now.isoformat(),
            'error_count_1h': db.fetchone(
                "SELECT COUNT(*) as count FROM error_logs WHERE timestamp > ?",
                ((now - timedelta(hours=1)).isoformat(),)
            )['count'],
            'error_count_24h': db.fetchone(
                "SELECT COUNT(*) as count FROM error_logs WHERE timestamp > ?",
                ((now - timedelta(hours=24)).isoformat(),)
            )['count'],
            'avg_response_time': db.fetchone(
                "SELECT AVG(duration_ms) as avg FROM performance_logs WHERE timestamp > ?",
                ((now - timedelta(hours=1)).isoformat(),)
            )['avg'],
            'total_users': db.fetchone("SELECT COUNT(*) as count FROM users")['count'],
            'total_vms': db.fetchone("SELECT COUNT(*) as count FROM vms")['count'],
            'active_sessions': db.fetchone("SELECT COUNT(*) as count FROM sessions")['count']
        }

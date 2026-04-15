"""
Natural VPS - Error Handler & Recovery System
Comprehensive error handling, logging, and recovery strategies
"""

import traceback
import json
from datetime import datetime
from functools import wraps
from flask import jsonify, request, g
from app.database import db
from app.logging_system import setup_logging

logger = setup_logging(__name__)

class APIError(Exception):
    """Base API Error class"""
    def __init__(self, message, status_code=400, error_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or 'API_ERROR'

class ValidationError(APIError):
    """Validation error"""
    def __init__(self, message, status_code=400):
        super().__init__(message, status_code, 'VALIDATION_ERROR')

class AuthenticationError(APIError):
    """Authentication error"""
    def __init__(self, message="Authentication failed"):
        super().__init__(message, 401, 'AUTH_ERROR')

class AuthorizationError(APIError):
    """Authorization error"""
    def __init__(self, message="Permission denied"):
        super().__init__(message, 403, 'AUTH_ERROR')

class NotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, message="Resource not found"):
        super().__init__(message, 404, 'NOT_FOUND')

class ConflictError(APIError):
    """Conflict error (e.g., duplicate resource)"""
    def __init__(self, message="Resource already exists"):
        super().__init__(message, 409, 'CONFLICT')

class RateLimitError(APIError):
    """Rate limit exceeded"""
    def __init__(self, message="Rate limit exceeded"):
        super().__init__(message, 429, 'RATE_LIMIT')

class ExternalServiceError(APIError):
    """External service error (GitHub, Tailscale, etc.)"""
    def __init__(self, service, message):
        super().__init__(f"{service} service error: {message}", 502, 'SERVICE_ERROR')

class ErrorHandler:
    """Error handler and recovery manager"""
    
    @staticmethod
    def register_error_handlers(app):
        """Register error handlers on Flask app"""
        
        @app.errorhandler(APIError)
        def handle_api_error(error):
            """Handle custom API errors"""
            response = {
                'success': False,
                'error': error.message,
                'error_code': error.error_code,
                'request_id': getattr(g, 'request_id', None)
            }
            
            # Log error
            ErrorHandler.log_error(error, error.status_code)
            
            return jsonify(response), error.status_code
        
        @app.errorhandler(400)
        def handle_bad_request(error):
            """Handle bad request errors"""
            return jsonify({
                'success': False,
                'error': 'Bad request - Invalid input',
                'error_code': 'BAD_REQUEST',
                'request_id': getattr(g, 'request_id', None)
            }), 400
        
        @app.errorhandler(401)
        def handle_unauthorized(error):
            """Handle unauthorized errors"""
            return jsonify({
                'success': False,
                'error': 'Unauthorized - Please login',
                'error_code': 'UNAUTHORIZED',
                'request_id': getattr(g, 'request_id', None)
            }), 401
        
        @app.errorhandler(403)
        def handle_forbidden(error):
            """Handle forbidden errors"""
            return jsonify({
                'success': False,
                'error': 'Forbidden - Access denied',
                'error_code': 'FORBIDDEN',
                'request_id': getattr(g, 'request_id', None)
            }), 403
        
        @app.errorhandler(404)
        def handle_not_found(error):
            """Handle not found errors"""
            return jsonify({
                'success': False,
                'error': 'Resource not found',
                'error_code': 'NOT_FOUND',
                'request_id': getattr(g, 'request_id', None)
            }), 404
        
        @app.errorhandler(429)
        def handle_rate_limit(error):
            """Handle rate limit errors"""
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded - please try again later',
                'error_code': 'RATE_LIMIT',
                'request_id': getattr(g, 'request_id', None)
            }), 429
        
        @app.errorhandler(500)
        def handle_internal_error(error):
            """Handle internal server errors"""
            error_resp = {
                'success': False,
                'error': 'Internal server error - please try again later',
                'error_code': 'INTERNAL_ERROR',
                'request_id': getattr(g, 'request_id', None)
            }
            
            # Log error
            ErrorHandler.log_error(error, 500)
            
            return jsonify(error_resp), 500
        
        @app.errorhandler(Exception)
        def handle_generic_error(error):
            """Handle generic unhandled exceptions"""
            error_resp = {
                'success': False,
                'error': 'An unexpected error occurred',
                'error_code': 'UNKNOWN_ERROR',
                'request_id': getattr(g, 'request_id', None)
            }
            
            # Log error
            ErrorHandler.log_error(error, 500, traceback=True)
            
            return jsonify(error_resp), 500
    
    @staticmethod
    def log_error(error, status_code, user_id=None, traceback_info=False):
        """Log error to database and logger"""
        try:
            error_type = type(error).__name__
            error_message = str(error)
            ip = getattr(g, 'client_ip', 'unknown')
            
            # Log to file
            logger.error(f"[{status_code}] {error_type}: {error_message}")
            
            # Log to database
            if traceback_info:
                tb = traceback.format_exc()
            else:
                tb = None
            
            db.execute(
                """INSERT INTO error_logs (error_type, user_id, error_message, traceback, context, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (error_type, user_id, error_message, tb, ip, datetime.now().isoformat())
            )
        except Exception as e:
            logger.error(f"Error logging failed: {e}")
    
    @staticmethod
    def catch_errors(f):
        """Decorator to catch and handle errors"""
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except ValidationError as e:
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'error_code': e.error_code
                }), e.status_code
            except AuthenticationError as e:
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'error_code': e.error_code
                }), 401
            except AuthorizationError as e:
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'error_code': e.error_code
                }), 403
            except NotFoundError as e:
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'error_code': e.error_code
                }), 404
            except ConflictError as e:
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'error_code': e.error_code
                }), 409
            except RateLimitError as e:
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'error_code': e.error_code
                }), 429
            except ExternalServiceError as e:
                ErrorHandler.log_error(e, 502, user_id=getattr(g, 'user_id', None))
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'error_code': e.error_code
                }), 502
            except APIError as e:
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'error_code': e.error_code
                }), e.status_code
            except Exception as e:
                ErrorHandler.log_error(e, 500, user_id=getattr(g, 'user_id', None), traceback_info=True)
                return jsonify({
                    'success': False,
                    'error': 'Internal server error',
                    'error_code': 'INTERNAL_ERROR'
                }), 500
        return decorated
    
    @staticmethod
    def safe_operation(operation_name, operation_func, *args, **kwargs):
        """Safely execute an operation with error handling"""
        try:
            result = operation_func(*args, **kwargs)
            logger.info(f"Operation '{operation_name}' completed successfully")
            return True, result
        except Exception as e:
            logger.error(f"Operation '{operation_name}' failed: {str(e)}")
            ErrorHandler.log_error(e, 500, traceback_info=True)
            return False, str(e)


class RecoveryStrategy:
    """Strategies for recovering from errors"""
    
    @staticmethod
    def retry_with_backoff(func, max_retries=3, base_delay=1, backoff_factor=2):
        """Retry operation with exponential backoff"""
        import time
        for attempt in range(max_retries):
            try:
                return True, func()
            except Exception as e:
                if attempt == max_retries - 1:
                    return False, str(e)
                
                delay = base_delay * (backoff_factor ** attempt)
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s: {str(e)}")
                time.sleep(delay)
        
        return False, "Max retries exceeded"
    
    @staticmethod
    def fallback_chain(*strategies):
        """Try multiple strategies in sequence"""
        for strategy_name, strategy_func in strategies:
            try:
                result = strategy_func()
                logger.info(f"Fallback strategy '{strategy_name}' succeeded")
                return True, result
            except Exception as e:
                logger.warning(f"Fallback strategy '{strategy_name}' failed: {str(e)}")
                continue
        
        return False, "All fallback strategies exhausted"
    
    @staticmethod
    def circuit_breaker(func, failure_threshold=5, reset_timeout=60):
        """Circuit breaker pattern to prevent cascading failures"""
        state = {'failures': 0, 'last_failure': None, 'is_open': False}
        
        def wrapped(*args, **kwargs):
            if state['is_open']:
                import time
                elapsed = time.time() - state['last_failure']
                if elapsed > reset_timeout:
                    state['is_open'] = False
                    state['failures'] = 0
                else:
                    raise Exception("Circuit breaker is open - service temporarily unavailable")
            
            try:
                result = func(*args, **kwargs)
                state['failures'] = 0
                return result
            except Exception as e:
                state['failures'] += 1
                state['last_failure'] = __import__('time').time()
                
                if state['failures'] >= failure_threshold:
                    state['is_open'] = True
                    logger.error(f"Circuit breaker opened after {state['failures']} failures")
                
                raise e
        
        return wrapped

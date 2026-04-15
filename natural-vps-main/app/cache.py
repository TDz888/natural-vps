"""
Natural VPS - Caching System
Implements in-memory caching with TTL support
"""

from flask_caching import Cache
import functools
import hashlib
import json

# Initialize cache
cache = Cache(config={'CACHE_TYPE': 'simple'})

def cache_query(ttl=300):
    """Decorator for database query caching"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            cache_key = f"query_{f.__name__}_{hashlib.md5(json.dumps([args, kwargs], default=str).encode()).hexdigest()}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout=ttl)
            return result
        return decorated_function
    return decorator

def cache_api_response(ttl=300):
    """Decorator for API response caching"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request, g
            
            # Don't cache if user not authenticated
            if not hasattr(g, 'user_id'):
                return f(*args, **kwargs)
            
            # Generate cache key with user context
            cache_key = f"api_{g.user_id}_{f.__name__}_{hashlib.md5(str(request.args).encode()).hexdigest()}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout=ttl)
            return result
        return decorated_function
    return decorator

def invalidate_cache(pattern=None):
    """Clear cache entries"""
    if pattern:
        keys = cache.cache._cache.keys()
        for key in keys:
            if pattern in str(key):
                cache.delete(key)
    else:
        cache.clear()

# Cache warming functions
def warmup_vm_cache():
    """Pre-load frequently accessed VM data into cache"""
    from app.database import db
    
    # Cache VMs by status
    for status in ['running', 'creating', 'failed']:
        vms = db.fetchall("SELECT * FROM vms WHERE status = ?", (status,))
        cache.set(f"vms_by_status_{status}", vms, timeout=600)

def warmup_user_cache():
    """Pre-load frequently accessed user data into cache"""
    from app.database import db
    
    # Cache top users by VM count
    users = db.fetchall("""
        SELECT u.*, COUNT(v.id) as vm_count 
        FROM users u 
        LEFT JOIN vms v ON u.id = v.user_id 
        GROUP BY u.id 
        ORDER BY vm_count DESC 
        LIMIT 100
    """)
    cache.set("top_users_by_vm_count", users, timeout=3600)

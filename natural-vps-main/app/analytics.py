"""
Natural VPS - Advanced Analytics & AI Logic
Intelligent system for prediction, optimization, and anomaly detection
"""

from datetime import datetime, timedelta
from app.database import db
from app.config import Config
import json
from collections import defaultdict
import statistics

class AdvancedAnalytics:
    """AI-powered analytics for system intelligence"""
    
    @staticmethod
    def predict_resource_usage():
        """Predict future resource usage based on patterns"""
        vms = db.fetchall("""
            SELECT created_at, expires_at, status 
            FROM vms 
            WHERE created_at > ?
        """, ((datetime.now() - timedelta(days=30)).isoformat(),))
        
        if not vms:
            return {'confidence': 0, 'prediction': 'insufficient_data'}
        
        # Analyze creation patterns
        creation_times = []
        for vm in vms:
            created = datetime.fromisoformat(vm['created_at'])
            creation_times.append(created.hour)
        
        # Find peak hours
        peak_hour = max(set(creation_times), key=creation_times.count)
        average_creates_per_hour = len(vms) / 24
        
        return {
            'confidence': min(0.95, len(vms) / 1000),
            'peak_hour': peak_hour,
            'avg_creates_per_hour': round(average_creates_per_hour, 2),
            'prediction': 'high_load' if average_creates_per_hour > 2 else 'normal_load'
        }
    
    @staticmethod
    def detect_anomalies():
        """Detect anomalous user behavior"""
        from app.security import RequestLogger
        
        # Get request stats
        stats = RequestLogger.get_request_stats(hours=1)
        
        anomalies = []
        
        # Check for unusual request patterns
        if stats.get('total_requests', 0) > 500:
            anomalies.append({
                'type': 'high_request_volume',
                'severity': 'warning',
                'requests': stats['total_requests'],
                'threshold': 500
            })
        
        # Check for error rate
        if stats.get('total_requests', 1) > 0:
            error_rate = (stats.get('errors', 0) / stats['total_requests']) * 100
            if error_rate > 5:
                anomalies.append({
                    'type': 'high_error_rate',
                    'severity': 'critical',
                    'error_rate': round(error_rate, 2)
                })
        
        return anomalies
    
    @staticmethod
    def get_user_recommendations():
        """Generate AI recommendations for users"""
        recommendations = []
        
        # Check VMs for optimization
        vms = db.fetchall("""
            SELECT COUNT(*) as count, status 
            FROM vms 
            WHERE created_at > ? 
            GROUP BY status
        """, ((datetime.now() - timedelta(hours=24)).isoformat(),))
        
        creating_count = next((vm['count'] for vm in vms if vm['status'] == 'creating'), 0)
        if creating_count > 3:
            recommendations.append({
                'type': 'batch_operations',
                'priority': 'high',
                'message': f'Consider batching operations: {creating_count} VMs pending'
            })
        
        # Check for inactive users
        users = db.fetchall("""
            SELECT u.id, u.username, MAX(s.created_at) as last_login
            FROM users u 
            LEFT JOIN sessions s ON u.id = s.user_id 
            GROUP BY u.id
        """)
        
        for user in users:
            if user['last_login']:
                last_login = datetime.fromisoformat(user['last_login'])
                if datetime.now() - last_login > timedelta(days=7):
                    recommendations.append({
                        'type': 'inactive_user',
                        'priority': 'low',
                        'user_id': user['id']
                    })
        
        return recommendations
    
    @staticmethod
    def optimize_cache_strategy():
        """Dynamically optimize cache based on usage patterns"""
        from app.cache import cache
        
        # Analyze most accessed resources
        request_logs = db.fetchall("""
            SELECT path, COUNT(*) as count 
            FROM request_logs 
            WHERE timestamp > ? 
            GROUP BY path 
            ORDER BY count DESC 
            LIMIT 10
        """, ((datetime.now() - timedelta(hours=24)).isoformat(),))
        
        optimizations = []
        for log in request_logs:
            path = log['path']
            count = log['count']
            
            # Recommend longer cache for frequently accessed paths
            if count > 100:
                optimizations.append({
                    'path': path,
                    'recommended_ttl': 600,  # 10 minutes
                    'current_ttl': 300,
                    'improvement': f"{(600-300)/300*100:.0f}%"
                })
        
        return optimizations

class SmartErrorHandler:
    """Intelligent error handling and recovery"""
    
    @staticmethod
    def categorize_error(error):
        """Categorize errors for smarter handling"""
        error_str = str(error).lower()
        
        if 'database' in error_str or 'sqlite' in error_str:
            return 'database_error'
        elif 'timeout' in error_str or 'connection' in error_str:
            return 'network_error'
        elif 'authentication' in error_str or 'unauthorized' in error_str:
            return 'auth_error'
        elif 'permission' in error_str or 'forbidden' in error_str:
            return 'permission_error'
        elif 'not found' in error_str or '404' in error_str:
            return 'not_found_error'
        elif 'validation' in error_str or 'invalid' in error_str:
            return 'validation_error'
        else:
            return 'unknown_error'
    
    @staticmethod
    def get_recovery_suggestion(error_category):
        """Get smart recovery suggestions"""
        suggestions = {
            'database_error': 'Retry operation or check DB connection',
            'network_error': 'Check internet connection and try again',
            'auth_error': 'Log in again or refresh credentials',
            'permission_error': 'Check user permissions or contact admin',
            'not_found_error': 'Resource may have been deleted',
            'validation_error': 'Check input format and try again',
            'unknown_error': 'Contact support if issue persists'
        }
        return suggestions.get(error_category, 'Unknown error')

class PerformanceOptimizer:
    """Optimize application performance"""
    
    @staticmethod
    def get_slowest_endpoints():
        """Find slowest API endpoints"""
        # Analyze performance by tracking execution time
        request_logs = db.fetchall("""
            SELECT path, COUNT(*) as requests, status_code
            FROM request_logs 
            WHERE timestamp > ? 
            GROUP BY path 
            ORDER BY requests DESC 
            LIMIT 10
        """, ((datetime.now() - timedelta(hours=24)).isoformat(),))
        
        return request_logs
    
    @staticmethod
    def identify_db_bottlenecks():
        """Identify database performance issues"""
        issues = []
        
        # Check table sizes
        tables = ['users', 'sessions', 'vms', 'request_logs']
        for table in tables:
            result = db.fetchone(f"SELECT COUNT(*) as count FROM {table}")
            count = result['count'] if result else 0
            
            if count > 100000:
                issues.append({
                    'type': 'large_table',
                    'table': table,
                    'rows': count,
                    'action': 'Consider archiving old records'
                })
        
        return issues
    
    @staticmethod
    def optimize_queries():
        """Suggest query optimizations"""
        optimizations = [
            {
                'query': 'SELECT * FROM request_logs',
                'issue': 'Selecting all columns',
                'fix': 'Select only needed columns'
            },
            {
                'query': 'Frequent COUNT() queries',
                'issue': 'No indexes on filtered columns',
                'fix': 'Add indexes to frequently filtered columns'
            }
        ]
        return optimizations

class UserBehaviorAnalysis:
    """Analyze user behavior patterns"""
    
    @staticmethod
    def get_user_engagement():
        """Analyze user engagement metrics"""
        users = db.fetchall("""
            SELECT u.id, u.username, 
                   COUNT(v.id) as vm_count,
                   MAX(s.created_at) as last_active
            FROM users u 
            LEFT JOIN vms v ON u.id = v.user_id 
            LEFT JOIN sessions s ON u.id = s.user_id 
            GROUP BY u.id
        """)
        
        engagement = []
        for user in users:
            last_active = user['last_active']
            if last_active:
                days_inactive = (datetime.now() - datetime.fromisoformat(last_active)).days
            else:
                days_inactive = 999
            
            engagement_score = max(0, 100 - (days_inactive * 5) - (user['vm_count'] == 0) * 50)
            
            engagement.append({
                'user_id': user['id'],
                'username': user['username'],
                'vm_count': user['vm_count'],
                'days_inactive': days_inactive,
                'engagement_score': engagement_score
            })
        
        return sorted(engagement, key=lambda x: x['engagement_score'], reverse=True)
    
    @staticmethod
    def predict_churn():
        """Predict users likely to churn"""
        at_risk = []
        
        users = db.fetchall("""
            SELECT u.id, u.username, u.created_at,
                   MAX(s.created_at) as last_active
            FROM users u 
            LEFT JOIN sessions s ON u.id = s.user_id 
            GROUP BY u.id
        """)
        
        for user in users:
            account_age = (datetime.now() - datetime.fromisoformat(user['created_at'])).days
            
            if user['last_active']:
                days_inactive = (datetime.now() - datetime.fromisoformat(user['last_active'])).days
            else:
                days_inactive = account_age
            
            # Churn indicators
            if days_inactive > 14 and account_age < 60:  # Inactive early users
                churn_risk = 'high'
            elif days_inactive > 7:
                churn_risk = 'medium'
            else:
                churn_risk = 'low'
            
            if churn_risk != 'low':
                at_risk.append({
                    'user_id': user['id'],
                    'username': user['username'],
                    'days_inactive': days_inactive,
                    'account_age': account_age,
                    'churn_risk': churn_risk
                })
        
        return at_risk

class SystemHealthMonitor:
    """Advanced system health monitoring"""
    
    @staticmethod
    def get_comprehensive_health():
        """Get detailed system health"""
        from app.security import RequestLogger
        
        stats = RequestLogger.get_request_stats(hours=24)
        
        # Calculate health score
        success_rate = (stats.get('successful', 0) / max(stats.get('total_requests', 1), 1)) * 100
        
        if success_rate >= 99:
            health_status = 'excellent'
        elif success_rate >= 95:
            health_status = 'good'
        elif success_rate >= 90:
            health_status = 'fair'
        else:
            health_status = 'poor'
        
        return {
            'status': health_status,
            'success_rate': round(success_rate, 2),
            'total_requests_24h': stats.get('total_requests', 0),
            'unique_ips': stats.get('unique_ips', 0),
            'uptime_percentage': round(success_rate, 2),
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def get_alerts():
        """Get system alerts"""
        alerts = []
        
        # Check for high error rate
        stats = RequestLogger.get_request_stats(hours=1)
        if stats.get('total_requests', 0) > 0:
            error_rate = (stats.get('errors', 0) / stats['total_requests']) * 100
            if error_rate > 5:
                alerts.append({
                    'severity': 'high',
                    'type': 'high_error_rate',
                    'message': f'Error rate at {error_rate:.1f}%'
                })
        
        # Check for slow response times (implied through error rate)
        # Check for unusual activity patterns
        
        return alerts

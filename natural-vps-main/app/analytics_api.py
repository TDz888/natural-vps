"""
Natural VPS - Advanced Analytics & Insights API
AI-powered analytics, predictions, and recommendations
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from app.decorators import require_auth
from app.analytics import (
    AdvancedAnalytics, UserBehaviorAnalysis, 
    SystemHealthMonitor, PerformanceOptimizer
)
from app.logging_system import AdvancedLogger, DebugHelper
from app.security import RequestLogger

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/insights/dashboard', methods=['GET'])
@require_auth
def get_insights_dashboard():
    """Get comprehensive dashboard with AI insights"""
    return jsonify({
        'success': True,
        'dashboard': {
            'system_health': SystemHealthMonitor.get_comprehensive_health(),
            'alerts': SystemHealthMonitor.get_alerts(),
            'resource_prediction': AdvancedAnalytics.predict_resource_usage(),
            'anomalies': AdvancedAnalytics.detect_anomalies(),
            'performance_issues': PerformanceOptimizer.get_slowest_endpoints(),
            'recommendations': AdvancedAnalytics.get_user_recommendations(),
            'timestamp': datetime.now().isoformat()
        }
    })

@analytics_bp.route('/insights/performance', methods=['GET'])
@require_auth
def get_performance_insights():
    """Get detailed performance analysis"""
    hours = request.args.get('hours', 24, type=int)
    
    return jsonify({
        'success': True,
        'performance': {
            'slowest_endpoints': PerformanceOptimizer.get_slowest_endpoints(),
            'db_bottlenecks': PerformanceOptimizer.identify_db_bottlenecks(),
            'cache_optimization': AdvancedAnalytics.optimize_cache_strategy(),
            'request_stats': RequestLogger.get_request_stats(hours=hours),
            'timestamp': datetime.now().isoformat()
        }
    })

@analytics_bp.route('/insights/users', methods=['GET'])
@require_auth
def get_user_insights():
    """Get user behavior and engagement insights"""
    return jsonify({
        'success': True,
        'user_insights': {
            'engagement_rankings': UserBehaviorAnalysis.get_user_engagement(),
            'churn_predictions': UserBehaviorAnalysis.predict_churn(),
            'total_users': len(UserBehaviorAnalysis.get_user_engagement()),
            'timestamp': datetime.now().isoformat()
        }
    })

@analytics_bp.route('/insights/predictions', methods=['GET'])
@require_auth
def get_predictions():
    """Get AI predictions for resource usage and trends"""
    return jsonify({
        'success': True,
        'predictions': {
            'resource_usage': AdvancedAnalytics.predict_resource_usage(),
            'recommendations': AdvancedAnalytics.get_user_recommendations(),
            'timestamp': datetime.now().isoformat()
        }
    })

@analytics_bp.route('/diagnostics/system', methods=['GET'])
@require_auth
def get_system_diagnostics():
    """Get comprehensive system diagnostics"""
    return jsonify({
        'success': True,
        'diagnostics': DebugHelper.get_system_diagnostics()
    })

@analytics_bp.route('/diagnostics/errors', methods=['GET'])
@require_auth
def get_error_diagnostics():
    """Get error diagnostics and logs"""
    limit = request.args.get('limit', 50, type=int)
    
    return jsonify({
        'success': True,
        'diagnostics': {
            'recent_errors': DebugHelper.get_error_logs(limit=limit),
            'error_summary': DebugHelper.get_system_diagnostics(),
            'timestamp': datetime.now().isoformat()
        }
    })

@analytics_bp.route('/diagnostics/performance', methods=['GET'])
@require_auth
def get_performance_diagnostics():
    """Get performance diagnostics"""
    hours = request.args.get('hours', 24, type=int)
    
    return jsonify({
        'success': True,
        'diagnostics': {
            'performance_summary': DebugHelper.get_performance_summary(hours=hours),
            'slowest_operations': DebugHelper.get_slowest_operations(limit=20),
            'timestamp': datetime.now().isoformat()
        }
    })

@analytics_bp.route('/health/summary', methods=['GET'])
def get_health_summary():
    """Quick health summary (no auth required)"""
    return jsonify({
        'success': True,
        'health': SystemHealthMonitor.get_comprehensive_health()
    })

@analytics_bp.route('/stats/usage', methods=['GET'])
@require_auth
def get_usage_stats():
    """Get detailed usage statistics"""
    from app.database import db
    
    stats = db.fetchone("""
        SELECT 
            COUNT(DISTINCT u.id) as total_users,
            COUNT(DISTINCT v.id) as total_vms,
            SUM(CASE WHEN v.status = 'running' THEN 1 ELSE 0 END) as running_vms,
            SUM(CASE WHEN v.status = 'creating' THEN 1 ELSE 0 END) as creating_vms,
            SUM(CASE WHEN v.status = 'failed' THEN 1 ELSE 0 END) as failed_vms,
            COUNT(DISTINCT s.id) as active_sessions
        FROM users u
        LEFT JOIN vms v ON u.id = v.user_id
        LEFT JOIN sessions s ON u.id = s.user_id
    """)
    
    return jsonify({
        'success': True,
        'stats': dict(stats) if stats else {}
    })

@analytics_bp.route('/recommendations/optimize', methods=['GET'])
@require_auth
def get_optimization_recommendations():
    """Get AI-powered optimization recommendations"""
    recommendations = []
    
    # Performance recommendations
    perf_opts = PerformanceOptimizer.optimize_queries()
    recommendations.extend([
        {'category': 'performance', **opt} for opt in perf_opts
    ])
    
    # Analytics recommendations
    analytics_recs = AdvancedAnalytics.get_user_recommendations()
    recommendations.extend([
        {'category': 'operations', **rec} for rec in analytics_recs
    ])
    
    return jsonify({
        'success': True,
        'recommendations': recommendations,
        'total': len(recommendations)
    })

@analytics_bp.route('/export/analytics', methods=['GET'])
@require_auth
def export_analytics():
    """Export analytics data"""
    export_format = request.args.get('format', 'json')
    
    data = {
        'system_health': SystemHealthMonitor.get_comprehensive_health(),
        'performance': DebugHelper.get_performance_summary(),
        'user_engagement': UserBehaviorAnalysis.get_user_engagement(),
        'generated_at': datetime.now().isoformat()
    }
    
    if export_format == 'json':
        return jsonify({'success': True, 'data': data})
    else:
        return jsonify({'success': False, 'error': 'Unsupported format'}), 400

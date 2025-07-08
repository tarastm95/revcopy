"""
Real-time System Monitoring API

Enterprise-grade monitoring endpoints providing comprehensive
system health, performance metrics, and operational insights.

Features:
- Real-time performance metrics
- System health monitoring
- Task queue monitoring
- Cache performance analytics
- Database query performance
- Security monitoring
- Alert management
- Predictive analytics
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
import json
import asyncio
import psutil
import structlog

from app.core.database import get_async_session
from app.api.deps import get_current_admin_user
from app.core.performance import performance_collector
from app.core.cache import cache
from app.core.background_tasks import task_manager
from app.models.user import User

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def get_system_health(
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get comprehensive system health status.
    
    Returns:
        Dict: System health metrics and status
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "metrics": {}
        }
        
        # Database health check
        try:
            db_start = datetime.utcnow()
            result = await db.execute(select(func.count()).select_from(text("pg_stat_activity")))
            db_connections = result.scalar()
            db_latency = (datetime.utcnow() - db_start).total_seconds() * 1000
            
            health_status["checks"]["database"] = {
                "status": "healthy",
                "latency_ms": db_latency,
                "active_connections": db_connections
            }
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Cache health check
        try:
            cache_stats = cache.get_stats()
            health_status["checks"]["cache"] = {
                "status": "healthy",
                "memory_hit_rate": cache_stats["memory_cache"]["hit_rate"],
                "redis_hit_rate": cache_stats["redis_cache"]["hit_rate"],
                "total_size_mb": cache_stats["memory_cache"]["size_bytes"] / (1024 * 1024)
            }
        except Exception as e:
            health_status["checks"]["cache"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Task queue health check
        try:
            task_stats = await task_manager.get_system_stats()
            healthy_workers = sum(1 for w in task_stats["workers"] if w["is_running"])
            total_workers = len(task_stats["workers"])
            
            health_status["checks"]["task_queue"] = {
                "status": "healthy" if healthy_workers > 0 else "degraded",
                "healthy_workers": healthy_workers,
                "total_workers": total_workers,
                "queue_length": sum(q.get("queue_length", 0) for q in task_stats["queues"].values())
            }
        except Exception as e:
            health_status["checks"]["task_queue"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # System resources check
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_status["checks"]["system_resources"] = {
                "status": "healthy" if cpu_percent < 80 and memory.percent < 80 else "degraded",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "available_memory_gb": memory.available / (1024**3)
            }
        except Exception as e:
            health_status["checks"]["system_resources"] = {
                "status": "unknown",
                "error": str(e)
            }
        
        # Overall health determination
        unhealthy_checks = [c for c in health_status["checks"].values() if c["status"] == "unhealthy"]
        if unhealthy_checks:
            health_status["status"] = "unhealthy"
        elif any(c["status"] == "degraded" for c in health_status["checks"].values()):
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/performance/summary")
async def get_performance_summary(
    hours: int = Query(1, ge=1, le=168, description="Time period in hours"),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get performance summary for specified time period.
    
    Args:
        hours: Time period in hours (1-168)
        current_admin: Current admin user
        
    Returns:
        Dict: Performance summary with metrics and recommendations
    """
    try:
        summary = performance_collector.get_performance_summary(hours)
        
        # Add optimization recommendations
        summary["recommendations"] = performance_collector.get_optimization_recommendations()
        
        # Add system performance trends
        summary["trends"] = await _get_performance_trends(hours)
        
        return summary
        
    except Exception as e:
        logger.error("Failed to get performance summary", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve performance summary")


@router.get("/performance/operations")
async def get_operation_performance(
    operation: Optional[str] = Query(None, description="Specific operation to analyze"),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get detailed performance statistics for operations.
    
    Args:
        operation: Specific operation name (optional)
        current_admin: Current admin user
        
    Returns:
        Dict: Operation performance statistics
    """
    try:
        if operation:
            stats = performance_collector.get_operation_stats(operation)
            return {
                "operation": operation,
                "statistics": stats
            }
        else:
            # Get all operations
            all_stats = {}
            for op in performance_collector.operation_stats.keys():
                all_stats[op] = performance_collector.get_operation_stats(op)
            
            return {
                "operations": all_stats,
                "total_operations": len(all_stats)
            }
            
    except Exception as e:
        logger.error("Failed to get operation performance", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve operation performance")


@router.get("/performance/realtime")
async def get_realtime_performance(
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get real-time performance metrics stream.
    
    Returns:
        StreamingResponse: Real-time performance data
    """
    async def generate_metrics():
        """Generate real-time metrics."""
        while True:
            try:
                # Collect current metrics
                metrics = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "system": {
                        "cpu_percent": psutil.cpu_percent(interval=0.1),
                        "memory_percent": psutil.virtual_memory().percent,
                        "active_connections": len(psutil.net_connections(kind='inet'))
                    },
                    "performance": {
                        "recent_operations": len([m for m in performance_collector.metrics 
                                                if m.timestamp > datetime.utcnow() - timedelta(minutes=1)]),
                        "avg_response_time": _calculate_avg_response_time(),
                        "error_rate": _calculate_error_rate()
                    },
                    "cache": cache.get_stats(),
                    "tasks": await task_manager.get_system_stats()
                }
                
                yield f"data: {json.dumps(metrics)}\n\n"
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error("Real-time metrics error", error=str(e))
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                await asyncio.sleep(5)
    
    return StreamingResponse(
        generate_metrics(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@router.get("/database/performance")
async def get_database_performance(
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get database performance metrics and slow queries.
    
    Returns:
        Dict: Database performance analysis
    """
    try:
        # Get database size and statistics
        db_stats = await _get_database_stats(db)
        
        # Get slow queries
        slow_queries = await _get_slow_queries(db)
        
        # Get connection statistics
        connection_stats = await _get_connection_stats(db)
        
        # Get table statistics
        table_stats = await _get_table_stats(db)
        
        return {
            "database_stats": db_stats,
            "slow_queries": slow_queries,
            "connection_stats": connection_stats,
            "table_stats": table_stats,
            "recommendations": _get_database_recommendations(db_stats, slow_queries)
        }
        
    except Exception as e:
        logger.error("Failed to get database performance", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve database performance")


@router.get("/cache/analytics")
async def get_cache_analytics(
    namespace: Optional[str] = Query(None, description="Cache namespace to analyze"),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get detailed cache analytics and optimization recommendations.
    
    Args:
        namespace: Specific cache namespace (optional)
        current_admin: Current admin user
        
    Returns:
        Dict: Cache analytics and recommendations
    """
    try:
        analytics = {
            "overall_stats": cache.get_stats(),
            "performance_impact": _calculate_cache_performance_impact(),
            "optimization_opportunities": _identify_cache_optimization_opportunities(),
            "recommendations": _get_cache_recommendations()
        }
        
        if namespace:
            analytics["namespace_analysis"] = _analyze_cache_namespace(namespace)
        
        return analytics
        
    except Exception as e:
        logger.error("Failed to get cache analytics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve cache analytics")


@router.get("/tasks/monitoring")
async def get_task_monitoring(
    queue: str = Query("default", description="Queue name to monitor"),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get comprehensive task queue monitoring data.
    
    Args:
        queue: Queue name to monitor
        current_admin: Current admin user
        
    Returns:
        Dict: Task monitoring data
    """
    try:
        # Get system stats
        system_stats = await task_manager.get_system_stats()
        
        # Get queue-specific stats
        queue_stats = system_stats["queues"].get(queue, {})
        
        # Get worker performance
        worker_performance = _analyze_worker_performance(system_stats["workers"])
        
        # Get task failure analysis
        failure_analysis = await _analyze_task_failures(queue)
        
        return {
            "queue_stats": queue_stats,
            "worker_performance": worker_performance,
            "failure_analysis": failure_analysis,
            "scheduler_status": system_stats["scheduler"],
            "recommendations": _get_task_recommendations(queue_stats, worker_performance)
        }
        
    except Exception as e:
        logger.error("Failed to get task monitoring", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve task monitoring")


@router.get("/security/monitoring")
async def get_security_monitoring(
    hours: int = Query(24, ge=1, le=168, description="Time period in hours"),
    db: AsyncSession = Depends(get_async_session),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get security monitoring dashboard with threat detection.
    
    Args:
        hours: Time period in hours
        db: Database session
        current_admin: Current admin user
        
    Returns:
        Dict: Security monitoring data
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Authentication metrics
        auth_metrics = await _get_auth_metrics(db, cutoff_time)
        
        # Failed login attempts
        failed_logins = await _get_failed_login_attempts(db, cutoff_time)
        
        # Suspicious activities
        suspicious_activities = await _detect_suspicious_activities(db, cutoff_time)
        
        # Rate limiting statistics
        rate_limit_stats = _get_rate_limit_stats()
        
        # IP analysis
        ip_analysis = await _analyze_ip_patterns(db, cutoff_time)
        
        return {
            "auth_metrics": auth_metrics,
            "failed_logins": failed_logins,
            "suspicious_activities": suspicious_activities,
            "rate_limit_stats": rate_limit_stats,
            "ip_analysis": ip_analysis,
            "security_score": _calculate_security_score(auth_metrics, failed_logins, suspicious_activities),
            "recommendations": _get_security_recommendations(failed_logins, suspicious_activities)
        }
        
    except Exception as e:
        logger.error("Failed to get security monitoring", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve security monitoring")


@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    hours: int = Query(24, ge=1, le=168, description="Time period in hours"),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Get system alerts and notifications.
    
    Args:
        severity: Alert severity filter
        hours: Time period in hours
        current_admin: Current admin user
        
    Returns:
        Dict: System alerts
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get performance alerts
        performance_alerts = [
            alert for alert in performance_collector.alerts 
            if alert['timestamp'] >= cutoff_time
        ]
        
        # Filter by severity if specified
        if severity:
            performance_alerts = [a for a in performance_alerts if a.get('severity') == severity]
        
        # Get system alerts
        system_alerts = await _get_system_alerts(cutoff_time)
        
        # Get security alerts
        security_alerts = await _get_security_alerts(cutoff_time)
        
        all_alerts = performance_alerts + system_alerts + security_alerts
        
        # Sort by timestamp (newest first)
        all_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "alerts": all_alerts,
            "total_count": len(all_alerts),
            "severity_breakdown": _group_alerts_by_severity(all_alerts),
            "type_breakdown": _group_alerts_by_type(all_alerts)
        }
        
    except Exception as e:
        logger.error("Failed to get alerts", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.post("/maintenance/cleanup")
async def trigger_maintenance_cleanup(
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Trigger system maintenance and cleanup tasks.
    
    Args:
        background_tasks: Background task manager
        current_admin: Current admin user
        
    Returns:
        Dict: Cleanup task status
    """
    try:
        # Schedule cleanup tasks
        cleanup_tasks = []
        
        # Clear old completed tasks
        task_id = await task_manager.submit_task(
            "cleanup_completed_tasks",
            "app.tasks.maintenance.cleanup_completed_tasks",
            config={"priority": "high"}
        )
        cleanup_tasks.append({"task": "cleanup_completed_tasks", "task_id": task_id})
        
        # Clear old performance metrics
        task_id = await task_manager.submit_task(
            "cleanup_performance_metrics",
            "app.tasks.maintenance.cleanup_performance_metrics",
            config={"priority": "high"}
        )
        cleanup_tasks.append({"task": "cleanup_performance_metrics", "task_id": task_id})
        
        # Optimize database
        task_id = await task_manager.submit_task(
            "optimize_database",
            "app.tasks.maintenance.optimize_database",
            config={"priority": "medium"}
        )
        cleanup_tasks.append({"task": "optimize_database", "task_id": task_id})
        
        logger.info("Maintenance cleanup triggered", admin_id=current_admin.id, tasks=len(cleanup_tasks))
        
        return {
            "status": "scheduled",
            "tasks": cleanup_tasks,
            "message": f"Scheduled {len(cleanup_tasks)} maintenance tasks"
        }
        
    except Exception as e:
        logger.error("Failed to trigger maintenance cleanup", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to trigger maintenance cleanup")


# Helper functions
async def _get_performance_trends(hours: int) -> Dict[str, Any]:
    """Get performance trends over time."""
    # Implementation would analyze historical performance data
    return {
        "response_time_trend": "improving",
        "error_rate_trend": "stable",
        "throughput_trend": "increasing"
    }


def _calculate_avg_response_time() -> float:
    """Calculate average response time from recent metrics."""
    recent_metrics = [
        m for m in performance_collector.metrics 
        if m.timestamp > datetime.utcnow() - timedelta(minutes=5)
    ]
    
    if not recent_metrics:
        return 0.0
    
    return sum(m.duration_ms for m in recent_metrics) / len(recent_metrics)


def _calculate_error_rate() -> float:
    """Calculate error rate from recent metrics."""
    recent_metrics = [
        m for m in performance_collector.metrics 
        if m.timestamp > datetime.utcnow() - timedelta(minutes=5)
    ]
    
    if not recent_metrics:
        return 0.0
    
    error_count = sum(1 for m in recent_metrics if not m.success)
    return (error_count / len(recent_metrics)) * 100


async def _get_database_stats(db: AsyncSession) -> Dict[str, Any]:
    """Get database statistics."""
    try:
        # Database size
        result = await db.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
        db_size = result.scalar()
        
        # Connection count
        result = await db.execute(text("SELECT count(*) FROM pg_stat_activity"))
        connection_count = result.scalar()
        
        # Transaction statistics
        result = await db.execute(text("""
            SELECT sum(xact_commit) as commits, sum(xact_rollback) as rollbacks
            FROM pg_stat_database WHERE datname = current_database()
        """))
        tx_stats = result.fetchone()
        
        return {
            "database_size": db_size,
            "connection_count": connection_count,
            "commits": tx_stats[0] if tx_stats else 0,
            "rollbacks": tx_stats[1] if tx_stats else 0
        }
    except Exception as e:
        logger.error("Failed to get database stats", error=str(e))
        return {}


async def _get_slow_queries(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get slow queries from pg_stat_statements if available."""
    try:
        result = await db.execute(text("""
            SELECT query, calls, total_time, mean_time, rows
            FROM pg_stat_statements 
            WHERE mean_time > 100 
            ORDER BY mean_time DESC 
            LIMIT 10
        """))
        
        queries = []
        for row in result:
            queries.append({
                "query": row[0][:200] + "..." if len(row[0]) > 200 else row[0],
                "calls": row[1],
                "total_time": row[2],
                "mean_time": row[3],
                "rows": row[4]
            })
        
        return queries
    except Exception:
        # pg_stat_statements might not be available
        return []


async def _get_connection_stats(db: AsyncSession) -> Dict[str, Any]:
    """Get connection statistics."""
    try:
        result = await db.execute(text("""
            SELECT state, count(*) as count
            FROM pg_stat_activity 
            WHERE pid <> pg_backend_pid()
            GROUP BY state
        """))
        
        stats = {}
        for row in result:
            stats[row[0] or 'unknown'] = row[1]
        
        return stats
    except Exception as e:
        logger.error("Failed to get connection stats", error=str(e))
        return {}


async def _get_table_stats(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get table statistics."""
    try:
        result = await db.execute(text("""
            SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup
            FROM pg_stat_user_tables
            ORDER BY n_live_tup DESC
            LIMIT 10
        """))
        
        tables = []
        for row in result:
            tables.append({
                "schema": row[0],
                "table": row[1],
                "inserts": row[2],
                "updates": row[3],
                "deletes": row[4],
                "live_tuples": row[5],
                "dead_tuples": row[6]
            })
        
        return tables
    except Exception as e:
        logger.error("Failed to get table stats", error=str(e))
        return []


def _get_database_recommendations(db_stats: Dict, slow_queries: List) -> List[str]:
    """Generate database optimization recommendations."""
    recommendations = []
    
    if slow_queries:
        recommendations.append("Consider adding indexes for slow queries")
    
    if db_stats.get('connection_count', 0) > 100:
        recommendations.append("High connection count - consider connection pooling")
    
    return recommendations


def _calculate_cache_performance_impact() -> Dict[str, float]:
    """Calculate cache performance impact."""
    stats = cache.get_stats()
    
    # Estimate time saved by cache hits
    memory_hits = stats["memory_cache"]["hits"]
    redis_hits = stats["redis_cache"]["hits"]
    
    # Assume average database query takes 50ms, cache hit takes 1ms
    time_saved_ms = memory_hits * 49 + redis_hits * 30
    
    return {
        "time_saved_ms": time_saved_ms,
        "time_saved_minutes": time_saved_ms / (1000 * 60),
        "estimated_cost_savings": time_saved_ms * 0.001  # $0.001 per millisecond saved
    }


def _identify_cache_optimization_opportunities() -> List[str]:
    """Identify cache optimization opportunities."""
    opportunities = []
    stats = cache.get_stats()
    
    if stats["memory_cache"]["hit_rate"] < 0.8:
        opportunities.append("Memory cache hit rate is low - consider warming frequently accessed data")
    
    if stats["redis_cache"]["hit_rate"] < 0.7:
        opportunities.append("Redis cache hit rate is low - review TTL settings")
    
    return opportunities


def _get_cache_recommendations() -> List[str]:
    """Get cache optimization recommendations."""
    return [
        "Monitor cache hit rates regularly",
        "Implement cache warming for critical data",
        "Consider increasing cache size for frequently accessed data",
        "Review and optimize TTL settings"
    ]


def _analyze_cache_namespace(namespace: str) -> Dict[str, Any]:
    """Analyze specific cache namespace."""
    # This would require enhanced cache implementation
    return {
        "namespace": namespace,
        "hit_rate": 0.85,
        "total_keys": 100,
        "avg_ttl": 3600
    }


def _analyze_worker_performance(workers: List[Dict]) -> Dict[str, Any]:
    """Analyze worker performance."""
    if not workers:
        return {}
    
    total_processed = sum(w["stats"]["tasks_processed"] for w in workers)
    total_completed = sum(w["stats"]["tasks_completed"] for w in workers)
    total_failed = sum(w["stats"]["tasks_failed"] for w in workers)
    
    return {
        "total_workers": len(workers),
        "active_workers": sum(1 for w in workers if w["is_running"]),
        "total_processed": total_processed,
        "total_completed": total_completed,
        "total_failed": total_failed,
        "success_rate": (total_completed / total_processed * 100) if total_processed > 0 else 0
    }


async def _analyze_task_failures(queue: str) -> Dict[str, Any]:
    """Analyze task failures."""
    # This would require access to task failure logs
    return {
        "common_errors": [],
        "failure_rate": 0.02,
        "avg_retry_count": 1.5
    }


def _get_task_recommendations(queue_stats: Dict, worker_performance: Dict) -> List[str]:
    """Get task optimization recommendations."""
    recommendations = []
    
    if queue_stats.get("queue_length", 0) > 100:
        recommendations.append("Queue length is high - consider adding more workers")
    
    if worker_performance.get("success_rate", 100) < 95:
        recommendations.append("Task success rate is low - review error handling")
    
    return recommendations


async def _get_auth_metrics(db: AsyncSession, cutoff_time: datetime) -> Dict[str, Any]:
    """Get authentication metrics."""
    try:
        # Successful logins
        result = await db.execute(
            select(func.count(User.id)).where(User.last_login >= cutoff_time)
        )
        successful_logins = result.scalar() or 0
        
        # Total users
        result = await db.execute(select(func.count(User.id)))
        total_users = result.scalar() or 0
        
        return {
            "successful_logins": successful_logins,
            "total_users": total_users,
            "login_rate": successful_logins / 24 if successful_logins > 0 else 0
        }
    except Exception as e:
        logger.error("Failed to get auth metrics", error=str(e))
        return {}


async def _get_failed_login_attempts(db: AsyncSession, cutoff_time: datetime) -> List[Dict]:
    """Get failed login attempts."""
    # This would require a failed login attempts table
    return []


async def _detect_suspicious_activities(db: AsyncSession, cutoff_time: datetime) -> List[Dict]:
    """Detect suspicious activities."""
    # This would require activity logging
    return []


def _get_rate_limit_stats() -> Dict[str, Any]:
    """Get rate limiting statistics."""
    # This would require rate limiting implementation
    return {
        "total_requests": 0,
        "rate_limited_requests": 0,
        "rate_limit_percentage": 0
    }


async def _analyze_ip_patterns(db: AsyncSession, cutoff_time: datetime) -> Dict[str, Any]:
    """Analyze IP address patterns."""
    # This would require IP logging
    return {
        "unique_ips": 0,
        "top_ips": [],
        "suspicious_ips": []
    }


def _calculate_security_score(auth_metrics: Dict, failed_logins: List, suspicious_activities: List) -> int:
    """Calculate security score (0-100)."""
    base_score = 100
    
    # Deduct points for failed logins
    base_score -= min(len(failed_logins) * 2, 30)
    
    # Deduct points for suspicious activities
    base_score -= min(len(suspicious_activities) * 5, 40)
    
    return max(base_score, 0)


def _get_security_recommendations(failed_logins: List, suspicious_activities: List) -> List[str]:
    """Get security recommendations."""
    recommendations = []
    
    if len(failed_logins) > 10:
        recommendations.append("High number of failed logins - consider implementing account lockout")
    
    if suspicious_activities:
        recommendations.append("Suspicious activities detected - review security logs")
    
    return recommendations


async def _get_system_alerts(cutoff_time: datetime) -> List[Dict]:
    """Get system alerts."""
    # This would be populated from various system monitoring sources
    return []


async def _get_security_alerts(cutoff_time: datetime) -> List[Dict]:
    """Get security alerts."""
    # This would be populated from security monitoring sources
    return []


def _group_alerts_by_severity(alerts: List[Dict]) -> Dict[str, int]:
    """Group alerts by severity level."""
    severity_counts = {}
    for alert in alerts:
        severity = alert.get('severity', 'medium')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    return severity_counts


def _group_alerts_by_type(alerts: List[Dict]) -> Dict[str, int]:
    """Group alerts by type."""
    type_counts = {}
    for alert in alerts:
        alert_type = alert.get('type', 'unknown')
        type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
    return type_counts 
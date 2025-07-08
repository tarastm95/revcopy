"""
Enterprise Performance Monitoring System

This module provides comprehensive performance monitoring capabilities
for production environments with real-time metrics collection,
anomaly detection, and automated optimization recommendations.

Features:
- Request/response time tracking
- Database query performance monitoring
- Memory and CPU usage tracking
- Automatic bottleneck detection
- Performance trend analysis
- Alert system for performance degradation
"""

import time
import asyncio
import psutil
import functools
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import asynccontextmanager

import structlog
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Container for performance measurement data."""
    
    timestamp: datetime
    operation: str
    duration_ms: float
    success: bool
    context: Dict[str, Any] = field(default_factory=dict)
    resource_usage: Optional[Dict[str, float]] = None


@dataclass
class SystemMetrics:
    """System-level performance metrics."""
    
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    timestamp: datetime


class PerformanceCollector:
    """
    Central performance metrics collection system.
    
    Collects and analyzes performance data across all application layers
    with intelligent alerting and optimization recommendations.
    """
    
    def __init__(self, max_metrics: int = 10000, alert_threshold_ms: float = 1000.0):
        self.max_metrics = max_metrics
        self.alert_threshold_ms = alert_threshold_ms
        self.metrics: deque = deque(maxlen=max_metrics)
        self.operation_stats: Dict[str, List[float]] = defaultdict(list)
        self.slow_queries: deque = deque(maxlen=100)
        self.system_metrics: deque = deque(maxlen=1000)
        self.alerts: deque = deque(maxlen=500)
        self._last_system_check = time.time()
        
        # Performance thresholds
        self.thresholds = {
            'api_response_time_ms': 500.0,
            'database_query_time_ms': 100.0,
            'memory_usage_percent': 80.0,
            'cpu_usage_percent': 75.0,
            'disk_usage_percent': 85.0,
        }
        
        # Start background monitoring
        self._monitoring_task = None
        # Don't start monitoring automatically - will be started by app lifecycle
    
    def start_monitoring(self) -> None:
        """Start background system monitoring."""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitor_system())
    
    async def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
    
    def record_metric(self, metric: PerformanceMetric) -> None:
        """Record a performance metric."""
        self.metrics.append(metric)
        self.operation_stats[metric.operation].append(metric.duration_ms)
        
        # Keep only recent stats for each operation (last 1000 measurements)
        if len(self.operation_stats[metric.operation]) > 1000:
            self.operation_stats[metric.operation] = self.operation_stats[metric.operation][-1000:]
        
        # Check for performance alerts
        self._check_performance_alert(metric)
    
    def _check_performance_alert(self, metric: PerformanceMetric) -> None:
        """Check if metric triggers performance alert."""
        if metric.duration_ms > self.alert_threshold_ms:
            alert = {
                'timestamp': metric.timestamp,
                'type': 'slow_operation',
                'operation': metric.operation,
                'duration_ms': metric.duration_ms,
                'threshold_ms': self.alert_threshold_ms,
                'context': metric.context
            }
            self.alerts.append(alert)
            logger.warning(
                "Performance alert triggered",
                operation=metric.operation,
                duration_ms=metric.duration_ms,
                threshold_ms=self.alert_threshold_ms
            )
    
    async def _monitor_system(self) -> None:
        """Background system monitoring task."""
        while True:
            try:
                # Collect system metrics every 30 seconds
                await asyncio.sleep(30)
                metrics = self._collect_system_metrics()
                self.system_metrics.append(metrics)
                
                # Check system-level alerts
                self._check_system_alerts(metrics)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("System monitoring error", error=str(e))
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics."""
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0
        disk_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0
        
        # Network I/O
        network_io = psutil.net_io_counters()
        network_sent_mb = network_io.bytes_sent / (1024 * 1024) if network_io else 0
        network_recv_mb = network_io.bytes_recv / (1024 * 1024) if network_io else 0
        
        # Active connections
        try:
            connections = len(psutil.net_connections(kind='inet'))
        except (psutil.AccessDenied, OSError):
            connections = 0
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            active_connections=connections,
            timestamp=datetime.utcnow()
        )
    
    def _check_system_alerts(self, metrics: SystemMetrics) -> None:
        """Check system metrics for alert conditions."""
        alerts = []
        
        if metrics.cpu_percent > self.thresholds['cpu_usage_percent']:
            alerts.append({
                'type': 'high_cpu_usage',
                'value': metrics.cpu_percent,
                'threshold': self.thresholds['cpu_usage_percent']
            })
        
        if metrics.memory_percent > self.thresholds['memory_usage_percent']:
            alerts.append({
                'type': 'high_memory_usage',
                'value': metrics.memory_percent,
                'threshold': self.thresholds['memory_usage_percent']
            })
        
        for alert in alerts:
            alert['timestamp'] = metrics.timestamp
            self.alerts.append(alert)
            logger.warning("System resource alert", alert_type=alert['type'], **alert)
    
    def get_operation_stats(self, operation: str) -> Dict[str, float]:
        """Get statistical analysis for specific operation."""
        if operation not in self.operation_stats:
            return {}
        
        durations = self.operation_stats[operation]
        if not durations:
            return {}
        
        durations_sorted = sorted(durations)
        count = len(durations)
        
        return {
            'count': count,
            'avg_ms': sum(durations) / count,
            'min_ms': min(durations),
            'max_ms': max(durations),
            'p50_ms': durations_sorted[int(count * 0.5)],
            'p95_ms': durations_sorted[int(count * 0.95)],
            'p99_ms': durations_sorted[int(count * 0.99)]
        }
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get comprehensive performance summary for specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter metrics by time period
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        recent_system = [m for m in self.system_metrics if m.timestamp >= cutoff_time]
        recent_alerts = [a for a in self.alerts if a['timestamp'] >= cutoff_time]
        
        # Calculate operation statistics
        operation_summary = {}
        for operation in set(m.operation for m in recent_metrics):
            operation_metrics = [m for m in recent_metrics if m.operation == operation]
            if operation_metrics:
                durations = [m.duration_ms for m in operation_metrics]
                operation_summary[operation] = {
                    'count': len(durations),
                    'avg_ms': sum(durations) / len(durations),
                    'max_ms': max(durations),
                    'success_rate': sum(1 for m in operation_metrics if m.success) / len(operation_metrics) * 100
                }
        
        # System metrics summary
        system_summary = {}
        if recent_system:
            system_summary = {
                'avg_cpu_percent': sum(m.cpu_percent for m in recent_system) / len(recent_system),
                'avg_memory_percent': sum(m.memory_percent for m in recent_system) / len(recent_system),
                'max_memory_used_mb': max(m.memory_used_mb for m in recent_system),
                'avg_connections': sum(m.active_connections for m in recent_system) / len(recent_system)
            }
        
        return {
            'time_period_hours': hours,
            'total_requests': len(recent_metrics),
            'total_alerts': len(recent_alerts),
            'operations': operation_summary,
            'system_metrics': system_summary,
            'alerts_by_type': self._group_alerts_by_type(recent_alerts)
        }
    
    def _group_alerts_by_type(self, alerts: List[Dict]) -> Dict[str, int]:
        """Group alerts by type and count occurrences."""
        alert_counts = defaultdict(int)
        for alert in alerts:
            alert_counts[alert['type']] += 1
        return dict(alert_counts)
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate intelligent optimization recommendations based on collected data."""
        recommendations = []
        
        # Analyze slow operations
        for operation, stats in self.operation_stats.items():
            if len(stats) < 10:  # Need sufficient data
                continue
            
            avg_duration = sum(stats) / len(stats)
            if avg_duration > self.thresholds.get(f'{operation}_time_ms', 200):
                recommendations.append({
                    'type': 'slow_operation',
                    'operation': operation,
                    'avg_duration_ms': avg_duration,
                    'priority': 'high' if avg_duration > 1000 else 'medium',
                    'recommendation': f'Optimize {operation} - average response time is {avg_duration:.1f}ms'
                })
        
        # Analyze system resource usage
        if self.system_metrics:
            recent_metrics = list(self.system_metrics)[-10:]  # Last 10 measurements
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            
            if avg_cpu > 60:
                recommendations.append({
                    'type': 'high_cpu_usage',
                    'value': avg_cpu,
                    'priority': 'high' if avg_cpu > 80 else 'medium',
                    'recommendation': f'CPU usage is averaging {avg_cpu:.1f}% - consider optimizing compute-intensive operations'
                })
            
            if avg_memory > 70:
                recommendations.append({
                    'type': 'high_memory_usage',
                    'value': avg_memory,
                    'priority': 'high' if avg_memory > 85 else 'medium',
                    'recommendation': f'Memory usage is averaging {avg_memory:.1f}% - review memory leaks and caching strategies'
                })
        
        return recommendations


# Global performance collector instance
performance_collector = PerformanceCollector()


def monitor_performance(operation: str = None, context: Dict[str, Any] = None):
    """
    Decorator for monitoring function/method performance.
    
    Args:
        operation: Operation name (defaults to function name)
        context: Additional context to include in metrics
    """
    def decorator(func: Callable) -> Callable:
        operation_name = operation or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error = None
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    metric_context = dict(context or {})
                    if error:
                        metric_context['error'] = error
                    
                    metric = PerformanceMetric(
                        timestamp=datetime.utcnow(),
                        operation=operation_name,
                        duration_ms=duration_ms,
                        success=success,
                        context=metric_context
                    )
                    performance_collector.record_metric(metric)
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    metric_context = dict(context or {})
                    if error:
                        metric_context['error'] = error
                    
                    metric = PerformanceMetric(
                        timestamp=datetime.utcnow(),
                        operation=operation_name,
                        duration_ms=duration_ms,
                        success=success,
                        context=metric_context
                    )
                    performance_collector.record_metric(metric)
            
            return sync_wrapper
    
    return decorator


@asynccontextmanager
async def performance_context(operation: str, context: Dict[str, Any] = None):
    """
    Async context manager for monitoring code block performance.
    
    Usage:
        async with performance_context("database_query", {"table": "users"}):
            result = await db.execute(query)
    """
    start_time = time.time()
    success = True
    error = None
    
    try:
        yield
    except Exception as e:
        success = False
        error = str(e)
        raise
    finally:
        duration_ms = (time.time() - start_time) * 1000
        metric_context = dict(context or {})
        if error:
            metric_context['error'] = error
        
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            context=metric_context
        )
        performance_collector.record_metric(metric)


class DatabaseQueryMonitor:
    """Monitor database query performance and detect slow queries."""
    
    def __init__(self, slow_query_threshold_ms: float = 100.0):
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.query_stats: Dict[str, List[float]] = defaultdict(list)
    
    def setup_monitoring(self, engine: Engine) -> None:
        """Setup SQLAlchemy event listeners for query monitoring."""
        
        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - context._query_start_time
            duration_ms = total_time * 1000
            
            # Record query performance
            query_type = statement.strip().split()[0].upper()
            self.query_stats[query_type].append(duration_ms)
            
            # Log slow queries
            if duration_ms > self.slow_query_threshold_ms:
                logger.warning(
                    "Slow database query detected",
                    duration_ms=duration_ms,
                    query_type=query_type,
                    statement=statement[:200] + "..." if len(statement) > 200 else statement
                )
                
                # Record as performance metric
                metric = PerformanceMetric(
                    timestamp=datetime.utcnow(),
                    operation=f"database.{query_type.lower()}",
                    duration_ms=duration_ms,
                    success=True,
                    context={
                        'query_type': query_type,
                        'statement_preview': statement[:100]
                    }
                )
                performance_collector.record_metric(metric)
    
    def get_query_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all monitored query types."""
        stats = {}
        for query_type, durations in self.query_stats.items():
            if durations:
                stats[query_type] = {
                    'count': len(durations),
                    'avg_ms': sum(durations) / len(durations),
                    'max_ms': max(durations),
                    'min_ms': min(durations)
                }
        return stats


# Global database query monitor
db_query_monitor = DatabaseQueryMonitor()


# Cleanup function for graceful shutdown
async def cleanup_performance_monitoring():
    """Cleanup performance monitoring on application shutdown."""
    await performance_collector.stop_monitoring()
    logger.info("Performance monitoring stopped") 
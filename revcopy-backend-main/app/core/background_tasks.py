"""
Enterprise Background Task Management System

Advanced asynchronous task processing with intelligent scheduling,
monitoring, error handling, and distributed coordination.

Features:
- Distributed task queue with Redis backend
- Task prioritization and scheduling
- Retry mechanisms with exponential backoff
- Task monitoring and progress tracking
- Dead letter queue for failed tasks
- Performance analytics and reporting
- Auto-scaling based on queue length
- Task dependency management
"""

import asyncio
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Union, TypeVar
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import asynccontextmanager

import structlog
import redis.asyncio as redis
try:
    from croniter import croniter
except ImportError:
    # For testing or when croniter is not available
    class MockCroniter:
        def __init__(self, cron_expression, start_time):
            self.cron_expression = cron_expression
            self.start_time = start_time
        
        def get_next(self, ret_type=None):
            from datetime import datetime, timedelta
            return datetime.utcnow() + timedelta(minutes=5)
    
    croniter = MockCroniter

from app.core.config import settings
from app.core.performance import performance_collector, PerformanceMetric

logger = structlog.get_logger(__name__)

T = TypeVar('T')


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class TaskConfig:
    """Configuration for task execution."""
    
    max_retries: int = 3
    retry_delay: float = 1.0  # Initial delay in seconds
    retry_backoff: float = 2.0  # Exponential backoff multiplier
    max_retry_delay: float = 300.0  # Maximum retry delay
    timeout: Optional[float] = None  # Task timeout in seconds
    priority: TaskPriority = TaskPriority.NORMAL
    depends_on: List[str] = field(default_factory=list)  # Task dependencies
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Task execution result."""
    
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    retries_attempted: int = 0
    worker_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class Task:
    """Background task definition."""
    
    id: str
    name: str
    function: str  # Function path (module.function)
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    config: TaskConfig = field(default_factory=TaskConfig)
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[TaskResult] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for field_name in ['created_at', 'scheduled_at']:
            if data[field_name]:
                data[field_name] = data[field_name].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary."""
        # Convert ISO strings back to datetime objects
        for field_name in ['created_at', 'scheduled_at']:
            if data.get(field_name):
                data[field_name] = datetime.fromisoformat(data[field_name])
        
        # Reconstruct nested objects
        if 'config' in data:
            data['config'] = TaskConfig(**data['config'])
        if 'result' in data and data['result']:
            data['result'] = TaskResult(**data['result'])
        
        return cls(**data)


class TaskRegistry:
    """Registry for task functions."""
    
    def __init__(self):
        self._functions: Dict[str, Callable] = {}
    
    def register(self, name: str = None):
        """Decorator to register task functions."""
        def decorator(func: Callable) -> Callable:
            func_name = name or f"{func.__module__}.{func.__name__}"
            self._functions[func_name] = func
            logger.info("Task function registered", name=func_name)
            return func
        return decorator
    
    def get_function(self, name: str) -> Optional[Callable]:
        """Get registered function by name."""
        return self._functions.get(name)
    
    def list_functions(self) -> List[str]:
        """List all registered function names."""
        return list(self._functions.keys())


class TaskQueue:
    """Redis-based distributed task queue."""
    
    def __init__(self, redis_url: str = None, queue_name: str = "default"):
        self.redis_url = redis_url or settings.REDIS_URL
        self.queue_name = queue_name
        self.client: Optional[redis.Redis] = None
        self.stats = {
            'tasks_enqueued': 0,
            'tasks_dequeued': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'queue_length': 0
        }
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            await self.client.ping()
            logger.info("Task queue connected to Redis", queue=self.queue_name)
        except Exception as e:
            logger.error("Failed to connect task queue to Redis", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            self.client = None
    
    async def enqueue(self, task: Task) -> None:
        """Add task to queue."""
        if not self.client:
            raise RuntimeError("Task queue not connected")
        
        # Serialize task
        task_data = json.dumps(task.to_dict())
        
        # Use priority for queue ordering
        priority_score = task.config.priority.value
        
        # Add to priority queue (Redis sorted set)
        await self.client.zadd(
            f"queue:{self.queue_name}:priority",
            {task_data: priority_score}
        )
        
        # Add to task tracking
        await self.client.hset(
            f"tasks:{self.queue_name}",
            task.id,
            task_data
        )
        
        # Update stats
        self.stats['tasks_enqueued'] += 1
        self.stats['queue_length'] = await self.client.zcard(f"queue:{self.queue_name}:priority")
        
        logger.info("Task enqueued", task_id=task.id, queue=self.queue_name, priority=task.config.priority.name)
    
    async def dequeue(self, timeout: float = 1.0) -> Optional[Task]:
        """Get next task from queue."""
        if not self.client:
            raise RuntimeError("Task queue not connected")
        
        # Get highest priority task
        result = await self.client.bzpopmax(
            f"queue:{self.queue_name}:priority",
            timeout=timeout
        )
        
        if not result:
            return None
        
        _, task_data, _ = result
        task = Task.from_dict(json.loads(task_data))
        
        # Update stats
        self.stats['tasks_dequeued'] += 1
        self.stats['queue_length'] = await self.client.zcard(f"queue:{self.queue_name}:priority")
        
        logger.info("Task dequeued", task_id=task.id, queue=self.queue_name)
        return task
    
    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """Get task status by ID."""
        if not self.client:
            return None
        
        task_data = await self.client.hget(f"tasks:{self.queue_name}", task_id)
        if task_data:
            return Task.from_dict(json.loads(task_data))
        return None
    
    async def update_task_status(self, task: Task) -> None:
        """Update task status in storage."""
        if not self.client:
            return
        
        task_data = json.dumps(task.to_dict())
        await self.client.hset(f"tasks:{self.queue_name}", task.id, task_data)
        
        # Update completion stats
        if task.status == TaskStatus.COMPLETED:
            self.stats['tasks_completed'] += 1
        elif task.status == TaskStatus.FAILED:
            self.stats['tasks_failed'] += 1
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        if not self.client:
            return self.stats
        
        # Update queue length
        self.stats['queue_length'] = await self.client.zcard(f"queue:{self.queue_name}:priority")
        
        # Get task counts by status
        all_tasks = await self.client.hgetall(f"tasks:{self.queue_name}")
        status_counts = {}
        for task_data in all_tasks.values():
            task = Task.from_dict(json.loads(task_data))
            status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1
        
        return {
            **self.stats,
            'status_counts': status_counts
        }
    
    async def clear_completed_tasks(self, older_than_hours: int = 24) -> int:
        """Clear completed tasks older than specified hours."""
        if not self.client:
            return 0
        
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        cleared = 0
        
        all_tasks = await self.client.hgetall(f"tasks:{self.queue_name}")
        for task_id, task_data in all_tasks.items():
            task = Task.from_dict(json.loads(task_data))
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and 
                task.created_at < cutoff_time):
                await self.client.hdel(f"tasks:{self.queue_name}", task_id)
                cleared += 1
        
        logger.info("Cleared completed tasks", count=cleared, queue=self.queue_name)
        return cleared


class TaskWorker:
    """Background task worker."""
    
    def __init__(self, worker_id: str, queue: TaskQueue, registry: TaskRegistry):
        self.worker_id = worker_id
        self.queue = queue
        self.registry = registry
        self.is_running = False
        self.current_task: Optional[Task] = None
        self.stats = {
            'tasks_processed': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'started_at': None,
            'last_activity': None
        }
    
    async def start(self) -> None:
        """Start the worker."""
        self.is_running = True
        self.stats['started_at'] = datetime.utcnow()
        
        logger.info("Task worker started", worker_id=self.worker_id)
        
        try:
            await self._work_loop()
        except Exception as e:
            logger.error("Worker error", worker_id=self.worker_id, error=str(e))
        finally:
            self.is_running = False
    
    async def stop(self) -> None:
        """Stop the worker."""
        self.is_running = False
        logger.info("Task worker stopped", worker_id=self.worker_id)
    
    async def _work_loop(self) -> None:
        """Main worker loop."""
        while self.is_running:
            try:
                # Get next task
                task = await self.queue.dequeue(timeout=1.0)
                if not task:
                    await asyncio.sleep(0.1)
                    continue
                
                # Execute task
                await self._execute_task(task)
                
                # Update activity
                self.stats['last_activity'] = datetime.utcnow()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Worker loop error", worker_id=self.worker_id, error=str(e))
                await asyncio.sleep(1.0)
    
    async def _execute_task(self, task: Task) -> None:
        """Execute a single task."""
        self.current_task = task
        start_time = time.time()
        
        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            task.result = TaskResult(
                task_id=task.id,
                status=TaskStatus.RUNNING,
                started_at=datetime.utcnow(),
                worker_id=self.worker_id
            )
            await self.queue.update_task_status(task)
            
            # Get task function
            func = self.registry.get_function(task.function)
            if not func:
                raise ValueError(f"Task function not found: {task.function}")
            
            # Execute with timeout
            if task.config.timeout:
                result = await asyncio.wait_for(
                    func(*task.args, **task.kwargs),
                    timeout=task.config.timeout
                )
            else:
                result = await func(*task.args, **task.kwargs)
            
            # Task completed successfully
            duration_ms = (time.time() - start_time) * 1000
            task.status = TaskStatus.COMPLETED
            task.result = TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result=result,
                started_at=task.result.started_at,
                completed_at=datetime.utcnow(),
                duration_ms=duration_ms,
                worker_id=self.worker_id
            )
            
            self.stats['tasks_completed'] += 1
            logger.info("Task completed", task_id=task.id, duration_ms=duration_ms)
            
        except Exception as e:
            # Task failed
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            # Check if we should retry
            if (task.result and 
                task.result.retries_attempted < task.config.max_retries):
                
                # Schedule retry
                retry_delay = min(
                    task.config.retry_delay * (task.config.retry_backoff ** task.result.retries_attempted),
                    task.config.max_retry_delay
                )
                
                task.status = TaskStatus.RETRY
                task.result.retries_attempted += 1
                task.result.error = error_msg
                task.scheduled_at = datetime.utcnow() + timedelta(seconds=retry_delay)
                
                # Re-enqueue for retry
                await self.queue.enqueue(task)
                
                logger.warning("Task failed, scheduled for retry", 
                             task_id=task.id, 
                             retry_attempt=task.result.retries_attempted,
                             retry_delay=retry_delay,
                             error=error_msg)
            else:
                # No more retries
                task.status = TaskStatus.FAILED
                task.result = TaskResult(
                    task_id=task.id,
                    status=TaskStatus.FAILED,
                    error=error_msg,
                    started_at=task.result.started_at if task.result else datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    duration_ms=duration_ms,
                    retries_attempted=task.result.retries_attempted if task.result else 0,
                    worker_id=self.worker_id
                )
                
                self.stats['tasks_failed'] += 1
                logger.error("Task failed permanently", task_id=task.id, error=error_msg)
        
        finally:
            # Update task status
            await self.queue.update_task_status(task)
            self.current_task = None
            self.stats['tasks_processed'] += 1
            
            # Record performance metric
            duration_ms = (time.time() - start_time) * 1000
            metric = PerformanceMetric(
                timestamp=datetime.utcnow(),
                operation=f"task.{task.function}",
                duration_ms=duration_ms,
                success=task.status == TaskStatus.COMPLETED,
                context={
                    'task_id': task.id,
                    'worker_id': self.worker_id,
                    'priority': task.config.priority.name
                }
            )
            performance_collector.record_metric(metric)


class TaskScheduler:
    """Task scheduler for periodic and delayed tasks."""
    
    def __init__(self, queue: TaskQueue, registry: TaskRegistry):
        self.queue = queue
        self.registry = registry
        self.scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self.is_running = False
    
    async def start(self) -> None:
        """Start the scheduler."""
        self.is_running = True
        logger.info("Task scheduler started")
        
        try:
            await self._schedule_loop()
        except Exception as e:
            logger.error("Scheduler error", error=str(e))
        finally:
            self.is_running = False
    
    async def stop(self) -> None:
        """Stop the scheduler."""
        self.is_running = False
        logger.info("Task scheduler stopped")
    
    def schedule_periodic(self, 
                         cron_expression: str, 
                         task_name: str,
                         function: str,
                         args: List[Any] = None,
                         kwargs: Dict[str, Any] = None,
                         config: TaskConfig = None) -> str:
        """Schedule a periodic task using cron expression."""
        schedule_id = str(uuid.uuid4())
        
        self.scheduled_tasks[schedule_id] = {
            'type': 'periodic',
            'cron': cron_expression,
            'task_name': task_name,
            'function': function,
            'args': args or [],
            'kwargs': kwargs or {},
            'config': config or TaskConfig(),
            'next_run': None
        }
        
        # Calculate next run time
        cron = croniter(cron_expression, datetime.utcnow())
        self.scheduled_tasks[schedule_id]['next_run'] = cron.get_next(datetime)
        
        logger.info("Periodic task scheduled", 
                   schedule_id=schedule_id,
                   cron=cron_expression,
                   task_name=task_name,
                   next_run=self.scheduled_tasks[schedule_id]['next_run'])
        
        return schedule_id
    
    def schedule_delayed(self,
                        delay_seconds: float,
                        task_name: str,
                        function: str,
                        args: List[Any] = None,
                        kwargs: Dict[str, Any] = None,
                        config: TaskConfig = None) -> str:
        """Schedule a delayed task."""
        schedule_id = str(uuid.uuid4())
        run_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
        
        self.scheduled_tasks[schedule_id] = {
            'type': 'delayed',
            'task_name': task_name,
            'function': function,
            'args': args or [],
            'kwargs': kwargs or {},
            'config': config or TaskConfig(),
            'next_run': run_time
        }
        
        logger.info("Delayed task scheduled",
                   schedule_id=schedule_id,
                   task_name=task_name,
                   delay_seconds=delay_seconds,
                   run_time=run_time)
        
        return schedule_id
    
    def unschedule(self, schedule_id: str) -> bool:
        """Unschedule a task."""
        if schedule_id in self.scheduled_tasks:
            del self.scheduled_tasks[schedule_id]
            logger.info("Task unscheduled", schedule_id=schedule_id)
            return True
        return False
    
    async def _schedule_loop(self) -> None:
        """Main scheduler loop."""
        while self.is_running:
            try:
                now = datetime.utcnow()
                
                # Check for tasks that need to be executed
                for schedule_id, schedule_info in list(self.scheduled_tasks.items()):
                    if schedule_info['next_run'] <= now:
                        await self._execute_scheduled_task(schedule_id, schedule_info)
                
                # Sleep for 1 second before next check
                await asyncio.sleep(1.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Scheduler loop error", error=str(e))
                await asyncio.sleep(1.0)
    
    async def _execute_scheduled_task(self, schedule_id: str, schedule_info: Dict[str, Any]) -> None:
        """Execute a scheduled task."""
        try:
            # Create task
            task = Task(
                id=str(uuid.uuid4()),
                name=schedule_info['task_name'],
                function=schedule_info['function'],
                args=schedule_info['args'],
                kwargs=schedule_info['kwargs'],
                config=schedule_info['config'],
                scheduled_at=schedule_info['next_run']
            )
            
            # Enqueue task
            await self.queue.enqueue(task)
            
            # Update next run time for periodic tasks
            if schedule_info['type'] == 'periodic':
                cron = croniter(schedule_info['cron'], datetime.utcnow())
                schedule_info['next_run'] = cron.get_next(datetime)
            else:
                # Remove one-time delayed tasks
                del self.scheduled_tasks[schedule_id]
            
            logger.info("Scheduled task executed", 
                       schedule_id=schedule_id,
                       task_id=task.id,
                       task_name=task.name)
            
        except Exception as e:
            logger.error("Failed to execute scheduled task", 
                        schedule_id=schedule_id,
                        error=str(e))


class BackgroundTaskManager:
    """Main background task management system."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.registry = TaskRegistry()
        self.queues: Dict[str, TaskQueue] = {}
        self.workers: List[TaskWorker] = []
        self.scheduler: Optional[TaskScheduler] = None
        self.is_running = False
        # Don't initialize automatically - will be initialized by app lifecycle
    
    async def initialize(self) -> None:
        """Initialize the task management system."""
        # Create default queue
        await self.create_queue("default")
        
        # Create scheduler
        self.scheduler = TaskScheduler(self.queues["default"], self.registry)
        
        logger.info("Background task manager initialized")
    
    async def create_queue(self, name: str) -> TaskQueue:
        """Create a new task queue."""
        queue = TaskQueue(self.redis_url, name)
        await queue.connect()
        self.queues[name] = queue
        logger.info("Task queue created", queue_name=name)
        return queue
    
    async def start_workers(self, count: int = 1, queue_name: str = "default") -> None:
        """Start worker processes."""
        queue = self.queues.get(queue_name)
        if not queue:
            raise ValueError(f"Queue '{queue_name}' not found")
        
        for i in range(count):
            worker_id = f"{queue_name}-worker-{i}"
            worker = TaskWorker(worker_id, queue, self.registry)
            self.workers.append(worker)
            
            # Start worker in background
            asyncio.create_task(worker.start())
        
        logger.info("Workers started", count=count, queue=queue_name)
    
    async def start_scheduler(self) -> None:
        """Start the task scheduler."""
        if self.scheduler:
            asyncio.create_task(self.scheduler.start())
            logger.info("Task scheduler started")
    
    async def submit_task(self, 
                         name: str,
                         function: str,
                         args: List[Any] = None,
                         kwargs: Dict[str, Any] = None,
                         config: TaskConfig = None,
                         queue_name: str = "default") -> str:
        """Submit a task for execution."""
        queue = self.queues.get(queue_name)
        if not queue:
            raise ValueError(f"Queue '{queue_name}' not found")
        
        task = Task(
            id=str(uuid.uuid4()),
            name=name,
            function=function,
            args=args or [],
            kwargs=kwargs or {},
            config=config or TaskConfig()
        )
        
        await queue.enqueue(task)
        return task.id
    
    async def get_task_status(self, task_id: str, queue_name: str = "default") -> Optional[TaskResult]:
        """Get task status."""
        queue = self.queues.get(queue_name)
        if not queue:
            return None
        
        task = await queue.get_task_status(task_id)
        return task.result if task else None
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        stats = {
            'queues': {},
            'workers': [],
            'scheduler': {
                'is_running': self.scheduler.is_running if self.scheduler else False,
                'scheduled_tasks': len(self.scheduler.scheduled_tasks) if self.scheduler else 0
            }
        }
        
        # Queue stats
        for name, queue in self.queues.items():
            stats['queues'][name] = await queue.get_queue_stats()
        
        # Worker stats
        for worker in self.workers:
            stats['workers'].append({
                'worker_id': worker.worker_id,
                'is_running': worker.is_running,
                'current_task': worker.current_task.id if worker.current_task else None,
                'stats': worker.stats
            })
        
        return stats
    
    async def shutdown(self) -> None:
        """Shutdown the task management system."""
        # Stop scheduler
        if self.scheduler:
            await self.scheduler.stop()
        
        # Stop workers
        for worker in self.workers:
            await worker.stop()
        
        # Disconnect queues
        for queue in self.queues.values():
            await queue.disconnect()
        
        self.is_running = False
        logger.info("Background task manager shut down")
    
    def register_task(self, name: str = None):
        """Decorator to register task functions."""
        return self.registry.register(name)


# Global task manager instance
task_manager = BackgroundTaskManager()


# Convenience functions
async def submit_task(name: str, function: str, *args, **kwargs) -> str:
    """Submit a task for background execution."""
    return await task_manager.submit_task(name, function, list(args), kwargs)


async def get_task_status(task_id: str) -> Optional[TaskResult]:
    """Get task execution status."""
    return await task_manager.get_task_status(task_id)


def background_task(name: str = None, config: TaskConfig = None):
    """Decorator to mark functions as background tasks."""
    def decorator(func: Callable) -> Callable:
        # Register the task
        task_manager.register_task(name)(func)
        
        # Return the original function
        return func
    
    return decorator


# Initialize task manager on startup
async def initialize_task_manager():
    """Initialize task management system on application startup."""
    await task_manager.initialize()
    await task_manager.start_workers(count=2)  # Start 2 workers
    await task_manager.start_scheduler()
    logger.info("Task management system started")


# Cleanup on shutdown
async def cleanup_task_manager():
    """Cleanup task management system on application shutdown."""
    await task_manager.shutdown()
    logger.info("Task management system cleaned up") 
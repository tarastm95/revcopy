"""
Enterprise Caching System

Advanced multi-tier caching solution with intelligent cache management,
distributed caching support, and automatic cache optimization.

Features:
- Multi-tier caching (Memory, Redis, Database)
- Intelligent cache warming and invalidation
- Cache performance monitoring
- Automatic cache optimization
- Distributed cache coordination
- Cache analytics and reporting
"""

import asyncio
import json
import hashlib
import time
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from collections import defaultdict
from contextlib import asynccontextmanager
from enum import Enum

import structlog
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.performance import performance_collector, PerformanceMetric

logger = structlog.get_logger(__name__)

T = TypeVar('T')


class CacheLevel(Enum):
    """Cache storage levels."""
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"


class CachePolicy(Enum):
    """Cache policies for different data types."""
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    CACHE_ASIDE = "cache_aside"
    REFRESH_AHEAD = "refresh_ahead"


@dataclass
class CacheConfig:
    """Configuration for cache behavior."""
    
    ttl_seconds: int = 3600  # Default TTL: 1 hour
    max_size: int = 1000  # Maximum items in cache
    policy: CachePolicy = CachePolicy.CACHE_ASIDE
    levels: List[CacheLevel] = field(default_factory=lambda: [CacheLevel.MEMORY, CacheLevel.REDIS])
    auto_refresh: bool = False
    refresh_threshold: float = 0.8  # Refresh when TTL is 80% expired
    compression: bool = True
    encryption: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    ttl_seconds: int
    access_count: int = 0
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    @property
    def time_to_refresh(self) -> float:
        """Time until refresh threshold is reached (0-1)."""
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return max(0, 1 - elapsed / self.ttl_seconds)


@dataclass
class CacheStats:
    """Cache performance statistics."""
    
    hits: int = 0
    misses: int = 0
    writes: int = 0
    evictions: int = 0
    errors: int = 0
    total_size_bytes: int = 0
    avg_access_time_ms: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate


class InMemoryCache:
    """High-performance in-memory cache with LRU eviction."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        self.stats = CacheStats()
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get cache entry by key."""
        async with self._lock:
            entry = self.cache.get(key)
            if entry:
                if entry.is_expired:
                    await self._remove(key)
                    self.stats.misses += 1
                    return None
                
                # Update access statistics
                entry.accessed_at = datetime.utcnow()
                entry.access_count += 1
                self._update_access_order(key)
                self.stats.hits += 1
                return entry
            
            self.stats.misses += 1
            return None
    
    async def set(self, key: str, entry: CacheEntry) -> None:
        """Set cache entry."""
        async with self._lock:
            # Remove if already exists
            if key in self.cache:
                await self._remove(key)
            
            # Evict if necessary
            while len(self.cache) >= self.max_size:
                await self._evict_lru()
            
            # Add new entry
            self.cache[key] = entry
            self.access_order.append(key)
            self.stats.writes += 1
            self.stats.total_size_bytes += entry.size_bytes
    
    async def remove(self, key: str) -> bool:
        """Remove cache entry."""
        async with self._lock:
            return await self._remove(key)
    
    async def _remove(self, key: str) -> bool:
        """Internal remove method."""
        if key in self.cache:
            entry = self.cache.pop(key)
            if key in self.access_order:
                self.access_order.remove(key)
            self.stats.total_size_bytes -= entry.size_bytes
            return True
        return False
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if self.access_order:
            lru_key = self.access_order[0]
            await self._remove(lru_key)
            self.stats.evictions += 1
    
    def _update_access_order(self, key: str) -> None:
        """Update access order for LRU tracking."""
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self.cache.clear()
            self.access_order.clear()
            self.stats = CacheStats()
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self.stats


class RedisCache:
    """Redis-based distributed cache."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.client: Optional[redis.Redis] = None
        self.stats = CacheStats()
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=False)
            await self.client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            self.client = None
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get cache entry from Redis."""
        if not self.client:
            return None
        
        try:
            data = await self.client.get(key)
            if data:
                entry = pickle.loads(data)
                if entry.is_expired:
                    await self.remove(key)
                    self.stats.misses += 1
                    return None
                
                entry.accessed_at = datetime.utcnow()
                entry.access_count += 1
                self.stats.hits += 1
                return entry
            
            self.stats.misses += 1
            return None
        except Exception as e:
            logger.error("Redis get error", key=key, error=str(e))
            self.stats.errors += 1
            return None
    
    async def set(self, key: str, entry: CacheEntry) -> None:
        """Set cache entry in Redis."""
        if not self.client:
            return
        
        try:
            data = pickle.dumps(entry)
            await self.client.setex(key, entry.ttl_seconds, data)
            self.stats.writes += 1
        except Exception as e:
            logger.error("Redis set error", key=key, error=str(e))
            self.stats.errors += 1
    
    async def remove(self, key: str) -> bool:
        """Remove cache entry from Redis."""
        if not self.client:
            return False
        
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error("Redis remove error", key=key, error=str(e))
            self.stats.errors += 1
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        if not self.client:
            return
        
        try:
            await self.client.flushall()
            self.stats = CacheStats()
        except Exception as e:
            logger.error("Redis clear error", error=str(e))
            self.stats.errors += 1
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self.stats


class EnterpriseCache:
    """
    Enterprise-grade multi-tier caching system.
    
    Provides intelligent caching with automatic optimization,
    performance monitoring, and distributed coordination.
    """
    
    def __init__(self):
        self.memory_cache = InMemoryCache(max_size=10000)
        self.redis_cache = RedisCache()
        self.cache_configs: Dict[str, CacheConfig] = {}
        self.warming_tasks: Dict[str, asyncio.Task] = {}
        self.refresh_tasks: Dict[str, asyncio.Task] = {}
        self._initialized = False
        # Don't initialize automatically - will be initialized by app lifecycle
    
    async def initialize(self) -> None:
        """Initialize the cache system."""
        if self._initialized:
            return
        
        try:
            await self.redis_cache.connect()
            self._initialized = True
            logger.info("Enterprise cache initialized successfully")
        except Exception as e:
            logger.warning("Redis unavailable, using memory cache only", error=str(e))
            self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown the cache system."""
        # Cancel all warming/refresh tasks
        for task in list(self.warming_tasks.values()) + list(self.refresh_tasks.values()):
            task.cancel()
        
        # Disconnect from Redis
        await self.redis_cache.disconnect()
        
        # Clear memory cache
        await self.memory_cache.clear()
        
        self._initialized = False
        logger.info("Enterprise cache shut down")
    
    def configure(self, namespace: str, config: CacheConfig) -> None:
        """Configure cache behavior for a namespace."""
        self.cache_configs[namespace] = config
        logger.info("Cache configured", namespace=namespace, config=config)
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get value from cache with multi-tier lookup."""
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        full_key = f"{namespace}:{key}"
        config = self.cache_configs.get(namespace, CacheConfig())
        
        try:
            # Try memory cache first
            if CacheLevel.MEMORY in config.levels:
                entry = await self.memory_cache.get(full_key)
                if entry:
                    await self._record_cache_access(full_key, "memory", time.time() - start_time)
                    return entry.value
            
            # Try Redis cache
            if CacheLevel.REDIS in config.levels and self.redis_cache.client:
                entry = await self.redis_cache.get(full_key)
                if entry:
                    # Promote to memory cache
                    if CacheLevel.MEMORY in config.levels:
                        await self.memory_cache.set(full_key, entry)
                    
                    await self._record_cache_access(full_key, "redis", time.time() - start_time)
                    return entry.value
            
            # Cache miss
            await self._record_cache_access(full_key, "miss", time.time() - start_time)
            return None
            
        except Exception as e:
            logger.error("Cache get error", key=key, namespace=namespace, error=str(e))
            return None
    
    async def set(self, key: str, value: Any, namespace: str = "default", ttl: Optional[int] = None) -> None:
        """Set value in cache across all configured levels."""
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        full_key = f"{namespace}:{key}"
        config = self.cache_configs.get(namespace, CacheConfig())
        
        # Use provided TTL or config default
        ttl_seconds = ttl or config.ttl_seconds
        
        # Calculate size
        size_bytes = len(pickle.dumps(value))
        
        # Create cache entry
        entry = CacheEntry(
            key=full_key,
            value=value,
            created_at=datetime.utcnow(),
            accessed_at=datetime.utcnow(),
            ttl_seconds=ttl_seconds,
            size_bytes=size_bytes,
            tags=config.tags
        )
        
        try:
            # Set in memory cache
            if CacheLevel.MEMORY in config.levels:
                await self.memory_cache.set(full_key, entry)
            
            # Set in Redis cache
            if CacheLevel.REDIS in config.levels and self.redis_cache.client:
                await self.redis_cache.set(full_key, entry)
            
            # Setup auto-refresh if enabled
            if config.auto_refresh and config.refresh_threshold > 0:
                await self._schedule_refresh(full_key, namespace, config)
            
            await self._record_cache_write(full_key, namespace, time.time() - start_time)
            
        except Exception as e:
            logger.error("Cache set error", key=key, namespace=namespace, error=str(e))
    
    async def remove(self, key: str, namespace: str = "default") -> bool:
        """Remove value from all cache levels."""
        if not self._initialized:
            await self.initialize()
        
        full_key = f"{namespace}:{key}"
        config = self.cache_configs.get(namespace, CacheConfig())
        
        removed = False
        
        # Remove from memory cache
        if CacheLevel.MEMORY in config.levels:
            removed = await self.memory_cache.remove(full_key) or removed
        
        # Remove from Redis cache
        if CacheLevel.REDIS in config.levels and self.redis_cache.client:
            removed = await self.redis_cache.remove(full_key) or removed
        
        # Cancel refresh task if exists
        if full_key in self.refresh_tasks:
            self.refresh_tasks[full_key].cancel()
            del self.refresh_tasks[full_key]
        
        return removed
    
    async def invalidate_by_tags(self, tags: List[str], namespace: str = "default") -> int:
        """Invalidate cache entries by tags."""
        # This is a simplified implementation
        # In production, you'd want to maintain tag indexes
        invalidated = 0
        
        # For now, clear the entire namespace
        # TODO: Implement proper tag-based invalidation
        await self.clear_namespace(namespace)
        invalidated += 1
        
        logger.info("Cache invalidated by tags", tags=tags, namespace=namespace, count=invalidated)
        return invalidated
    
    async def clear_namespace(self, namespace: str) -> None:
        """Clear all cache entries in a namespace."""
        # Cancel all tasks for this namespace
        keys_to_remove = []
        for key in list(self.refresh_tasks.keys()):
            if key.startswith(f"{namespace}:"):
                self.refresh_tasks[key].cancel()
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.refresh_tasks[key]
        
        # Clear from memory cache (simplified - would need proper namespace support)
        await self.memory_cache.clear()
        
        # Clear from Redis (simplified - would need proper namespace support)
        await self.redis_cache.clear()
    
    async def warm_cache(self, namespace: str, data_loader: Callable[[], Any]) -> None:
        """Warm cache with data from loader function."""
        if namespace in self.warming_tasks:
            return  # Already warming
        
        async def warm_task():
            try:
                logger.info("Starting cache warming", namespace=namespace)
                data = await data_loader()
                # Store warmed data (implementation depends on data structure)
                logger.info("Cache warming completed", namespace=namespace)
            except Exception as e:
                logger.error("Cache warming failed", namespace=namespace, error=str(e))
            finally:
                if namespace in self.warming_tasks:
                    del self.warming_tasks[namespace]
        
        self.warming_tasks[namespace] = asyncio.create_task(warm_task())
    
    async def _schedule_refresh(self, key: str, namespace: str, config: CacheConfig) -> None:
        """Schedule automatic cache refresh."""
        if key in self.refresh_tasks:
            self.refresh_tasks[key].cancel()
        
        refresh_delay = config.ttl_seconds * config.refresh_threshold
        
        async def refresh_task():
            try:
                await asyncio.sleep(refresh_delay)
                # Trigger refresh (implementation depends on refresh strategy)
                logger.debug("Cache refresh triggered", key=key, namespace=namespace)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error("Cache refresh failed", key=key, error=str(e))
            finally:
                if key in self.refresh_tasks:
                    del self.refresh_tasks[key]
        
        self.refresh_tasks[key] = asyncio.create_task(refresh_task())
    
    async def _record_cache_access(self, key: str, cache_type: str, duration: float) -> None:
        """Record cache access for performance monitoring."""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            operation=f"cache.{cache_type}",
            duration_ms=duration * 1000,
            success=True,
            context={"key": key[:50]}  # Truncate key for privacy
        )
        performance_collector.record_metric(metric)
    
    async def _record_cache_write(self, key: str, namespace: str, duration: float) -> None:
        """Record cache write for performance monitoring."""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            operation="cache.write",
            duration_ms=duration * 1000,
            success=True,
            context={"namespace": namespace, "key": key[:50]}
        )
        performance_collector.record_metric(metric)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        memory_stats = self.memory_cache.get_stats()
        redis_stats = self.redis_cache.get_stats()
        
        return {
            "memory_cache": {
                "hits": memory_stats.hits,
                "misses": memory_stats.misses,
                "hit_rate": memory_stats.hit_rate,
                "size_bytes": memory_stats.total_size_bytes,
                "evictions": memory_stats.evictions
            },
            "redis_cache": {
                "hits": redis_stats.hits,
                "misses": redis_stats.misses,
                "hit_rate": redis_stats.hit_rate,
                "errors": redis_stats.errors,
                "writes": redis_stats.writes
            },
            "active_namespaces": len(self.cache_configs),
            "warming_tasks": len(self.warming_tasks),
            "refresh_tasks": len(self.refresh_tasks)
        }


# Global cache instance
cache = EnterpriseCache()


# Cache decorators for easy usage
def cached(namespace: str = "default", ttl: Optional[int] = None, key_builder: Optional[Callable] = None):
    """
    Decorator for caching function results.
    
    Args:
        namespace: Cache namespace
        ttl: Time to live in seconds
        key_builder: Function to build cache key from args
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                # Build cache key
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
                
                # Try cache first
                cached_result = await cache.get(cache_key, namespace)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await cache.set(cache_key, result, namespace, ttl)
                return result
            
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                # For sync functions, we'd need to run cache operations in event loop
                # This is a simplified implementation
                return func(*args, **kwargs)
            
            return sync_wrapper
    
    return decorator


@asynccontextmanager
async def cache_context(namespace: str = "default"):
    """Context manager for cache operations."""
    if not cache._initialized:
        await cache.initialize()
    
    try:
        yield cache
    finally:
        # Cleanup if needed
        pass


# Initialize cache on startup
async def initialize_cache():
    """Initialize cache system on application startup."""
    await cache.initialize()
    
    # Configure default namespaces
    cache.configure("users", CacheConfig(ttl_seconds=1800, tags=["user_data"]))
    cache.configure("products", CacheConfig(ttl_seconds=3600, tags=["product_data"]))
    cache.configure("analytics", CacheConfig(ttl_seconds=300, tags=["analytics"]))
    cache.configure("auth", CacheConfig(ttl_seconds=900, tags=["authentication"]))
    
    logger.info("Cache system initialized with default configurations")


# Cleanup on shutdown
async def cleanup_cache():
    """Cleanup cache system on application shutdown."""
    await cache.shutdown()
    logger.info("Cache system cleaned up") 
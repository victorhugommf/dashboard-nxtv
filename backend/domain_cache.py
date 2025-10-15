#!/usr/bin/env python3
"""
Domain-Aware Cache Manager
Provides isolated caching per domain with domain-specific configurations and monitoring
"""

import time
import threading
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
import hashlib
from collections import defaultdict

from domain_config import DomainConfig


@dataclass
class CacheEntry:
    """Represents a single cache entry with metadata"""
    value: Any
    created_at: float
    expires_at: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired"""
        return time.time() > self.expires_at
    
    def access(self) -> Any:
        """Access the cache entry and update statistics"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value


@dataclass
class DomainCacheStats:
    """Statistics for a domain's cache"""
    domain: str
    total_entries: int = 0
    total_hits: int = 0
    total_misses: int = 0
    total_sets: int = 0
    total_deletes: int = 0
    total_size_bytes: int = 0
    oldest_entry: Optional[float] = None
    newest_entry: Optional[float] = None
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as percentage"""
        total_requests = self.total_hits + self.total_misses
        if total_requests == 0:
            return 0.0
        return (self.total_hits / total_requests) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary for JSON serialization"""
        return {
            'domain': self.domain,
            'total_entries': self.total_entries,
            'total_hits': self.total_hits,
            'total_misses': self.total_misses,
            'total_sets': self.total_sets,
            'total_deletes': self.total_deletes,
            'hit_rate_percent': round(self.hit_rate, 2),
            'total_size_bytes': self.total_size_bytes,
            'oldest_entry': datetime.fromtimestamp(self.oldest_entry).isoformat() if self.oldest_entry else None,
            'newest_entry': datetime.fromtimestamp(self.newest_entry).isoformat() if self.newest_entry else None
        }


class DomainCacheManager:
    """
    Domain-aware cache manager that provides isolated caching per domain.
    Each domain has its own cache namespace and timeout configurations.
    """
    
    def __init__(self):
        """Initialize the domain cache manager"""
        self._caches: Dict[str, Dict[str, CacheEntry]] = defaultdict(dict)
        self._stats: Dict[str, DomainCacheStats] = defaultdict(lambda: DomainCacheStats(""))
        self._locks: Dict[str, threading.RLock] = defaultdict(threading.RLock)
        self._cleanup_thread = None
        self._cleanup_interval = 300  # 5 minutes
        self._running = True
        self.logger = logging.getLogger(__name__)
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
        self.logger.info("DomainCacheManager initialized")
    
    def _start_cleanup_thread(self) -> None:
        """Start the background cleanup thread"""
        def cleanup_worker():
            while self._running:
                try:
                    self._cleanup_expired_entries()
                    time.sleep(self._cleanup_interval)
                except Exception as e:
                    self.logger.error(f"Error in cache cleanup thread: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        self.logger.debug("Cache cleanup thread started")
    
    def _cleanup_expired_entries(self) -> None:
        """Remove expired entries from all domain caches"""
        current_time = time.time()
        total_cleaned = 0
        
        for domain in list(self._caches.keys()):
            with self._locks[domain]:
                cache = self._caches[domain]
                expired_keys = [
                    key for key, entry in cache.items() 
                    if entry.is_expired()
                ]
                
                for key in expired_keys:
                    del cache[key]
                    total_cleaned += 1
                
                # Update stats
                if expired_keys:
                    self._update_cache_stats(domain)
        
        if total_cleaned > 0:
            self.logger.debug(f"Cleaned up {total_cleaned} expired cache entries")
    
    def _get_cache_key(self, domain: str, key: str) -> str:
        """Generate a cache key with domain isolation"""
        # Ensure domain isolation by prefixing with domain
        domain_key = f"domain:{domain}:key:{key}"
        # Hash for consistent length and to avoid special characters
        return hashlib.md5(domain_key.encode('utf-8')).hexdigest()
    
    def _calculate_entry_size(self, value: Any) -> int:
        """Estimate the size of a cache entry in bytes"""
        try:
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (int, float)):
                return 8  # Approximate size
            elif isinstance(value, (list, dict)):
                return len(json.dumps(value, default=str).encode('utf-8'))
            else:
                return len(str(value).encode('utf-8'))
        except Exception:
            return 100  # Default estimate
    
    def _update_cache_stats(self, domain: str) -> None:
        """Update cache statistics for a domain"""
        cache = self._caches[domain]
        stats = self._stats[domain]
        stats.domain = domain
        stats.total_entries = len(cache)
        
        if cache:
            entry_times = [entry.created_at for entry in cache.values()]
            stats.oldest_entry = min(entry_times)
            stats.newest_entry = max(entry_times)
            stats.total_size_bytes = sum(
                self._calculate_entry_size(entry.value) for entry in cache.values()
            )
        else:
            stats.oldest_entry = None
            stats.newest_entry = None
            stats.total_size_bytes = 0
    
    def get(self, domain: str, key: str) -> Optional[Any]:
        """
        Get a value from the domain-specific cache.
        
        Args:
            domain: The domain namespace
            key: The cache key
            
        Returns:
            The cached value or None if not found/expired
        """
        cache_key = self._get_cache_key(domain, key)
        
        with self._locks[domain]:
            cache = self._caches[domain]
            stats = self._stats[domain]
            
            if cache_key in cache:
                entry = cache[cache_key]
                
                if entry.is_expired():
                    # Remove expired entry
                    del cache[cache_key]
                    stats.total_misses += 1
                    self._update_cache_stats(domain)
                    self.logger.debug(f"Cache miss (expired) for domain {domain}, key {key}")
                    return None
                else:
                    # Return valid entry
                    value = entry.access()
                    stats.total_hits += 1
                    self.logger.debug(f"Cache hit for domain {domain}, key {key}")
                    return value
            else:
                stats.total_misses += 1
                self.logger.debug(f"Cache miss (not found) for domain {domain}, key {key}")
                return None
    
    def set(self, domain: str, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """
        Set a value in the domain-specific cache.
        
        Args:
            domain: The domain namespace
            key: The cache key
            value: The value to cache
            timeout: Cache timeout in seconds (uses domain default if None)
        """
        cache_key = self._get_cache_key(domain, key)
        current_time = time.time()
        
        # Use provided timeout or default to 300 seconds
        if timeout is None:
            timeout = 300
        
        expires_at = current_time + timeout
        
        entry = CacheEntry(
            value=value,
            created_at=current_time,
            expires_at=expires_at
        )
        
        with self._locks[domain]:
            cache = self._caches[domain]
            stats = self._stats[domain]
            
            cache[cache_key] = entry
            stats.total_sets += 1
            self._update_cache_stats(domain)
        
        self.logger.debug(f"Cache set for domain {domain}, key {key}, timeout {timeout}s")
    
    def delete(self, domain: str, key: str) -> bool:
        """
        Delete a specific key from the domain cache.
        
        Args:
            domain: The domain namespace
            key: The cache key to delete
            
        Returns:
            True if the key was deleted, False if not found
        """
        cache_key = self._get_cache_key(domain, key)
        
        with self._locks[domain]:
            cache = self._caches[domain]
            stats = self._stats[domain]
            
            if cache_key in cache:
                del cache[cache_key]
                stats.total_deletes += 1
                self._update_cache_stats(domain)
                self.logger.debug(f"Cache delete for domain {domain}, key {key}")
                return True
            else:
                self.logger.debug(f"Cache delete failed (not found) for domain {domain}, key {key}")
                return False
    
    def clear_domain_cache(self, domain: str) -> int:
        """
        Clear all cache entries for a specific domain.
        
        Args:
            domain: The domain namespace to clear
            
        Returns:
            Number of entries that were cleared
        """
        with self._locks[domain]:
            cache = self._caches[domain]
            count = len(cache)
            cache.clear()
            
            # Reset stats but keep counters
            stats = self._stats[domain]
            stats.total_deletes += count
            self._update_cache_stats(domain)
        
        self.logger.info(f"Cleared {count} cache entries for domain {domain}")
        return count
    
    def get_cache_stats(self, domain: str) -> Dict[str, Any]:
        """
        Get cache statistics for a specific domain.
        
        Args:
            domain: The domain namespace
            
        Returns:
            Dictionary containing cache statistics
        """
        with self._locks[domain]:
            self._update_cache_stats(domain)
            stats = self._stats[domain]
            stats.domain = domain
            return stats.to_dict()
    
    def get_all_cache_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get cache statistics for all domains.
        
        Returns:
            Dictionary mapping domain names to their statistics
        """
        all_stats = {}
        
        # Get stats for all domains that have caches
        for domain in self._caches.keys():
            all_stats[domain] = self.get_cache_stats(domain)
        
        # Also include domains that have stats but no current cache entries
        for domain in self._stats.keys():
            if domain not in all_stats:
                all_stats[domain] = self.get_cache_stats(domain)
        
        return all_stats
    
    def set_with_domain_config(self, domain: str, key: str, value: Any, domain_config: DomainConfig) -> None:
        """
        Set a value using the domain's configured cache timeout.
        
        Args:
            domain: The domain namespace
            key: The cache key
            value: The value to cache
            domain_config: Domain configuration containing cache timeout
        """
        timeout = domain_config.cache_timeout
        self.set(domain, key, value, timeout)
        self.logger.debug(f"Cache set with domain config timeout {timeout}s for domain {domain}")
    
    def get_domain_cache_size(self, domain: str) -> int:
        """
        Get the number of entries in a domain's cache.
        
        Args:
            domain: The domain namespace
            
        Returns:
            Number of cache entries for the domain
        """
        with self._locks[domain]:
            return len(self._caches[domain])
    
    def get_total_cache_size(self) -> int:
        """
        Get the total number of cache entries across all domains.
        
        Returns:
            Total number of cache entries
        """
        total = 0
        for domain in self._caches.keys():
            total += self.get_domain_cache_size(domain)
        return total
    
    def list_domain_keys(self, domain: str) -> List[str]:
        """
        List all cache keys for a specific domain (for debugging).
        
        Args:
            domain: The domain namespace
            
        Returns:
            List of cache keys (hashed) for the domain
        """
        with self._locks[domain]:
            return list(self._caches[domain].keys())
    
    def shutdown(self) -> None:
        """Shutdown the cache manager and cleanup resources"""
        self._running = False
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)
        
        # Clear all caches
        total_cleared = 0
        for domain in list(self._caches.keys()):
            total_cleared += self.clear_domain_cache(domain)
        
        self.logger.info(f"DomainCacheManager shutdown, cleared {total_cleared} total entries")


# Global cache manager instance
_cache_manager_instance: Optional[DomainCacheManager] = None


def get_cache_manager() -> DomainCacheManager:
    """
    Get the global cache manager instance (singleton pattern).
    
    Returns:
        The global DomainCacheManager instance
    """
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = DomainCacheManager()
    return _cache_manager_instance


def create_cache_manager() -> DomainCacheManager:
    """
    Create a new cache manager instance (for testing or specific use cases).
    
    Returns:
        A new DomainCacheManager instance
    """
    return DomainCacheManager()
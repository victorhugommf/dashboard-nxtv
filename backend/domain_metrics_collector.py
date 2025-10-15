#!/usr/bin/env python3
"""
Domain Metrics Collector
Advanced metrics collection and analysis for multi-domain system
"""

import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics

from domain_config import DomainConfigManager
from domain_cache import get_cache_manager
from domain_logger import get_domain_logger, LogCategory


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    domain: str
    metric_type: str
    tags: Dict[str, str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'domain': self.domain,
            'metric_type': self.metric_type,
            'tags': self.tags or {}
        }


@dataclass
class DomainMetrics:
    """Comprehensive metrics for a domain"""
    domain: str
    
    # Performance metrics
    response_times: List[float]
    cache_hit_rates: List[float]
    error_rates: List[float]
    
    # Resource metrics
    memory_usage: List[float]
    cpu_usage: List[float]
    
    # Business metrics
    request_counts: List[int]
    data_freshness: List[float]
    
    # Availability metrics
    uptime_percentage: float
    last_downtime: Optional[datetime]
    
    # Timestamps
    collected_at: datetime
    
    def get_averages(self) -> Dict[str, float]:
        """Get average values for all metrics"""
        return {
            'avg_response_time': statistics.mean(self.response_times) if self.response_times else 0,
            'avg_cache_hit_rate': statistics.mean(self.cache_hit_rates) if self.cache_hit_rates else 0,
            'avg_error_rate': statistics.mean(self.error_rates) if self.error_rates else 0,
            'avg_memory_usage': statistics.mean(self.memory_usage) if self.memory_usage else 0,
            'avg_cpu_usage': statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
            'avg_request_count': statistics.mean(self.request_counts) if self.request_counts else 0,
            'avg_data_freshness': statistics.mean(self.data_freshness) if self.data_freshness else 0
        }
    
    def get_percentiles(self) -> Dict[str, Dict[str, float]]:
        """Get percentile values for key metrics"""
        percentiles = {}
        
        for metric_name, values in [
            ('response_times', self.response_times),
            ('cache_hit_rates', self.cache_hit_rates),
            ('error_rates', self.error_rates)
        ]:
            if values:
                sorted_values = sorted(values)
                percentiles[metric_name] = {
                    'p50': statistics.median(sorted_values),
                    'p90': sorted_values[int(len(sorted_values) * 0.9)] if len(sorted_values) > 10 else sorted_values[-1],
                    'p95': sorted_values[int(len(sorted_values) * 0.95)] if len(sorted_values) > 20 else sorted_values[-1],
                    'p99': sorted_values[int(len(sorted_values) * 0.99)] if len(sorted_values) > 100 else sorted_values[-1]
                }
            else:
                percentiles[metric_name] = {'p50': 0, 'p90': 0, 'p95': 0, 'p99': 0}
        
        return percentiles


class MetricsCollector:
    """Advanced metrics collector for multi-domain system"""
    
    def __init__(self, config_file: str = "domains.json", retention_hours: int = 24):
        """Initialize metrics collector"""
        self.config_manager = DomainConfigManager(config_file)
        self.cache_manager = get_cache_manager()
        self.logger = get_domain_logger()
        
        # Metrics storage
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.domain_metrics: Dict[str, DomainMetrics] = {}
        
        # Collection settings
        self.retention_hours = retention_hours
        self.collection_interval = 30  # seconds
        self.is_collecting = False
        self.collection_thread = None
        
        # Performance tracking
        self.request_counters: Dict[str, int] = defaultdict(int)
        self.error_counters: Dict[str, int] = defaultdict(int)
        self.response_time_samples: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Lock for thread safety
        self._lock = threading.Lock()
    
    def start_collection(self):
        """Start automatic metrics collection"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        
        self.logger.info(
            LogCategory.PERFORMANCE,
            "Metrics collection started",
            details={'interval': self.collection_interval, 'retention_hours': self.retention_hours}
        )
    
    def stop_collection(self):
        """Stop automatic metrics collection"""
        self.is_collecting = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        
        self.logger.info(LogCategory.PERFORMANCE, "Metrics collection stopped")
    
    def _collection_loop(self):
        """Main collection loop"""
        while self.is_collecting:
            try:
                self.collect_all_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                self.logger.error(
                    LogCategory.ERROR_HANDLING,
                    f"Error in metrics collection loop: {str(e)}"
                )
                time.sleep(self.collection_interval)
    
    def collect_all_metrics(self):
        """Collect metrics for all domains"""
        domains = self.config_manager.get_all_domains()
        
        for domain in domains:
            try:
                self.collect_domain_metrics(domain)
            except Exception as e:
                self.logger.error(
                    LogCategory.ERROR_HANDLING,
                    f"Error collecting metrics for domain {domain}: {str(e)}"
                )
    
    def collect_domain_metrics(self, domain: str):
        """Collect comprehensive metrics for a specific domain"""
        timestamp = datetime.now()
        
        with self._lock:
            # Collect cache metrics
            cache_stats = self.cache_manager.get_cache_stats(domain)
            hit_rate = cache_stats.get('hit_rate_percent', 0)
            
            self._add_metric_point(domain, 'cache_hit_rate', hit_rate, timestamp)
            
            # Collect error metrics
            error_summary = self.logger.get_error_summary(domain, hours=1)
            error_rate = error_summary.get('total_errors', 0)
            
            self._add_metric_point(domain, 'error_rate', error_rate, timestamp)
            
            # Collect request metrics
            request_count = self.request_counters.get(domain, 0)
            self._add_metric_point(domain, 'request_count', request_count, timestamp)
            
            # Collect response time metrics
            response_times = list(self.response_time_samples.get(domain, []))
            if response_times:
                avg_response_time = statistics.mean(response_times)
                self._add_metric_point(domain, 'response_time', avg_response_time, timestamp)
            
            # Collect system resource metrics (if available)
            try:
                import psutil
                
                # CPU usage (system-wide, tagged by domain)
                cpu_percent = psutil.cpu_percent()
                self._add_metric_point(domain, 'cpu_usage', cpu_percent, timestamp)
                
                # Memory usage (system-wide, tagged by domain)
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                self._add_metric_point(domain, 'memory_usage', memory_percent, timestamp)
                
            except ImportError:
                # psutil not available, skip system metrics
                pass
            
            # Collect data freshness metrics
            newest_entry = cache_stats.get('newest_entry')
            if newest_entry:
                try:
                    newest_time = datetime.fromisoformat(newest_entry)
                    freshness_minutes = (timestamp - newest_time).total_seconds() / 60
                    self._add_metric_point(domain, 'data_freshness', freshness_minutes, timestamp)
                except Exception:
                    pass
            
            # Update domain metrics summary
            self._update_domain_metrics_summary(domain, timestamp)
    
    def _add_metric_point(self, domain: str, metric_type: str, value: float, timestamp: datetime):
        """Add a metric point to the history"""
        metric_key = f"{domain}:{metric_type}"
        
        metric_point = MetricPoint(
            timestamp=timestamp,
            value=value,
            domain=domain,
            metric_type=metric_type
        )
        
        self.metrics_history[metric_key].append(metric_point)
        
        # Clean old metrics
        self._clean_old_metrics(metric_key)
    
    def _clean_old_metrics(self, metric_key: str):
        """Remove metrics older than retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        while (self.metrics_history[metric_key] and 
               self.metrics_history[metric_key][0].timestamp < cutoff_time):
            self.metrics_history[metric_key].popleft()
    
    def _update_domain_metrics_summary(self, domain: str, timestamp: datetime):
        """Update comprehensive domain metrics summary"""
        # Collect recent metrics for this domain
        recent_metrics = self._get_recent_metrics(domain, hours=1)
        
        # Extract metric values
        response_times = [m.value for m in recent_metrics.get('response_time', [])]
        cache_hit_rates = [m.value for m in recent_metrics.get('cache_hit_rate', [])]
        error_rates = [m.value for m in recent_metrics.get('error_rate', [])]
        memory_usage = [m.value for m in recent_metrics.get('memory_usage', [])]
        cpu_usage = [m.value for m in recent_metrics.get('cpu_usage', [])]
        request_counts = [int(m.value) for m in recent_metrics.get('request_count', [])]
        data_freshness = [m.value for m in recent_metrics.get('data_freshness', [])]
        
        # Calculate uptime (simplified - based on error rates)
        uptime_percentage = 100.0
        if error_rates:
            avg_error_rate = statistics.mean(error_rates)
            uptime_percentage = max(0, 100 - (avg_error_rate * 10))  # Rough calculation
        
        # Create domain metrics summary
        self.domain_metrics[domain] = DomainMetrics(
            domain=domain,
            response_times=response_times,
            cache_hit_rates=cache_hit_rates,
            error_rates=error_rates,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            request_counts=request_counts,
            data_freshness=data_freshness,
            uptime_percentage=uptime_percentage,
            last_downtime=None,  # Would need more sophisticated tracking
            collected_at=timestamp
        )
    
    def _get_recent_metrics(self, domain: str, hours: int = 1) -> Dict[str, List[MetricPoint]]:
        """Get recent metrics for a domain"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = defaultdict(list)
        
        for metric_key, metrics in self.metrics_history.items():
            if metric_key.startswith(f"{domain}:"):
                metric_type = metric_key.split(':', 1)[1]
                
                for metric_point in metrics:
                    if metric_point.timestamp >= cutoff_time:
                        recent_metrics[metric_type].append(metric_point)
        
        return recent_metrics
    
    def record_request(self, domain: str, response_time: float = None):
        """Record a request for metrics tracking"""
        with self._lock:
            self.request_counters[domain] += 1
            
            if response_time is not None:
                self.response_time_samples[domain].append(response_time)
    
    def record_error(self, domain: str):
        """Record an error for metrics tracking"""
        with self._lock:
            self.error_counters[domain] += 1
    
    def get_domain_metrics(self, domain: str) -> Optional[DomainMetrics]:
        """Get comprehensive metrics for a domain"""
        return self.domain_metrics.get(domain)
    
    def get_all_domain_metrics(self) -> Dict[str, DomainMetrics]:
        """Get metrics for all domains"""
        return self.domain_metrics.copy()
    
    def get_system_metrics_summary(self) -> Dict[str, Any]:
        """Get system-wide metrics summary"""
        all_metrics = self.get_all_domain_metrics()
        
        if not all_metrics:
            return {
                'total_domains': 0,
                'avg_response_time': 0,
                'avg_cache_hit_rate': 0,
                'avg_error_rate': 0,
                'total_requests': 0,
                'system_uptime': 100.0
            }
        
        # Aggregate metrics across all domains
        all_response_times = []
        all_cache_hit_rates = []
        all_error_rates = []
        total_requests = 0
        uptime_percentages = []
        
        for domain_metrics in all_metrics.values():
            all_response_times.extend(domain_metrics.response_times)
            all_cache_hit_rates.extend(domain_metrics.cache_hit_rates)
            all_error_rates.extend(domain_metrics.error_rates)
            total_requests += sum(domain_metrics.request_counts)
            uptime_percentages.append(domain_metrics.uptime_percentage)
        
        return {
            'total_domains': len(all_metrics),
            'avg_response_time': statistics.mean(all_response_times) if all_response_times else 0,
            'avg_cache_hit_rate': statistics.mean(all_cache_hit_rates) if all_cache_hit_rates else 0,
            'avg_error_rate': statistics.mean(all_error_rates) if all_error_rates else 0,
            'total_requests': total_requests,
            'system_uptime': statistics.mean(uptime_percentages) if uptime_percentages else 100.0,
            'collected_at': datetime.now().isoformat()
        }
    
    def get_metrics_for_timerange(self, domain: str, start_time: datetime, end_time: datetime) -> Dict[str, List[MetricPoint]]:
        """Get metrics for a specific time range"""
        timerange_metrics = defaultdict(list)
        
        for metric_key, metrics in self.metrics_history.items():
            if metric_key.startswith(f"{domain}:"):
                metric_type = metric_key.split(':', 1)[1]
                
                for metric_point in metrics:
                    if start_time <= metric_point.timestamp <= end_time:
                        timerange_metrics[metric_type].append(metric_point)
        
        return timerange_metrics
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export all metrics in specified format"""
        if format.lower() == 'json':
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'retention_hours': self.retention_hours,
                'domain_metrics': {
                    domain: {
                        'summary': asdict(metrics),
                        'averages': metrics.get_averages(),
                        'percentiles': metrics.get_percentiles()
                    }
                    for domain, metrics in self.domain_metrics.items()
                },
                'system_summary': self.get_system_metrics_summary()
            }
            
            return json.dumps(export_data, indent=2, default=str)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_alerts(self, thresholds: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """Get alerts based on metric thresholds"""
        if thresholds is None:
            thresholds = {
                'response_time_ms': 3000,
                'cache_hit_rate_min': 50,
                'error_rate_max': 10,
                'uptime_min': 95
            }
        
        alerts = []
        
        for domain, metrics in self.domain_metrics.items():
            averages = metrics.get_averages()
            
            # Response time alert
            if averages['avg_response_time'] > thresholds['response_time_ms']:
                alerts.append({
                    'domain': domain,
                    'type': 'response_time',
                    'severity': 'warning',
                    'message': f"High response time: {averages['avg_response_time']:.1f}ms",
                    'threshold': thresholds['response_time_ms'],
                    'current_value': averages['avg_response_time']
                })
            
            # Cache hit rate alert
            if averages['avg_cache_hit_rate'] < thresholds['cache_hit_rate_min']:
                alerts.append({
                    'domain': domain,
                    'type': 'cache_hit_rate',
                    'severity': 'warning',
                    'message': f"Low cache hit rate: {averages['avg_cache_hit_rate']:.1f}%",
                    'threshold': thresholds['cache_hit_rate_min'],
                    'current_value': averages['avg_cache_hit_rate']
                })
            
            # Error rate alert
            if averages['avg_error_rate'] > thresholds['error_rate_max']:
                alerts.append({
                    'domain': domain,
                    'type': 'error_rate',
                    'severity': 'critical',
                    'message': f"High error rate: {averages['avg_error_rate']:.1f}",
                    'threshold': thresholds['error_rate_max'],
                    'current_value': averages['avg_error_rate']
                })
            
            # Uptime alert
            if metrics.uptime_percentage < thresholds['uptime_min']:
                alerts.append({
                    'domain': domain,
                    'type': 'uptime',
                    'severity': 'critical',
                    'message': f"Low uptime: {metrics.uptime_percentage:.1f}%",
                    'threshold': thresholds['uptime_min'],
                    'current_value': metrics.uptime_percentage
                })
        
        return alerts


# Global metrics collector instance
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global _metrics_collector
    
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    
    return _metrics_collector


def start_metrics_collection():
    """Start global metrics collection"""
    collector = get_metrics_collector()
    collector.start_collection()


def stop_metrics_collection():
    """Stop global metrics collection"""
    global _metrics_collector
    
    if _metrics_collector:
        _metrics_collector.stop_collection()
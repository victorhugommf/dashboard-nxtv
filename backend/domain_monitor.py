#!/usr/bin/env python3
"""
Domain Monitoring Dashboard
Real-time monitoring tool for multi-domain dashboard system
"""

import time
import json
import argparse
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import requests
from dataclasses import dataclass

from domain_config import DomainConfigManager
from domain_cache import get_cache_manager
from domain_logger import get_domain_logger


@dataclass
class DomainHealthMetrics:
    """Health metrics for a domain"""
    domain: str
    status: str  # healthy, warning, critical, unknown
    response_time: Optional[float]
    cache_hit_rate: float
    error_count_24h: int
    last_successful_request: Optional[datetime]
    data_freshness: Optional[timedelta]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'domain': self.domain,
            'status': self.status,
            'response_time_ms': round(self.response_time * 1000, 2) if self.response_time else None,
            'cache_hit_rate_percent': round(self.cache_hit_rate, 2),
            'error_count_24h': self.error_count_24h,
            'last_successful_request': self.last_successful_request.isoformat() if self.last_successful_request else None,
            'data_freshness_minutes': self.data_freshness.total_seconds() / 60 if self.data_freshness else None
        }


class DomainMonitor:
    """Monitor for multi-domain dashboard system"""
    
    def __init__(self, config_file: str = "domains.json", base_url: str = "http://localhost:5000"):
        """Initialize domain monitor"""
        self.config_manager = DomainConfigManager(config_file)
        self.cache_manager = get_cache_manager()
        self.logger = get_domain_logger()
        self.base_url = base_url.rstrip('/')
        
        # Monitoring state
        self.last_check = {}
        self.health_history = {}
        self.alert_thresholds = {
            'error_count_critical': 20,
            'error_count_warning': 5,
            'response_time_critical': 10.0,  # seconds
            'response_time_warning': 3.0,
            'cache_hit_rate_warning': 50.0,  # percent
            'data_freshness_warning': 60,  # minutes
        }
    
    def check_all_domains(self) -> Dict[str, DomainHealthMetrics]:
        """Check health of all configured domains"""
        domains = self.config_manager.get_all_domains()
        health_metrics = {}
        
        print(f"🔍 Checking {len(domains)} domains...")
        
        for domain in domains:
            try:
                metrics = self.check_domain_health(domain)
                health_metrics[domain] = metrics
                
                # Store in history
                if domain not in self.health_history:
                    self.health_history[domain] = []
                
                self.health_history[domain].append({
                    'timestamp': datetime.now(),
                    'metrics': metrics
                })
                
                # Keep only last 100 entries
                self.health_history[domain] = self.health_history[domain][-100:]
                
            except Exception as e:
                print(f"❌ Error checking domain {domain}: {str(e)}")
                health_metrics[domain] = DomainHealthMetrics(
                    domain=domain,
                    status='unknown',
                    response_time=None,
                    cache_hit_rate=0.0,
                    error_count_24h=0,
                    last_successful_request=None,
                    data_freshness=None
                )
        
        return health_metrics
    
    def check_domain_health(self, domain: str) -> DomainHealthMetrics:
        """Check health of a specific domain"""
        try:
            domain_config = self.config_manager.get_config_by_domain(domain)
        except ValueError:
            return DomainHealthMetrics(
                domain=domain,
                status='critical',
                response_time=None,
                cache_hit_rate=0.0,
                error_count_24h=0,
                last_successful_request=None,
                data_freshness=None
            )
        
        # Test API endpoint response time
        response_time = self._test_api_response_time(domain)
        
        # Get cache statistics
        cache_stats = self.cache_manager.get_cache_stats(domain)
        cache_hit_rate = cache_stats.get('hit_rate_percent', 0.0)
        
        # Get error count from logs
        error_summary = self.logger.get_error_summary(domain, hours=24)
        error_count_24h = error_summary['total_errors']
        
        # Determine overall status
        status = self._calculate_domain_status(
            response_time, cache_hit_rate, error_count_24h
        )
        
        # Get last successful request time (approximate)
        last_successful = self._get_last_successful_request(domain)
        
        # Calculate data freshness (based on cache age)
        data_freshness = self._calculate_data_freshness(cache_stats)
        
        return DomainHealthMetrics(
            domain=domain,
            status=status,
            response_time=response_time,
            cache_hit_rate=cache_hit_rate,
            error_count_24h=error_count_24h,
            last_successful_request=last_successful,
            data_freshness=data_freshness
        )
    
    def _test_api_response_time(self, domain: str) -> Optional[float]:
        """Test API response time for a domain"""
        try:
            headers = {'Host': domain}
            url = f"{self.base_url}/api/health"
            
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                return end_time - start_time
            else:
                return None
                
        except Exception:
            return None
    
    def _calculate_domain_status(self, response_time: Optional[float], 
                                cache_hit_rate: float, error_count: int) -> str:
        """Calculate overall domain status"""
        if response_time is None:
            return 'critical'
        
        if (error_count >= self.alert_thresholds['error_count_critical'] or
            response_time >= self.alert_thresholds['response_time_critical']):
            return 'critical'
        
        if (error_count >= self.alert_thresholds['error_count_warning'] or
            response_time >= self.alert_thresholds['response_time_warning'] or
            cache_hit_rate < self.alert_thresholds['cache_hit_rate_warning']):
            return 'warning'
        
        return 'healthy'
    
    def _get_last_successful_request(self, domain: str) -> Optional[datetime]:
        """Get timestamp of last successful request (approximate)"""
        try:
            domain_logs = self.logger.get_domain_logs(domain, limit=50)
            
            for log_entry in domain_logs:
                if (log_entry.get('category') == 'api_request' and 
                    log_entry.get('level') == 'INFO'):
                    return datetime.fromisoformat(log_entry['timestamp'])
            
            return None
        except Exception:
            return None
    
    def _calculate_data_freshness(self, cache_stats: Dict[str, Any]) -> Optional[timedelta]:
        """Calculate data freshness based on cache statistics"""
        try:
            newest_entry = cache_stats.get('newest_entry')
            if newest_entry:
                newest_time = datetime.fromisoformat(newest_entry)
                return datetime.now() - newest_time
            return None
        except Exception:
            return None
    
    def generate_health_report(self, health_metrics: Dict[str, DomainHealthMetrics]) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        total_domains = len(health_metrics)
        healthy_count = sum(1 for m in health_metrics.values() if m.status == 'healthy')
        warning_count = sum(1 for m in health_metrics.values() if m.status == 'warning')
        critical_count = sum(1 for m in health_metrics.values() if m.status == 'critical')
        unknown_count = sum(1 for m in health_metrics.values() if m.status == 'unknown')
        
        # Calculate system-wide metrics
        response_times = [m.response_time for m in health_metrics.values() if m.response_time is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        cache_hit_rates = [m.cache_hit_rate for m in health_metrics.values()]
        avg_cache_hit_rate = sum(cache_hit_rates) / len(cache_hit_rates) if cache_hit_rates else 0
        
        total_errors = sum(m.error_count_24h for m in health_metrics.values())
        
        # Identify problematic domains
        critical_domains = [m.domain for m in health_metrics.values() if m.status == 'critical']
        warning_domains = [m.domain for m in health_metrics.values() if m.status == 'warning']
        
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_domains': total_domains,
                'healthy': healthy_count,
                'warning': warning_count,
                'critical': critical_count,
                'unknown': unknown_count,
                'overall_status': self._calculate_overall_status(healthy_count, warning_count, critical_count, unknown_count)
            },
            'system_metrics': {
                'avg_response_time_ms': round(avg_response_time * 1000, 2) if avg_response_time else 0,
                'avg_cache_hit_rate_percent': round(avg_cache_hit_rate, 2),
                'total_errors_24h': total_errors
            },
            'alerts': {
                'critical_domains': critical_domains,
                'warning_domains': warning_domains,
                'needs_attention': len(critical_domains) + len(warning_domains) > 0
            },
            'domain_details': {
                domain: metrics.to_dict() 
                for domain, metrics in health_metrics.items()
            }
        }
    
    def _calculate_overall_status(self, healthy: int, warning: int, critical: int, unknown: int) -> str:
        """Calculate overall system status"""
        if critical > 0:
            return 'critical'
        elif unknown > healthy:
            return 'unknown'
        elif warning > healthy:
            return 'degraded'
        elif warning > 0:
            return 'warning'
        else:
            return 'healthy'
    
    def print_health_report(self, health_metrics: Dict[str, DomainHealthMetrics]):
        """Print human-readable health report"""
        report = self.generate_health_report(health_metrics)
        
        print("\n" + "="*80)
        print(f"🏥 DOMAIN HEALTH REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Overall status
        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'degraded': '🟡',
            'critical': '🚨',
            'unknown': '❓'
        }
        
        overall_status = report['summary']['overall_status']
        print(f"\n{status_emoji.get(overall_status, '❓')} Overall Status: {overall_status.upper()}")
        
        # Summary
        summary = report['summary']
        print(f"\n📊 Summary:")
        print(f"  Total Domains: {summary['total_domains']}")
        print(f"  Healthy: {summary['healthy']} ✅")
        print(f"  Warning: {summary['warning']} ⚠️")
        print(f"  Critical: {summary['critical']} 🚨")
        print(f"  Unknown: {summary['unknown']} ❓")
        
        # System metrics
        metrics = report['system_metrics']
        print(f"\n📈 System Metrics:")
        print(f"  Avg Response Time: {metrics['avg_response_time_ms']}ms")
        print(f"  Avg Cache Hit Rate: {metrics['avg_cache_hit_rate_percent']}%")
        print(f"  Total Errors (24h): {metrics['total_errors_24h']}")
        
        # Alerts
        alerts = report['alerts']
        if alerts['needs_attention']:
            print(f"\n🚨 ALERTS:")
            if alerts['critical_domains']:
                print(f"  Critical Domains: {', '.join(alerts['critical_domains'])}")
            if alerts['warning_domains']:
                print(f"  Warning Domains: {', '.join(alerts['warning_domains'])}")
        else:
            print(f"\n✅ No alerts - all domains are healthy!")
        
        # Domain details
        print(f"\n📋 Domain Details:")
        for domain, metrics in health_metrics.items():
            status_icon = status_emoji.get(metrics.status, '❓')
            response_time = f"{metrics.response_time*1000:.0f}ms" if metrics.response_time else "N/A"
            
            print(f"  {status_icon} {domain}")
            print(f"    Status: {metrics.status}")
            print(f"    Response Time: {response_time}")
            print(f"    Cache Hit Rate: {metrics.cache_hit_rate:.1f}%")
            print(f"    Errors (24h): {metrics.error_count_24h}")
            
            if metrics.data_freshness:
                freshness_minutes = metrics.data_freshness.total_seconds() / 60
                print(f"    Data Freshness: {freshness_minutes:.0f} minutes ago")
    
    def monitor_continuous(self, interval: int = 60):
        """Run continuous monitoring"""
        print(f"🔄 Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                health_metrics = self.check_all_domains()
                self.print_health_report(health_metrics)
                
                # Check for alerts
                report = self.generate_health_report(health_metrics)
                if report['alerts']['needs_attention']:
                    self._send_alerts(report)
                
                print(f"\n⏰ Next check in {interval} seconds...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")
    
    def _send_alerts(self, report: Dict[str, Any]):
        """Send alerts for critical issues (placeholder for future implementation)"""
        # This could be extended to send emails, Slack notifications, etc.
        alerts = report['alerts']
        
        if alerts['critical_domains']:
            print(f"\n🚨 CRITICAL ALERT: Domains need immediate attention: {', '.join(alerts['critical_domains'])}")
        
        if alerts['warning_domains']:
            print(f"\n⚠️  WARNING: Domains need monitoring: {', '.join(alerts['warning_domains'])}")


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Monitor multi-domain dashboard system')
    parser.add_argument('--config', default='domains.json', help='Configuration file path')
    parser.add_argument('--base-url', default='http://localhost:5000', help='Base URL for API testing')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--domain', help='Check specific domain only')
    
    args = parser.parse_args()
    
    try:
        monitor = DomainMonitor(args.config, args.base_url)
        
        if args.continuous:
            monitor.monitor_continuous(args.interval)
        else:
            if args.domain:
                # Check specific domain
                try:
                    metrics = monitor.check_domain_health(args.domain)
                    health_metrics = {args.domain: metrics}
                except Exception as e:
                    print(f"Error checking domain {args.domain}: {str(e)}")
                    sys.exit(1)
            else:
                # Check all domains
                health_metrics = monitor.check_all_domains()
            
            if args.json:
                report = monitor.generate_health_report(health_metrics)
                print(json.dumps(report, indent=2))
            else:
                monitor.print_health_report(health_metrics)
            
            # Exit with error code if there are critical issues
            critical_count = sum(1 for m in health_metrics.values() if m.status == 'critical')
            if critical_count > 0:
                sys.exit(1)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
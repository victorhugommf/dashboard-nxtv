# Domain Administration Guide

This guide covers the administration and monitoring tools for the multi-domain dashboard system.

## Table of Contents

1. [Overview](#overview)
2. [Administration API](#administration-api)
3. [Domain Status Dashboard](#domain-status-dashboard)
4. [Metrics Collection System](#metrics-collection-system)
5. [Configuration Validation](#configuration-validation)
6. [Domain Monitoring](#domain-monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Overview

The multi-domain dashboard system provides comprehensive administration and monitoring tools to help you manage multiple client domains effectively. These tools include:

- **Administration API**: REST endpoints for managing domains and system metrics
- **Domain Status Dashboard**: Web-based dashboard for real-time monitoring
- **Metrics Collection System**: Advanced metrics collection and analysis
- **Configuration Validation**: Tools to validate domain configurations
- **Domain Monitoring**: Real-time monitoring and health checks
- **Logging and Audit**: Comprehensive logging with audit trails

## Administration API

### Base URL

All administration endpoints are available under `/api/admin/` and require appropriate access controls in production.

### Endpoints

#### List All Domains

```http
GET /api/admin/domains
```

Returns a list of all configured domains with their status and basic metrics.

**Response:**
```json
{
  "success": true,
  "domains": [
    {
      "domain": "dashboard-desktop.com",
      "client_name": "Desktop",
      "google_sheet_id": "1vPoodpppoT0CF0ly7RSaEGjYzaHvWchYiimNPcUyHTI",
      "enabled": true,
      "cache_timeout": 300,
      "theme": {
        "primary_color": "#059669",
        "secondary_color": "#10b981",
        "accent_colors": ["#34d399", "#6ee7b7", "#a7f3d0"]
      },
      "cache_stats": {
        "total_entries": 5,
        "hit_rate_percent": 85.2
      },
      "error_summary": {
        "total_errors_24h": 0,
        "error_categories": {}
      },
      "status": "healthy"
    }
  ],
  "total_domains": 1,
  "timestamp": "2025-01-06T10:30:00"
}
```

#### Get Domain Status

```http
GET /api/admin/domains/{domain}/status
```

Returns detailed status information for a specific domain.

**Response:**
```json
{
  "success": true,
  "domain_status": {
    "domain": "dashboard-desktop.com",
    "client_name": "Desktop",
    "enabled": true,
    "cache_stats": {
      "total_entries": 5,
      "total_hits": 42,
      "total_misses": 8,
      "hit_rate_percent": 84.0
    },
    "error_summary": {
      "total_errors": 0,
      "error_by_category": {},
      "recent_errors": []
    },
    "recent_logs": [...],
    "data_access_status": "healthy",
    "health_status": "healthy",
    "last_updated": "2025-01-06T10:30:00"
  }
}
```

#### Get System Metrics Overview

```http
GET /api/admin/metrics/overview
```

Returns system-wide metrics and health overview.

**Response:**
```json
{
  "success": true,
  "metrics": {
    "system_status": {
      "total_domains": 3,
      "healthy_domains": 2,
      "warning_domains": 1,
      "error_domains": 0,
      "overall_status": "warning"
    },
    "cache_metrics": {
      "total_entries": 15,
      "total_hits": 120,
      "total_misses": 25,
      "hit_rate_percent": 82.8,
      "domains_with_cache": 3
    },
    "error_metrics": {
      "total_errors_24h": 2,
      "error_by_category": {
        "data_access": 1,
        "cache_operation": 1
      },
      "recent_errors": [...]
    }
  }
}
```

#### Validate Configuration

```http
POST /api/admin/config/validate
Content-Type: application/json

{
  "domains": {
    "example.com": {
      "google_sheet_id": "1234567890",
      "client_name": "Example Client",
      "theme": {
        "primary_color": "#059669",
        "secondary_color": "#10b981",
        "accent_colors": ["#34d399"]
      },
      "cache_timeout": 300,
      "enabled": true
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": [
      "Domain 'example.com' should have at least 2 accent colors for better theming"
    ],
    "suggestions": [
      "Consider adding a 'default_config' section for fallback configuration"
    ],
    "validated_at": "2025-01-06T10:30:00"
  }
}
```

#### Reload Configuration

```http
POST /api/admin/config/reload
```

Reloads domain configuration from the configuration file without restarting the application.

#### Clear Cache

```http
POST /api/admin/cache/clear
Content-Type: application/json

{
  "domain": "dashboard-desktop.com"  // Optional: clear specific domain, omit for all
}
```

#### Get Domain Logs

```http
GET /api/admin/logs/{domain}?limit=50&level=ERROR&category=data_access
```

Returns logs for a specific domain with optional filtering.

#### Get Audit Trail

```http
GET /api/admin/audit-trail?limit=50
```

Returns audit trail of configuration changes and administrative actions.

## Domain Status Dashboard

### Web-Based Dashboard

Access the real-time domain status dashboard at:

```
http://your-server:5000/admin/dashboard/
```

The dashboard provides:

- **System Overview**: Total domains, health status, and key metrics
- **Domain Cards**: Individual domain status with real-time metrics
- **Auto-refresh**: Automatic updates every 30 seconds
- **Interactive Controls**: Manual refresh and auto-refresh toggle

### Dashboard Features

#### System Overview Cards
- Total number of configured domains
- Count of healthy domains
- Average response time across all domains
- System-wide cache hit rate

#### Domain Status Cards
Each domain displays:
- Current health status (healthy/warning/critical/unknown)
- Client name and domain
- Response time
- Cache hit rate
- Error count (24 hours)
- Current status

#### Status Indicators
- 🟢 **Healthy**: All metrics within normal ranges
- 🟡 **Warning**: Some metrics elevated but functional
- 🔴 **Critical**: Significant issues requiring attention
- ⚪ **Unknown**: Unable to determine status

### Dashboard API Endpoints

#### Get Dashboard Status
```http
GET /admin/dashboard/api/status
```

Returns comprehensive dashboard data including system overview and all domain metrics.

#### Get Domain Details
```http
GET /admin/dashboard/api/domain/{domain}/details
```

Returns detailed information for a specific domain including configuration, cache statistics, recent logs, and error summary.

## Metrics Collection System

### Advanced Metrics Collection

The system includes comprehensive metrics collection for performance monitoring and analysis.

#### Starting Metrics Collection

```python
from domain_metrics_collector import start_metrics_collection

# Start automatic metrics collection
start_metrics_collection()
```

#### Collected Metrics

**Performance Metrics:**
- Response times (per request)
- Cache hit rates
- Error rates
- Request counts

**Resource Metrics:**
- Memory usage (system-wide)
- CPU usage (system-wide)

**Business Metrics:**
- Data freshness (cache age)
- Uptime percentage
- Request patterns

#### Metrics API

```python
from domain_metrics_collector import get_metrics_collector

collector = get_metrics_collector()

# Get metrics for specific domain
domain_metrics = collector.get_domain_metrics('example.com')

# Get system-wide metrics summary
system_summary = collector.get_system_metrics_summary()

# Get alerts based on thresholds
alerts = collector.get_alerts()

# Export metrics
json_export = collector.export_metrics('json')
```

#### Recording Custom Metrics

```python
# Record a request with response time
collector.record_request('example.com', response_time=0.250)

# Record an error
collector.record_error('example.com')
```

#### Metrics Retention

- Default retention: 24 hours
- Configurable retention period
- Automatic cleanup of old metrics
- In-memory storage with configurable limits

#### Alerts and Thresholds

Default alert thresholds:
- **Response Time**: > 3000ms (warning)
- **Cache Hit Rate**: < 50% (warning)
- **Error Rate**: > 10 errors/hour (critical)
- **Uptime**: < 95% (critical)

Custom thresholds can be configured:

```python
custom_thresholds = {
    'response_time_ms': 2000,
    'cache_hit_rate_min': 70,
    'error_rate_max': 5,
    'uptime_min': 98
}

alerts = collector.get_alerts(custom_thresholds)
```

## Configuration Validation

### Command Line Tool

Use the standalone validation tool to check configuration files:

```bash
# Basic validation
python validate_domain_config.py domains.json

# JSON output
python validate_domain_config.py domains.json --json

# Strict mode (warnings as errors)
python validate_domain_config.py domains.json --strict

# Quiet mode (errors only)
python validate_domain_config.py domains.json --quiet
```

### Validation Rules

The validator checks for:

**Errors (will prevent system startup):**
- Missing required fields (`google_sheet_id`, `client_name`, `theme`)
- Invalid color formats (must be hex colors like `#059669`)
- Invalid data types
- Malformed JSON

**Warnings (system will work but may have issues):**
- Very short or long cache timeouts
- Duplicate Google Sheet IDs across domains
- Missing accent colors
- Invalid domain name formats

**Suggestions (best practices):**
- Adding more accent colors for better theming
- Including a default configuration
- Performance optimizations for many domains

### Example Validation Output

```
Configuration Validation Results for: domains.json
============================================================
✅ Configuration is VALID

Summary:
  Errors: 0
  Warnings: 2
  Suggestions: 1

⚠️  WARNINGS (2):
  1. Domain 'dashboard-desktop.com' should have at least 2 accent colors for better theming
  2. Very low cache timeout (60s) for domain 'fast-client.com'

💡 SUGGESTIONS (1):
  1. Consider adding a 'default_config' section for fallback configuration
```

## Domain Monitoring

### Command Line Monitor

Use the monitoring tool for real-time health checks:

```bash
# Single check of all domains
python domain_monitor.py

# Check specific domain
python domain_monitor.py --domain dashboard-desktop.com

# Continuous monitoring (every 60 seconds)
python domain_monitor.py --continuous --interval 60

# JSON output
python domain_monitor.py --json

# Custom base URL
python domain_monitor.py --base-url http://production-server:5000
```

### Monitoring Metrics

The monitor tracks:

- **Response Time**: API endpoint response times
- **Cache Performance**: Hit rates and cache statistics
- **Error Rates**: Error counts over 24-hour periods
- **Data Freshness**: How recent the cached data is
- **Domain Status**: Overall health (healthy/warning/critical/unknown)

### Health Status Levels

- **Healthy** ✅: All metrics within normal ranges
- **Warning** ⚠️: Some metrics elevated but system functional
- **Critical** 🚨: Significant issues requiring immediate attention
- **Unknown** ❓: Unable to determine status (connectivity issues)

### Alert Thresholds

Default thresholds (configurable in code):

- **Critical**: >20 errors/24h OR >10s response time
- **Warning**: >5 errors/24h OR >3s response time OR <50% cache hit rate

### Example Monitor Output

```
🏥 DOMAIN HEALTH REPORT - 2025-01-06 10:30:00
================================================================================

✅ Overall Status: HEALTHY

📊 Summary:
  Total Domains: 3
  Healthy: 2 ✅
  Warning: 1 ⚠️
  Critical: 0 🚨
  Unknown: 0 ❓

📈 System Metrics:
  Avg Response Time: 245ms
  Avg Cache Hit Rate: 82.3%
  Total Errors (24h): 2

⚠️  ALERTS:
  Warning Domains: slow-client.com

📋 Domain Details:
  ✅ dashboard-desktop.com
    Status: healthy
    Response Time: 180ms
    Cache Hit Rate: 85.2%
    Errors (24h): 0
    Data Freshness: 15 minutes ago

  ⚠️  slow-client.com
    Status: warning
    Response Time: 3200ms
    Cache Hit Rate: 45.1%
    Errors (24h): 2
    Data Freshness: 45 minutes ago
```

## Troubleshooting

### Common Issues

#### Domain Not Found (404)

**Symptoms:**
- API returns 404 for specific domain
- Domain shows as "unknown" in monitoring

**Solutions:**
1. Check domain configuration in `domains.json`
2. Verify domain name matches exactly (case-sensitive)
3. Ensure domain is enabled (`"enabled": true`)
4. Reload configuration: `POST /api/admin/config/reload`

#### High Response Times

**Symptoms:**
- Monitor shows high response times
- Users report slow loading

**Solutions:**
1. Check Google Sheets API connectivity
2. Increase cache timeout for the domain
3. Monitor system resources (CPU, memory)
4. Check for network issues

#### Cache Issues

**Symptoms:**
- Low cache hit rates
- Frequent data fetching

**Solutions:**
1. Check cache configuration
2. Monitor cache statistics: `GET /api/cache/stats`
3. Clear and rebuild cache: `POST /api/admin/cache/clear`
4. Adjust cache timeout settings

#### Configuration Errors

**Symptoms:**
- Validation fails
- System won't start

**Solutions:**
1. Run validation tool: `python validate_domain_config.py domains.json`
2. Check JSON syntax
3. Verify all required fields are present
4. Check color format (must be hex: `#059669`)

### Log Analysis

#### Log Locations

- **Application logs**: `logs/application.log`
- **Domain-specific logs**: `logs/domain.log`
- **Error logs**: `logs/errors.log`
- **Audit logs**: `logs/audit.log`
- **Structured logs**: `logs/structured.jsonl`

#### Key Log Categories

- `domain_resolution`: Domain identification and routing
- `data_access`: Google Sheets data fetching
- `cache_operation`: Cache hits, misses, and operations
- `configuration`: Configuration changes and reloads
- `api_request`: API endpoint access
- `error_handling`: Error processing and recovery

#### Log Analysis Commands

```bash
# Recent errors for specific domain
grep "dashboard-desktop.com" logs/errors.log | tail -20

# Cache operations
grep "cache_operation" logs/structured.jsonl | jq .

# Configuration changes
grep "AUDIT" logs/audit.log

# API request patterns
grep "api_request" logs/structured.jsonl | jq '.details.endpoint' | sort | uniq -c
```

## Best Practices

### Configuration Management

1. **Version Control**: Keep `domains.json` in version control
2. **Backup**: Regular backups before changes
3. **Validation**: Always validate before deploying
4. **Gradual Rollout**: Test new domains in staging first

### Monitoring

1. **Regular Checks**: Set up automated monitoring
2. **Alert Thresholds**: Adjust thresholds based on your SLA
3. **Log Retention**: Configure appropriate log retention policies
4. **Performance Baselines**: Establish baseline metrics for comparison

### Security

1. **Access Control**: Restrict admin API access in production
2. **HTTPS**: Enable HTTPS for production deployments
3. **Rate Limiting**: Configure appropriate rate limits
4. **Audit Trail**: Monitor configuration changes

### Performance

1. **Cache Tuning**: Optimize cache timeouts per domain
2. **Resource Monitoring**: Monitor system resources
3. **Load Testing**: Test with expected concurrent users
4. **Scaling**: Plan for horizontal scaling if needed

### Maintenance

1. **Regular Updates**: Keep dependencies updated
2. **Log Rotation**: Implement log rotation to manage disk space
3. **Health Checks**: Regular health check automation
4. **Documentation**: Keep configuration documentation current

## API Authentication (Production)

For production deployments, implement authentication for admin endpoints:

```python
from functools import wraps
from flask import request, jsonify

def require_admin_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Implement your authentication logic here
        # Example: API key, JWT token, etc.
        auth_header = request.headers.get('Authorization')
        if not auth_header or not validate_admin_token(auth_header):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Apply to admin routes
@admin_bp.route('/domains')
@require_admin_auth
def list_domains():
    # ... existing code
```

## Integration Examples

### Monitoring Dashboard

Create a simple monitoring dashboard using the admin API:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Domain Monitor</title>
    <script>
        async function loadDomainStatus() {
            const response = await fetch('/api/admin/domains');
            const data = await response.json();
            
            const container = document.getElementById('domains');
            container.innerHTML = '';
            
            data.domains.forEach(domain => {
                const div = document.createElement('div');
                div.className = `domain-card ${domain.status}`;
                div.innerHTML = `
                    <h3>${domain.domain}</h3>
                    <p>Client: ${domain.client_name}</p>
                    <p>Status: ${domain.status}</p>
                    <p>Cache Hit Rate: ${domain.cache_stats.hit_rate_percent}%</p>
                `;
                container.appendChild(div);
            });
        }
        
        // Refresh every 30 seconds
        setInterval(loadDomainStatus, 30000);
        loadDomainStatus();
    </script>
</head>
<body>
    <h1>Domain Status Dashboard</h1>
    <div id="domains"></div>
</body>
</html>
```

### Automated Alerts

Set up automated alerts using the monitoring tool:

```bash
#!/bin/bash
# monitor-alert.sh

# Run monitor and capture output
OUTPUT=$(python domain_monitor.py --json)
STATUS=$?

# Check if there are critical issues
if [ $STATUS -ne 0 ]; then
    echo "CRITICAL: Domain monitoring detected issues"
    echo "$OUTPUT" | jq '.alerts'
    
    # Send alert (example: email, Slack, etc.)
    # curl -X POST -H 'Content-type: application/json' \
    #   --data '{"text":"Domain monitoring alert: Critical issues detected"}' \
    #   YOUR_SLACK_WEBHOOK_URL
fi
```

This comprehensive administration system provides all the tools needed to effectively manage and monitor your multi-domain dashboard deployment.
#!/usr/bin/env python3
"""
Domain Status Dashboard
Web-based dashboard for monitoring multi-domain system status
"""

from flask import Blueprint, render_template_string, jsonify, request
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

from domain_config import DomainConfigManager
from domain_cache import get_cache_manager
from domain_logger import get_domain_logger, LogCategory
from domain_monitor import DomainMonitor


# Create Blueprint for dashboard
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/admin/dashboard')


# HTML Template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Domain Dashboard - System Status</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, #059669, #10b981);
            color: white;
            padding: 2rem 0;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .status-overview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .status-card {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #059669;
        }
        
        .status-card.warning {
            border-left-color: #f59e0b;
        }
        
        .status-card.critical {
            border-left-color: #ef4444;
        }
        
        .status-card h3 {
            font-size: 1.1rem;
            color: #666;
            margin-bottom: 0.5rem;
        }
        
        .status-card .value {
            font-size: 2rem;
            font-weight: bold;
            color: #059669;
        }
        
        .status-card.warning .value {
            color: #f59e0b;
        }
        
        .status-card.critical .value {
            color: #ef4444;
        }
        
        .domains-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .domain-card {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: relative;
        }
        
        .domain-status {
            position: absolute;
            top: 1rem;
            right: 1rem;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: #059669;
        }
        
        .domain-status.warning {
            background-color: #f59e0b;
        }
        
        .domain-status.critical {
            background-color: #ef4444;
        }
        
        .domain-status.unknown {
            background-color: #6b7280;
        }
        
        .domain-card h3 {
            font-size: 1.3rem;
            margin-bottom: 0.5rem;
            color: #333;
        }
        
        .domain-card .client-name {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        
        .metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        
        .metric {
            text-align: center;
        }
        
        .metric .label {
            font-size: 0.8rem;
            color: #666;
            margin-bottom: 0.25rem;
        }
        
        .metric .value {
            font-size: 1.1rem;
            font-weight: bold;
            color: #333;
        }
        
        .refresh-info {
            text-align: center;
            color: #666;
            margin-top: 2rem;
            padding: 1rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }
        
        .error {
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #dc2626;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        
        .controls {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .btn {
            background: #059669;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
            margin: 0 0.5rem;
            transition: background-color 0.2s;
        }
        
        .btn:hover {
            background: #047857;
        }
        
        .btn.secondary {
            background: #6b7280;
        }
        
        .btn.secondary:hover {
            background: #4b5563;
        }
        
        .add-domain-form {
            background: white;
            border-radius: 10px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #059669;
        }
        
        .form-container h3 {
            color: #333;
            margin-bottom: 1.5rem;
            font-size: 1.5rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #333;
        }
        
        .form-group input {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e5e7eb;
            border-radius: 5px;
            font-size: 1rem;
            transition: border-color 0.2s;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #059669;
        }
        
        .form-group small {
            display: block;
            margin-top: 0.25rem;
            color: #666;
            font-size: 0.85rem;
        }
        
        .form-actions {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .success-message {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            color: #166534;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        
        .error-message {
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #dc2626;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .status-overview {
                grid-template-columns: 1fr;
            }
            
            .domains-grid {
                grid-template-columns: 1fr;
            }
            
            .form-row {
                grid-template-columns: 1fr;
            }
            
            .form-actions {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 Multi-Domain Dashboard</h1>
        <p>System Status & Monitoring</p>
    </div>
    
    <div class="container">
        <div class="controls">
            <button class="btn" onclick="refreshData()">🔄 Refresh Now</button>
            <button class="btn secondary" onclick="toggleAutoRefresh()">⏸️ Auto Refresh: ON</button>
            <button class="btn" onclick="toggleAddDomainForm()">➕ Add New Domain</button>
        </div>
        
        <!-- Add Domain Form -->
        <div id="add-domain-form" class="add-domain-form" style="display: none;">
            <div class="form-container">
                <h3>➕ Add New Domain</h3>
                <form id="domain-form" onsubmit="addNewDomain(event)">
                    <div class="form-group">
                        <label for="domain-name">Domain Name:</label>
                        <input type="text" id="domain-name" name="domain" placeholder="dashboard-cliente.com" required>
                        <small>Example: dashboard-cliente.com or cliente.mydomain.com</small>
                    </div>
                    
                    <div class="form-group">
                        <label for="client-name">Client Name:</label>
                        <input type="text" id="client-name" name="client_name" placeholder="Cliente Name" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="google-sheet-id">Google Sheet ID:</label>
                        <input type="text" id="google-sheet-id" name="google_sheet_id" placeholder="1ABC123DEF456..." required>
                        <small>Get this from the Google Sheets URL: /d/[ID]/edit</small>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="primary-color">Primary Color:</label>
                            <input type="color" id="primary-color" name="primary_color" value="#059669">
                        </div>
                        
                        <div class="form-group">
                            <label for="secondary-color">Secondary Color:</label>
                            <input type="color" id="secondary-color" name="secondary_color" value="#10b981">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="cache-timeout">Cache Timeout (seconds):</label>
                        <input type="number" id="cache-timeout" name="cache_timeout" value="300" min="60" max="3600">
                    </div>
                    
                    <div class="form-actions">
                        <button type="submit" class="btn">✅ Add Domain</button>
                        <button type="button" class="btn secondary" onclick="toggleAddDomainForm()">❌ Cancel</button>
                    </div>
                </form>
            </div>
        </div>
        
        <div id="loading" class="loading">
            <p>Loading system status...</p>
        </div>
        
        <div id="error" class="error" style="display: none;">
            <p>Error loading data. Please try refreshing the page.</p>
        </div>
        
        <div id="dashboard-content" style="display: none;">
            <div class="status-overview">
                <div class="status-card" id="total-domains-card">
                    <h3>Total Domains</h3>
                    <div class="value" id="total-domains">-</div>
                </div>
                
                <div class="status-card" id="healthy-domains-card">
                    <h3>Healthy Domains</h3>
                    <div class="value" id="healthy-domains">-</div>
                </div>
                
                <div class="status-card" id="avg-response-card">
                    <h3>Avg Response Time</h3>
                    <div class="value" id="avg-response">-</div>
                </div>
                
                <div class="status-card" id="cache-hit-rate-card">
                    <h3>Cache Hit Rate</h3>
                    <div class="value" id="cache-hit-rate">-</div>
                </div>
            </div>
            
            <div id="domains-container" class="domains-grid">
                <!-- Domain cards will be populated here -->
            </div>
        </div>
        
        <div class="refresh-info">
            <p>Last updated: <span id="last-updated">Never</span></p>
            <p>Auto-refresh every 30 seconds</p>
        </div>
    </div>

    <script>
        let autoRefreshEnabled = true;
        let refreshInterval;
        
        async function loadDashboardData() {
            try {
                document.getElementById('loading').style.display = 'block';
                document.getElementById('error').style.display = 'none';
                document.getElementById('dashboard-content').style.display = 'none';
                
                const response = await fetch('/admin/dashboard/api/status');
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.error || 'Unknown error');
                }
                
                updateDashboard(data);
                
                document.getElementById('loading').style.display = 'none';
                document.getElementById('dashboard-content').style.display = 'block';
                
            } catch (error) {
                console.error('Error loading dashboard data:', error);
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').style.display = 'block';
                document.getElementById('dashboard-content').style.display = 'none';
            }
        }
        
        function updateDashboard(data) {
            const overview = data.overview;
            const domains = data.domains;
            
            // Update overview cards
            document.getElementById('total-domains').textContent = overview.total_domains;
            document.getElementById('healthy-domains').textContent = overview.healthy_domains;
            document.getElementById('avg-response').textContent = overview.avg_response_time_ms + 'ms';
            document.getElementById('cache-hit-rate').textContent = overview.avg_cache_hit_rate + '%';
            
            // Update card styles based on status
            updateCardStatus('healthy-domains-card', overview.healthy_domains, overview.total_domains);
            updateCardStatus('avg-response-card', overview.avg_response_time_ms, null, 'response');
            updateCardStatus('cache-hit-rate-card', overview.avg_cache_hit_rate, null, 'cache');
            
            // Update domains
            const container = document.getElementById('domains-container');
            container.innerHTML = '';
            
            domains.forEach(domain => {
                const domainCard = createDomainCard(domain);
                container.appendChild(domainCard);
            });
            
            // Update timestamp
            document.getElementById('last-updated').textContent = new Date().toLocaleString();
        }
        
        function updateCardStatus(cardId, value, total, type) {
            const card = document.getElementById(cardId);
            card.className = 'status-card';
            
            if (type === 'response') {
                if (value > 3000) {
                    card.classList.add('critical');
                } else if (value > 1000) {
                    card.classList.add('warning');
                }
            } else if (type === 'cache') {
                if (value < 50) {
                    card.classList.add('warning');
                } else if (value < 30) {
                    card.classList.add('critical');
                }
            } else if (total) {
                const ratio = value / total;
                if (ratio < 0.5) {
                    card.classList.add('critical');
                } else if (ratio < 0.8) {
                    card.classList.add('warning');
                }
            }
        }
        
        function createDomainCard(domain) {
            const card = document.createElement('div');
            card.className = 'domain-card';
            
            card.innerHTML = `
                <div class="domain-status ${domain.status}"></div>
                <h3>${domain.domain}</h3>
                <div class="client-name">${domain.client_name}</div>
                <div class="metrics">
                    <div class="metric">
                        <div class="label">Response Time</div>
                        <div class="value">${domain.response_time_ms || 'N/A'}</div>
                    </div>
                    <div class="metric">
                        <div class="label">Cache Hit Rate</div>
                        <div class="value">${domain.cache_hit_rate}%</div>
                    </div>
                    <div class="metric">
                        <div class="label">Errors (24h)</div>
                        <div class="value">${domain.error_count_24h}</div>
                    </div>
                    <div class="metric">
                        <div class="label">Status</div>
                        <div class="value">${domain.status}</div>
                    </div>
                </div>
            `;
            
            return card;
        }
        
        function refreshData() {
            loadDashboardData();
        }
        
        function toggleAutoRefresh() {
            autoRefreshEnabled = !autoRefreshEnabled;
            const button = document.querySelector('.btn.secondary');
            
            if (autoRefreshEnabled) {
                button.textContent = '⏸️ Auto Refresh: ON';
                startAutoRefresh();
            } else {
                button.textContent = '▶️ Auto Refresh: OFF';
                stopAutoRefresh();
            }
        }
        
        function startAutoRefresh() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
            
            refreshInterval = setInterval(() => {
                if (autoRefreshEnabled) {
                    loadDashboardData();
                }
            }, 30000); // 30 seconds
        }
        
        function stopAutoRefresh() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
                refreshInterval = null;
            }
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboardData();
            startAutoRefresh();
        });
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                stopAutoRefresh();
            } else if (autoRefreshEnabled) {
                loadDashboardData();
                startAutoRefresh();
            }
        });
        
        // Add Domain Form Functions
        function toggleAddDomainForm() {
            const form = document.getElementById('add-domain-form');
            const isVisible = form.style.display !== 'none';
            
            if (isVisible) {
                form.style.display = 'none';
                clearForm();
            } else {
                form.style.display = 'block';
                document.getElementById('domain-name').focus();
            }
        }
        
        function clearForm() {
            document.getElementById('domain-form').reset();
            document.getElementById('primary-color').value = '#059669';
            document.getElementById('secondary-color').value = '#10b981';
            document.getElementById('cache-timeout').value = '300';
            
            // Remove any existing messages
            const existingMessages = document.querySelectorAll('.success-message, .error-message');
            existingMessages.forEach(msg => msg.remove());
        }
        
        async function addNewDomain(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const domainData = {
                domain: formData.get('domain'),
                client_name: formData.get('client_name'),
                google_sheet_id: formData.get('google_sheet_id'),
                primary_color: formData.get('primary_color'),
                secondary_color: formData.get('secondary_color'),
                cache_timeout: parseInt(formData.get('cache_timeout'))
            };
            
            // Remove existing messages
            const existingMessages = document.querySelectorAll('.success-message, .error-message');
            existingMessages.forEach(msg => msg.remove());
            
            try {
                const response = await fetch('/admin/dashboard/api/add-domain', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(domainData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showMessage('✅ Domain added successfully! Refreshing dashboard...', 'success');
                    
                    // Clear form and hide it
                    setTimeout(() => {
                        clearForm();
                        toggleAddDomainForm();
                        refreshData(); // Refresh the dashboard data
                    }, 2000);
                } else {
                    showMessage('❌ Error: ' + (result.error || 'Failed to add domain'), 'error');
                }
                
            } catch (error) {
                console.error('Error adding domain:', error);
                showMessage('❌ Network error: ' + error.message, 'error');
            }
        }
        
        function showMessage(text, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = type + '-message';
            messageDiv.textContent = text;
            
            const form = document.getElementById('add-domain-form');
            form.appendChild(messageDiv);
            
            // Auto-remove error messages after 5 seconds
            if (type === 'error') {
                setTimeout(() => {
                    if (messageDiv.parentNode) {
                        messageDiv.remove();
                    }
                }, 5000);
            }
        }
    </script>
</body>
</html>
"""


@dashboard_bp.route('/')
def dashboard_home():
    """Serve the main dashboard page"""
    return render_template_string(DASHBOARD_HTML)


@dashboard_bp.route('/api/status')
def dashboard_api_status():
    """API endpoint for dashboard data"""
    try:
        # Initialize monitor
        monitor = DomainMonitor()
        
        # Get health metrics for all domains
        health_metrics = monitor.check_all_domains()
        
        # Generate comprehensive report
        report = monitor.generate_health_report(health_metrics)
        
        # Format data for dashboard
        dashboard_data = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'overview': {
                'total_domains': report['summary']['total_domains'],
                'healthy_domains': report['summary']['healthy'],
                'warning_domains': report['summary']['warning'],
                'critical_domains': report['summary']['critical'],
                'unknown_domains': report['summary']['unknown'],
                'overall_status': report['summary']['overall_status'],
                'avg_response_time_ms': report['system_metrics']['avg_response_time_ms'],
                'avg_cache_hit_rate': report['system_metrics']['avg_cache_hit_rate_percent'],
                'total_errors_24h': report['system_metrics']['total_errors_24h']
            },
            'domains': [
                {
                    'domain': domain,
                    'client_name': metrics.domain,  # Will be updated with actual client name
                    'status': metrics.status,
                    'response_time_ms': round(metrics.response_time * 1000, 1) if metrics.response_time else None,
                    'cache_hit_rate': round(metrics.cache_hit_rate, 1),
                    'error_count_24h': metrics.error_count_24h,
                    'last_successful_request': metrics.last_successful_request.isoformat() if metrics.last_successful_request else None,
                    'data_freshness_minutes': round(metrics.data_freshness.total_seconds() / 60, 1) if metrics.data_freshness else None
                }
                for domain, metrics in health_metrics.items()
            ],
            'alerts': report['alerts']
        }
        
        # Enhance domain data with configuration info
        try:
            from flask import current_app
            config_manager = current_app.config.get('DOMAIN_CONFIG_MANAGER')
            
            if config_manager:
                for domain_data in dashboard_data['domains']:
                    try:
                        domain_config = config_manager.get_config_by_domain(domain_data['domain'])
                        domain_data['client_name'] = domain_config.client_name
                        domain_data['enabled'] = domain_config.enabled
                        domain_data['cache_timeout'] = domain_config.cache_timeout
                    except Exception:
                        pass  # Keep default values
        except Exception:
            pass  # Continue without enhanced data
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@dashboard_bp.route('/api/domain/<domain>/details')
def dashboard_domain_details(domain: str):
    """Get detailed information for a specific domain"""
    try:
        monitor = DomainMonitor()
        metrics = monitor.check_domain_health(domain)
        
        # Get additional details
        from flask import current_app
        config_manager = current_app.config.get('DOMAIN_CONFIG_MANAGER')
        cache_manager = get_cache_manager()
        logger = get_domain_logger()
        
        domain_details = {
            'success': True,
            'domain': domain,
            'health_metrics': metrics.to_dict(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add configuration details
        if config_manager:
            try:
                domain_config = config_manager.get_config_by_domain(domain)
                domain_details['configuration'] = {
                    'client_name': domain_config.client_name,
                    'google_sheet_id': domain_config.google_sheet_id,
                    'cache_timeout': domain_config.cache_timeout,
                    'enabled': domain_config.enabled,
                    'theme': domain_config.theme.to_dict()
                }
            except Exception as e:
                domain_details['configuration_error'] = str(e)
        
        # Add cache statistics
        cache_stats = cache_manager.get_cache_stats(domain)
        domain_details['cache_statistics'] = cache_stats
        
        # Add recent logs
        recent_logs = logger.get_domain_logs(domain, limit=10)
        domain_details['recent_logs'] = recent_logs
        
        # Add error summary
        error_summary = logger.get_error_summary(domain, hours=24)
        domain_details['error_summary'] = error_summary
        
        return jsonify(domain_details)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'domain': domain,
            'timestamp': datetime.now().isoformat()
        }), 500


@dashboard_bp.route('/api/add-domain', methods=['POST'])
def add_new_domain():
    """Add a new domain to the configuration using the domain config manager"""
    try:
        from flask import current_app, request
        import tempfile
        import shutil
        
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['domain', 'client_name', 'google_sheet_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Get config manager
        config_manager = current_app.config.get('DOMAIN_CONFIG_MANAGER')
        if not config_manager:
            return jsonify({
                'success': False,
                'error': 'Domain configuration manager not available'
            }), 500
        
        # Check if domain already exists
        all_domains = config_manager.get_all_domains()
        if data['domain'] in all_domains:
            return jsonify({
                'success': False,
                'error': f'Domain {data["domain"]} already exists'
            }), 400
        
        # Generate accent colors based on primary color
        primary_color = data.get('primary_color', '#059669')
        secondary_color = data.get('secondary_color', '#10b981')
        
        # Create accent colors (lighter variations)
        accent_colors = [
            lighten_color(primary_color, 0.3),
            lighten_color(primary_color, 0.5),
            lighten_color(primary_color, 0.7)
        ]
        
        # Create new domain configuration
        new_domain_config = {
            'google_sheet_id': data['google_sheet_id'],
            'client_name': data['client_name'],
            'theme': {
                'primary_color': primary_color,
                'secondary_color': secondary_color,
                'accent_colors': accent_colors
            },
            'cache_timeout': data.get('cache_timeout', 300),
            'enabled': True
        }
        
        # Use a more robust approach to update the configuration
        try:
            # Read current configuration
            config_file_path = str(config_manager.config_file_path)
            
            with open(config_file_path, 'r') as f:
                config = json.load(f)
            
            # Add new domain
            if 'domains' not in config:
                config['domains'] = {}
            
            config['domains'][data['domain']] = new_domain_config
            
            # Add domain to security whitelist
            if 'security' not in config:
                config['security'] = {'additional_whitelist': []}
            
            if 'additional_whitelist' not in config['security']:
                config['security']['additional_whitelist'] = []
            
            # Add the new domain to whitelist if not already present
            if data['domain'] not in config['security']['additional_whitelist']:
                config['security']['additional_whitelist'].append(data['domain'])
            
            # Write to temporary file first, then move (atomic operation)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(config, temp_file, indent=2)
                temp_file_path = temp_file.name
            
            # Move temporary file to actual location
            shutil.move(temp_file_path, config_file_path)
            
            # Reload configuration
            config_manager.reload_configurations()
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to save configuration: {str(e)}'
            }), 500
        
        # Log the addition
        logger = get_domain_logger()
        logger.audit(
            f"New domain added via dashboard: {data['domain']} for client {data['client_name']}",
            details={'action': 'add_domain', 'domain': data['domain'], 'client_name': data['client_name']}
        )
        
        return jsonify({
            'success': True,
            'message': f'Domain {data["domain"]} added successfully',
            'domain': data['domain'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger = get_domain_logger()
        logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to add domain: {str(e)}"
        )
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


def lighten_color(hex_color: str, factor: float) -> str:
    """Lighten a hex color by a given factor (0.0 to 1.0)"""
    try:
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Lighten each component
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
        
    except Exception:
        # Return default accent colors if conversion fails
        return ["#34d399", "#6ee7b7", "#a7f3d0"][int(factor * 2)]


def register_dashboard_blueprint(app):
    """Register the dashboard blueprint with the Flask app"""
    app.register_blueprint(dashboard_bp)
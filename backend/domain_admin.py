#!/usr/bin/env python3
"""
Domain Administration Module
Provides administration and monitoring tools for multi-domain dashboard system
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os
from pathlib import Path

from domain_config import DomainConfigManager, DomainConfig, ThemeConfig
from domain_cache import get_cache_manager
from domain_logger import get_domain_logger, LogCategory
from domain_middleware import get_current_domain, get_current_config, require_domain_context


# Create Blueprint for admin endpoints
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/domains', methods=['GET'])
def list_domains():
    """List all configured domains with their status"""
    try:
        # Get domain config manager from app context
        config_manager = current_app.config.get('DOMAIN_CONFIG_MANAGER')
        if not config_manager:
            return jsonify({'error': 'Domain configuration manager not available'}), 500
        
        cache_manager = get_cache_manager()
        logger = get_domain_logger()
        
        domains_info = []
        all_domains = config_manager.get_all_domains()
        
        for domain in all_domains:
            try:
                domain_config = config_manager.get_config_by_domain(domain)
                cache_stats = cache_manager.get_cache_stats(domain)
                error_summary = logger.get_error_summary(domain, hours=24)
                
                domain_info = {
                    'domain': domain,
                    'client_name': domain_config.client_name,
                    'google_sheet_id': domain_config.google_sheet_id,
                    'enabled': domain_config.enabled,
                    'cache_timeout': domain_config.cache_timeout,
                    'theme': domain_config.theme.to_dict(),
                    'cache_stats': cache_stats,
                    'error_summary': {
                        'total_errors_24h': error_summary['total_errors'],
                        'error_categories': error_summary['error_by_category']
                    },
                    'status': 'healthy' if error_summary['total_errors'] < 10 else 'warning'
                }
                domains_info.append(domain_info)
                
            except Exception as e:
                # Include domains with errors in the list
                domains_info.append({
                    'domain': domain,
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'domains': domains_info,
            'total_domains': len(domains_info),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger = get_domain_logger()
        logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to list domains: {str(e)}"
        )
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@admin_bp.route('/domains/<domain>/status', methods=['GET'])
def get_domain_status(domain: str):
    """Get detailed status for a specific domain"""
    try:
        config_manager = current_app.config.get('DOMAIN_CONFIG_MANAGER')
        if not config_manager:
            return jsonify({'error': 'Domain configuration manager not available'}), 500
        
        cache_manager = get_cache_manager()
        logger = get_domain_logger()
        
        # Get domain configuration
        try:
            domain_config = config_manager.get_config_by_domain(domain)
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Domain {domain} not found'
            }), 404
        
        # Get cache statistics
        cache_stats = cache_manager.get_cache_stats(domain)
        
        # Get error summary
        error_summary = logger.get_error_summary(domain, hours=24)
        
        # Get recent logs
        recent_logs = logger.get_domain_logs(domain, limit=20)
        
        # Test data access (basic health check)
        data_access_status = 'unknown'
        try:
            from multi_domain_analyzer import create_analyzer_for_domain
            analyzer = create_analyzer_for_domain(domain_config, cache_manager)
            # Just check if we can create analyzer, don't fetch data
            data_access_status = 'healthy'
        except Exception as e:
            data_access_status = f'error: {str(e)}'
        
        domain_status = {
            'domain': domain,
            'client_name': domain_config.client_name,
            'google_sheet_id': domain_config.google_sheet_id,
            'enabled': domain_config.enabled,
            'cache_timeout': domain_config.cache_timeout,
            'theme': domain_config.theme.to_dict(),
            'custom_settings': domain_config.custom_settings,
            'cache_stats': cache_stats,
            'error_summary': error_summary,
            'recent_logs': recent_logs,
            'data_access_status': data_access_status,
            'health_status': _calculate_health_status(error_summary, cache_stats, data_access_status),
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'domain_status': domain_status
        })
        
    except Exception as e:
        logger = get_domain_logger()
        logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to get domain status for {domain}: {str(e)}"
        )
        return jsonify({
            'success': False,
            'error': str(e),
            'domain': domain
        }), 500


@admin_bp.route('/metrics/overview', methods=['GET'])
def get_metrics_overview():
    """Get system-wide metrics overview"""
    try:
        config_manager = current_app.config.get('DOMAIN_CONFIG_MANAGER')
        if not config_manager:
            return jsonify({'error': 'Domain configuration manager not available'}), 500
        
        cache_manager = get_cache_manager()
        logger = get_domain_logger()
        
        # Get all cache stats
        all_cache_stats = cache_manager.get_all_cache_stats()
        
        # Calculate aggregate metrics
        total_cache_entries = sum(stats['total_entries'] for stats in all_cache_stats.values())
        total_cache_hits = sum(stats['total_hits'] for stats in all_cache_stats.values())
        total_cache_misses = sum(stats['total_misses'] for stats in all_cache_stats.values())
        
        # Calculate system-wide hit rate
        total_requests = total_cache_hits + total_cache_misses
        system_hit_rate = (total_cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        # Get error summary for all domains
        system_error_summary = logger.get_error_summary(domain=None, hours=24)
        
        # Get domain health status
        domains = config_manager.get_all_domains()
        healthy_domains = 0
        warning_domains = 0
        error_domains = 0
        
        for domain in domains:
            try:
                domain_config = config_manager.get_config_by_domain(domain)
                if domain_config.enabled:
                    domain_errors = logger.get_error_summary(domain, hours=24)
                    if domain_errors['total_errors'] == 0:
                        healthy_domains += 1
                    elif domain_errors['total_errors'] < 10:
                        warning_domains += 1
                    else:
                        error_domains += 1
                else:
                    # Disabled domains count as warning
                    warning_domains += 1
            except Exception:
                error_domains += 1
        
        metrics_overview = {
            'system_status': {
                'total_domains': len(domains),
                'healthy_domains': healthy_domains,
                'warning_domains': warning_domains,
                'error_domains': error_domains,
                'overall_status': _calculate_overall_system_status(healthy_domains, warning_domains, error_domains)
            },
            'cache_metrics': {
                'total_entries': total_cache_entries,
                'total_hits': total_cache_hits,
                'total_misses': total_cache_misses,
                'hit_rate_percent': round(system_hit_rate, 2),
                'domains_with_cache': len(all_cache_stats)
            },
            'error_metrics': {
                'total_errors_24h': system_error_summary['total_errors'],
                'error_by_category': system_error_summary['error_by_category'],
                'recent_errors': system_error_summary['recent_errors'][:5]  # Top 5 recent errors
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics_overview
        })
        
    except Exception as e:
        logger = get_domain_logger()
        logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to get metrics overview: {str(e)}"
        )
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/config/validate', methods=['POST'])
def validate_configuration():
    """Validate domain configuration"""
    try:
        config_manager = current_app.config.get('DOMAIN_CONFIG_MANAGER')
        if not config_manager:
            return jsonify({'error': 'Domain configuration manager not available'}), 500
        
        logger = get_domain_logger()
        
        # Get configuration data from request
        config_data = request.get_json()
        if not config_data:
            return jsonify({
                'success': False,
                'error': 'No configuration data provided'
            }), 400
        
        # Validate configuration
        validation_errors = config_manager.validate_config(config_data)
        
        # Additional validation checks
        additional_checks = _perform_additional_validation(config_data)
        
        validation_result = {
            'valid': len(validation_errors) == 0 and len(additional_checks['errors']) == 0,
            'errors': validation_errors + additional_checks['errors'],
            'warnings': additional_checks['warnings'],
            'suggestions': additional_checks['suggestions'],
            'validated_at': datetime.now().isoformat()
        }
        
        # Log validation attempt
        logger.info(
            LogCategory.CONFIGURATION,
            f"Configuration validation performed",
            details={
                'valid': validation_result['valid'],
                'error_count': len(validation_result['errors']),
                'warning_count': len(validation_result['warnings'])
            }
        )
        
        return jsonify({
            'success': True,
            'validation': validation_result
        })
        
    except Exception as e:
        logger = get_domain_logger()
        logger.error(
            LogCategory.ERROR_HANDLING,
            f"Configuration validation failed: {str(e)}"
        )
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/config/reload', methods=['POST'])
def reload_configuration():
    """Reload domain configuration from file"""
    try:
        config_manager = current_app.config.get('DOMAIN_CONFIG_MANAGER')
        if not config_manager:
            return jsonify({'error': 'Domain configuration manager not available'}), 500
        
        logger = get_domain_logger()
        
        # Get domains before reload
        old_domains = set(config_manager.get_all_domains())
        
        # Reload configuration
        config_manager.reload_configurations()
        
        # Get domains after reload
        new_domains = set(config_manager.get_all_domains())
        
        # Calculate changes
        added_domains = new_domains - old_domains
        removed_domains = old_domains - new_domains
        
        reload_result = {
            'success': True,
            'total_domains': len(new_domains),
            'added_domains': list(added_domains),
            'removed_domains': list(removed_domains),
            'reloaded_at': datetime.now().isoformat()
        }
        
        # Log configuration reload
        logger.audit(
            "Configuration reloaded via admin API",
            details=reload_result
        )
        
        return jsonify(reload_result)
        
    except Exception as e:
        logger = get_domain_logger()
        logger.error(
            LogCategory.ERROR_HANDLING,
            f"Configuration reload failed: {str(e)}"
        )
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear cache for specific domain or all domains"""
    try:
        cache_manager = get_cache_manager()
        logger = get_domain_logger()
        
        # Get optional domain parameter
        data = request.get_json() or {}
        target_domain = data.get('domain')
        
        if target_domain:
            # Clear cache for specific domain
            cleared_count = cache_manager.clear_domain_cache(target_domain)
            
            result = {
                'success': True,
                'action': 'domain_cache_cleared',
                'domain': target_domain,
                'cleared_entries': cleared_count,
                'cleared_at': datetime.now().isoformat()
            }
            
            logger.info(
                LogCategory.CACHE_OPERATION,
                f"Cache cleared for domain {target_domain}",
                details={'cleared_entries': cleared_count}
            )
        else:
            # Clear cache for all domains
            all_stats = cache_manager.get_all_cache_stats()
            total_cleared = 0
            cleared_domains = []
            
            for domain in all_stats.keys():
                cleared_count = cache_manager.clear_domain_cache(domain)
                total_cleared += cleared_count
                if cleared_count > 0:
                    cleared_domains.append({'domain': domain, 'cleared_entries': cleared_count})
            
            result = {
                'success': True,
                'action': 'all_cache_cleared',
                'total_cleared_entries': total_cleared,
                'cleared_domains': cleared_domains,
                'cleared_at': datetime.now().isoformat()
            }
            
            logger.info(
                LogCategory.CACHE_OPERATION,
                "Cache cleared for all domains",
                details={'total_cleared_entries': total_cleared, 'domains_count': len(cleared_domains)}
            )
        
        return jsonify(result)
        
    except Exception as e:
        logger = get_domain_logger()
        logger.error(
            LogCategory.ERROR_HANDLING,
            f"Cache clear operation failed: {str(e)}"
        )
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/logs/<domain>', methods=['GET'])
def get_domain_logs(domain: str):
    """Get logs for a specific domain"""
    try:
        logger = get_domain_logger()
        
        # Get query parameters
        limit = min(int(request.args.get('limit', 50)), 200)  # Max 200 logs
        level = request.args.get('level')  # Optional level filter
        category = request.args.get('category')  # Optional category filter
        
        # Get domain logs
        domain_logs = logger.get_domain_logs(domain, limit=limit * 2)  # Get more to allow filtering
        
        # Apply filters
        if level:
            domain_logs = [log for log in domain_logs if log.get('level') == level.upper()]
        
        if category:
            domain_logs = [log for log in domain_logs if log.get('category') == category]
        
        # Limit results
        domain_logs = domain_logs[:limit]
        
        return jsonify({
            'success': True,
            'domain': domain,
            'logs': domain_logs,
            'total_returned': len(domain_logs),
            'filters': {
                'level': level,
                'category': category,
                'limit': limit
            },
            'retrieved_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger = get_domain_logger()
        logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to retrieve logs for domain {domain}: {str(e)}"
        )
        return jsonify({
            'success': False,
            'error': str(e),
            'domain': domain
        }), 500


@admin_bp.route('/audit-trail', methods=['GET'])
def get_audit_trail():
    """Get audit trail of configuration changes"""
    try:
        logger = get_domain_logger()
        
        # Get query parameters
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 entries
        
        # Get audit trail
        audit_entries = logger.get_audit_trail(limit=limit)
        
        return jsonify({
            'success': True,
            'audit_entries': audit_entries,
            'total_returned': len(audit_entries),
            'retrieved_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger = get_domain_logger()
        logger.error(
            LogCategory.ERROR_HANDLING,
            f"Failed to retrieve audit trail: {str(e)}"
        )
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _calculate_health_status(error_summary: Dict, cache_stats: Dict, data_access_status: str) -> str:
    """Calculate health status based on various metrics"""
    if 'error:' in data_access_status:
        return 'critical'
    
    error_count = error_summary.get('total_errors', 0)
    
    if error_count == 0:
        return 'healthy'
    elif error_count < 5:
        return 'warning'
    elif error_count < 20:
        return 'degraded'
    else:
        return 'critical'


def _calculate_overall_system_status(healthy: int, warning: int, error: int) -> str:
    """Calculate overall system status"""
    total = healthy + warning + error
    
    if total == 0:
        return 'unknown'
    
    if error > 0:
        return 'critical'
    elif warning > healthy:
        return 'degraded'
    elif warning > 0:
        return 'warning'
    else:
        return 'healthy'


def _perform_additional_validation(config_data: Dict) -> Dict[str, List[str]]:
    """Perform additional validation checks beyond basic schema validation"""
    errors = []
    warnings = []
    suggestions = []
    
    try:
        domains = config_data.get('domains', {})
        
        # Check for duplicate Google Sheet IDs
        sheet_ids = {}
        for domain, domain_config in domains.items():
            sheet_id = domain_config.get('google_sheet_id')
            if sheet_id:
                if sheet_id in sheet_ids:
                    warnings.append(f"Duplicate Google Sheet ID '{sheet_id}' found in domains '{sheet_ids[sheet_id]}' and '{domain}'")
                else:
                    sheet_ids[sheet_id] = domain
        
        # Check cache timeout values
        for domain, domain_config in domains.items():
            cache_timeout = domain_config.get('cache_timeout', 300)
            if cache_timeout < 60:
                warnings.append(f"Domain '{domain}' has very low cache timeout ({cache_timeout}s), consider increasing for better performance")
            elif cache_timeout > 3600:
                warnings.append(f"Domain '{domain}' has very high cache timeout ({cache_timeout}s), consider reducing for fresher data")
        
        # Check theme color formats
        for domain, domain_config in domains.items():
            theme = domain_config.get('theme', {})
            for color_key in ['primary_color', 'secondary_color']:
                color = theme.get(color_key)
                if color and not color.startswith('#'):
                    errors.append(f"Domain '{domain}' theme color '{color_key}' should start with '#'")
            
            accent_colors = theme.get('accent_colors', [])
            if len(accent_colors) < 2:
                suggestions.append(f"Domain '{domain}' should have at least 2 accent colors for better theming")
        
        # Check for reasonable client names
        for domain, domain_config in domains.items():
            client_name = domain_config.get('client_name', '')
            if len(client_name) < 2:
                warnings.append(f"Domain '{domain}' has very short client name")
            elif len(client_name) > 50:
                warnings.append(f"Domain '{domain}' has very long client name, consider shortening")
        
        # Check if default_config exists
        if 'default_config' not in config_data:
            suggestions.append("Consider adding a 'default_config' section for fallback configuration")
        
        # Performance suggestions
        if len(domains) > 10:
            suggestions.append("With many domains configured, consider monitoring system performance and cache usage")
        
    except Exception as e:
        errors.append(f"Error during additional validation: {str(e)}")
    
    return {
        'errors': errors,
        'warnings': warnings,
        'suggestions': suggestions
    }


def register_admin_blueprint(app):
    """Register the admin blueprint with the Flask app"""
    app.register_blueprint(admin_bp)
    
    # Store config manager in app config for access in routes
    if hasattr(app, 'domain_config_manager'):
        app.config['DOMAIN_CONFIG_MANAGER'] = app.domain_config_manager
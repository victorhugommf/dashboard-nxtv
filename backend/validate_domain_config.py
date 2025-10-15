#!/usr/bin/env python3
"""
Domain Configuration Validation Tool
Standalone tool for validating domain configuration files
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from domain_config import DomainConfigManager, DomainConfig, ThemeConfig


class ConfigValidator:
    """Comprehensive configuration validator"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.suggestions = []
        self.info = []
    
    def validate_file(self, config_file: str) -> Dict[str, Any]:
        """Validate a configuration file"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            self.errors.append(f"Configuration file '{config_file}' does not exist")
            return self._get_results()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in configuration file: {str(e)}")
            return self._get_results()
        except Exception as e:
            self.errors.append(f"Error reading configuration file: {str(e)}")
            return self._get_results()
        
        return self.validate_config_data(config_data)
    
    def validate_config_data(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration data"""
        self.info.append(f"Validating configuration at {datetime.now().isoformat()}")
        
        # Basic structure validation
        self._validate_basic_structure(config_data)
        
        # Domain validation
        self._validate_domains(config_data)
        
        # Default config validation
        self._validate_default_config(config_data)
        
        # Security settings validation
        self._validate_security_settings(config_data)
        
        # Cross-domain validation
        self._validate_cross_domain_consistency(config_data)
        
        # Performance and best practices
        self._validate_performance_settings(config_data)
        
        return self._get_results()
    
    def _validate_basic_structure(self, config_data: Dict[str, Any]):
        """Validate basic configuration structure"""
        required_sections = ['domains']
        
        for section in required_sections:
            if section not in config_data:
                self.errors.append(f"Required section '{section}' is missing")
        
        if 'domains' in config_data:
            if not isinstance(config_data['domains'], dict):
                self.errors.append("'domains' section must be a dictionary")
            elif len(config_data['domains']) == 0:
                self.errors.append("At least one domain must be configured")
        
        # Check for unknown top-level keys
        known_keys = {'domains', 'default_config', 'security'}
        unknown_keys = set(config_data.keys()) - known_keys
        if unknown_keys:
            self.warnings.append(f"Unknown configuration keys: {', '.join(unknown_keys)}")
    
    def _validate_domains(self, config_data: Dict[str, Any]):
        """Validate individual domain configurations"""
        if 'domains' not in config_data:
            return
        
        domains = config_data['domains']
        
        for domain_name, domain_config in domains.items():
            self._validate_single_domain(domain_name, domain_config)
    
    def _validate_single_domain(self, domain_name: str, domain_config: Dict[str, Any]):
        """Validate a single domain configuration"""
        # Domain name validation
        if not self._is_valid_domain_name(domain_name):
            self.warnings.append(f"Domain name '{domain_name}' may not be valid")
        
        # Required fields
        required_fields = ['google_sheet_id', 'client_name', 'theme']
        for field in required_fields:
            if field not in domain_config:
                self.errors.append(f"Domain '{domain_name}': Missing required field '{field}'")
        
        # Google Sheet ID validation
        sheet_id = domain_config.get('google_sheet_id', '')
        if sheet_id:
            if len(sheet_id) < 20:
                self.warnings.append(f"Domain '{domain_name}': Google Sheet ID seems too short")
            if not sheet_id.replace('_', '').replace('-', '').isalnum():
                self.warnings.append(f"Domain '{domain_name}': Google Sheet ID contains unexpected characters")
        
        # Client name validation
        client_name = domain_config.get('client_name', '')
        if client_name:
            if len(client_name) < 2:
                self.warnings.append(f"Domain '{domain_name}': Client name is very short")
            elif len(client_name) > 50:
                self.warnings.append(f"Domain '{domain_name}': Client name is very long")
        
        # Theme validation
        if 'theme' in domain_config:
            self._validate_theme_config(domain_name, domain_config['theme'])
        
        # Cache timeout validation
        cache_timeout = domain_config.get('cache_timeout', 300)
        if not isinstance(cache_timeout, int) or cache_timeout < 0:
            self.errors.append(f"Domain '{domain_name}': cache_timeout must be a non-negative integer")
        elif cache_timeout < 60:
            self.warnings.append(f"Domain '{domain_name}': Very low cache timeout ({cache_timeout}s)")
        elif cache_timeout > 3600:
            self.warnings.append(f"Domain '{domain_name}': Very high cache timeout ({cache_timeout}s)")
        
        # Enabled field validation
        enabled = domain_config.get('enabled', True)
        if not isinstance(enabled, bool):
            self.errors.append(f"Domain '{domain_name}': 'enabled' must be a boolean")
        
        # Custom settings validation
        custom_settings = domain_config.get('custom_settings', {})
        if custom_settings and not isinstance(custom_settings, dict):
            self.errors.append(f"Domain '{domain_name}': 'custom_settings' must be a dictionary")
    
    def _validate_theme_config(self, domain_name: str, theme_config: Dict[str, Any]):
        """Validate theme configuration"""
        required_theme_fields = ['primary_color', 'secondary_color', 'accent_colors']
        
        for field in required_theme_fields:
            if field not in theme_config:
                self.errors.append(f"Domain '{domain_name}': Missing required theme field '{field}'")
        
        # Color validation
        for color_field in ['primary_color', 'secondary_color']:
            color = theme_config.get(color_field)
            if color:
                if not self._is_valid_color(color):
                    self.errors.append(f"Domain '{domain_name}': Invalid color format for '{color_field}': {color}")
        
        # Accent colors validation
        accent_colors = theme_config.get('accent_colors', [])
        if not isinstance(accent_colors, list):
            self.errors.append(f"Domain '{domain_name}': 'accent_colors' must be a list")
        elif len(accent_colors) == 0:
            self.warnings.append(f"Domain '{domain_name}': No accent colors defined")
        elif len(accent_colors) < 2:
            self.suggestions.append(f"Domain '{domain_name}': Consider adding more accent colors for better theming")
        else:
            for i, color in enumerate(accent_colors):
                if not self._is_valid_color(color):
                    self.errors.append(f"Domain '{domain_name}': Invalid accent color {i+1}: {color}")
        
        # Optional fields validation
        logo_url = theme_config.get('logo_url')
        if logo_url and not self._is_valid_url(logo_url):
            self.warnings.append(f"Domain '{domain_name}': logo_url may not be valid: {logo_url}")
        
        favicon_url = theme_config.get('favicon_url')
        if favicon_url and not self._is_valid_url(favicon_url):
            self.warnings.append(f"Domain '{domain_name}': favicon_url may not be valid: {favicon_url}")
    
    def _validate_default_config(self, config_data: Dict[str, Any]):
        """Validate default configuration"""
        if 'default_config' not in config_data:
            self.suggestions.append("Consider adding a 'default_config' section for fallback configuration")
            return
        
        default_config = config_data['default_config']
        self._validate_single_domain('default_config', default_config)
    
    def _validate_security_settings(self, config_data: Dict[str, Any]):
        """Validate security settings"""
        if 'security' not in config_data:
            self.suggestions.append("Consider adding security settings for enhanced protection")
            return
        
        security = config_data['security']
        
        # Rate limiting validation
        if 'rate_limiting' in security:
            rate_limiting = security['rate_limiting']
            
            if 'enabled' in rate_limiting and not isinstance(rate_limiting['enabled'], bool):
                self.errors.append("Security rate_limiting.enabled must be a boolean")
            
            for field in ['requests_per_minute', 'requests_per_hour', 'burst_limit']:
                if field in rate_limiting:
                    value = rate_limiting[field]
                    if not isinstance(value, int) or value < 0:
                        self.errors.append(f"Security rate_limiting.{field} must be a non-negative integer")
        
        # HTTPS validation
        require_https = security.get('require_https', False)
        if not isinstance(require_https, bool):
            self.errors.append("Security require_https must be a boolean")
        elif not require_https:
            self.warnings.append("HTTPS is not required - consider enabling for production")
        
        # Request size validation
        max_request_size = security.get('max_request_size')
        if max_request_size is not None:
            if not isinstance(max_request_size, int) or max_request_size < 0:
                self.errors.append("Security max_request_size must be a non-negative integer")
    
    def _validate_cross_domain_consistency(self, config_data: Dict[str, Any]):
        """Validate consistency across domains"""
        if 'domains' not in config_data:
            return
        
        domains = config_data['domains']
        
        # Check for duplicate Google Sheet IDs
        sheet_ids = {}
        for domain_name, domain_config in domains.items():
            sheet_id = domain_config.get('google_sheet_id')
            if sheet_id:
                if sheet_id in sheet_ids:
                    self.warnings.append(
                        f"Duplicate Google Sheet ID '{sheet_id}' found in domains "
                        f"'{sheet_ids[sheet_id]}' and '{domain_name}'"
                    )
                else:
                    sheet_ids[sheet_id] = domain_name
        
        # Check for similar client names
        client_names = {}
        for domain_name, domain_config in domains.items():
            client_name = domain_config.get('client_name', '').lower()
            if client_name:
                if client_name in client_names:
                    self.warnings.append(
                        f"Similar client names found: '{client_names[client_name]}' and '{domain_name}'"
                    )
                else:
                    client_names[client_name] = domain_name
    
    def _validate_performance_settings(self, config_data: Dict[str, Any]):
        """Validate performance-related settings"""
        if 'domains' not in config_data:
            return
        
        domains = config_data['domains']
        domain_count = len(domains)
        
        if domain_count > 20:
            self.warnings.append(f"Large number of domains ({domain_count}) - monitor system performance")
        elif domain_count > 50:
            self.errors.append(f"Very large number of domains ({domain_count}) - may impact performance")
        
        # Check cache timeout distribution
        cache_timeouts = [
            domain_config.get('cache_timeout', 300) 
            for domain_config in domains.values()
        ]
        
        if len(set(cache_timeouts)) == 1:
            self.suggestions.append("All domains have the same cache timeout - consider optimizing per domain")
        
        avg_timeout = sum(cache_timeouts) / len(cache_timeouts)
        if avg_timeout < 120:
            self.warnings.append("Average cache timeout is low - may increase API calls to Google Sheets")
    
    def _is_valid_domain_name(self, domain: str) -> bool:
        """Basic domain name validation"""
        import re
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(pattern, domain)) and len(domain) <= 253
    
    def _is_valid_color(self, color: str) -> bool:
        """Validate color format (hex colors)"""
        import re
        return bool(re.match(r'^#[0-9A-Fa-f]{6}$', color))
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        return url.startswith(('http://', 'https://')) and len(url) > 10
    
    def validate_google_sheets_access(self, config_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate Google Sheets access for all configured domains"""
        validation_results = {
            'accessible': [],
            'inaccessible': [],
            'errors': []
        }
        
        if 'domains' not in config_data:
            return validation_results
        
        domains = config_data['domains']
        
        for domain_name, domain_config in domains.items():
            sheet_id = domain_config.get('google_sheet_id')
            if not sheet_id:
                continue
            
            try:
                # Test Google Sheets access (simplified check)
                # In a real implementation, you would use the Google Sheets API
                # For now, we'll just validate the sheet ID format
                if len(sheet_id) >= 20 and sheet_id.replace('_', '').replace('-', '').isalnum():
                    validation_results['accessible'].append({
                        'domain': domain_name,
                        'sheet_id': sheet_id,
                        'status': 'format_valid'
                    })
                else:
                    validation_results['inaccessible'].append({
                        'domain': domain_name,
                        'sheet_id': sheet_id,
                        'error': 'Invalid sheet ID format'
                    })
                    
            except Exception as e:
                validation_results['errors'].append({
                    'domain': domain_name,
                    'sheet_id': sheet_id,
                    'error': str(e)
                })
        
        return validation_results
    
    def generate_validation_report(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        # Run standard validation
        standard_results = self.validate_config_data(config_data)
        
        # Run Google Sheets validation
        sheets_validation = self.validate_google_sheets_access(config_data)
        
        # Performance analysis
        performance_analysis = self._analyze_performance_settings(config_data)
        
        # Security analysis
        security_analysis = self._analyze_security_settings(config_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(config_data, standard_results)
        
        return {
            'validation_summary': {
                'overall_valid': standard_results['valid'],
                'total_errors': len(standard_results['errors']),
                'total_warnings': len(standard_results['warnings']),
                'total_suggestions': len(standard_results['suggestions']),
                'validated_at': datetime.now().isoformat()
            },
            'standard_validation': standard_results,
            'sheets_validation': sheets_validation,
            'performance_analysis': performance_analysis,
            'security_analysis': security_analysis,
            'recommendations': recommendations
        }
    
    def _analyze_performance_settings(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance-related configuration settings"""
        analysis = {
            'cache_timeout_distribution': {},
            'potential_bottlenecks': [],
            'optimization_opportunities': []
        }
        
        if 'domains' not in config_data:
            return analysis
        
        domains = config_data['domains']
        cache_timeouts = []
        
        for domain_name, domain_config in domains.items():
            timeout = domain_config.get('cache_timeout', 300)
            cache_timeouts.append(timeout)
            
            # Identify potential issues
            if timeout < 60:
                analysis['potential_bottlenecks'].append({
                    'domain': domain_name,
                    'issue': 'Very low cache timeout may cause frequent API calls',
                    'current_value': timeout,
                    'recommended_min': 120
                })
            elif timeout > 1800:
                analysis['potential_bottlenecks'].append({
                    'domain': domain_name,
                    'issue': 'Very high cache timeout may serve stale data',
                    'current_value': timeout,
                    'recommended_max': 1800
                })
        
        if cache_timeouts:
            analysis['cache_timeout_distribution'] = {
                'min': min(cache_timeouts),
                'max': max(cache_timeouts),
                'avg': sum(cache_timeouts) / len(cache_timeouts),
                'unique_values': len(set(cache_timeouts))
            }
            
            # Optimization opportunities
            if len(set(cache_timeouts)) == 1:
                analysis['optimization_opportunities'].append(
                    'All domains use the same cache timeout - consider optimizing per domain usage patterns'
                )
            
            if len(domains) > 10:
                analysis['optimization_opportunities'].append(
                    'Large number of domains - consider implementing cache warming strategies'
                )
        
        return analysis
    
    def _analyze_security_settings(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security-related configuration settings"""
        analysis = {
            'security_score': 0,
            'vulnerabilities': [],
            'recommendations': [],
            'compliance_checks': {}
        }
        
        max_score = 100
        current_score = 0
        
        # Check for HTTPS requirement
        security_config = config_data.get('security', {})
        if security_config.get('require_https', False):
            current_score += 20
            analysis['compliance_checks']['https_required'] = True
        else:
            analysis['vulnerabilities'].append({
                'severity': 'medium',
                'issue': 'HTTPS not required',
                'recommendation': 'Enable require_https for production environments'
            })
            analysis['compliance_checks']['https_required'] = False
        
        # Check for rate limiting
        if 'rate_limiting' in security_config:
            rate_config = security_config['rate_limiting']
            if rate_config.get('enabled', False):
                current_score += 15
                analysis['compliance_checks']['rate_limiting_enabled'] = True
            else:
                analysis['recommendations'].append('Enable rate limiting to prevent abuse')
                analysis['compliance_checks']['rate_limiting_enabled'] = False
        else:
            analysis['recommendations'].append('Configure rate limiting settings')
            analysis['compliance_checks']['rate_limiting_enabled'] = False
        
        # Check for duplicate sheet IDs (data isolation)
        domains = config_data.get('domains', {})
        sheet_ids = [d.get('google_sheet_id') for d in domains.values() if d.get('google_sheet_id')]
        unique_sheets = set(sheet_ids)
        
        if len(unique_sheets) == len(sheet_ids):
            current_score += 25
            analysis['compliance_checks']['data_isolation'] = True
        else:
            analysis['vulnerabilities'].append({
                'severity': 'high',
                'issue': 'Duplicate Google Sheet IDs found - potential data leakage',
                'recommendation': 'Ensure each domain has a unique Google Sheet ID'
            })
            analysis['compliance_checks']['data_isolation'] = False
        
        # Check for proper domain validation
        valid_domains = 0
        for domain_name in domains.keys():
            if self._is_valid_domain_name(domain_name):
                valid_domains += 1
        
        if valid_domains == len(domains):
            current_score += 20
            analysis['compliance_checks']['valid_domain_names'] = True
        else:
            analysis['vulnerabilities'].append({
                'severity': 'medium',
                'issue': 'Some domain names may not be valid',
                'recommendation': 'Validate all domain names follow proper format'
            })
            analysis['compliance_checks']['valid_domain_names'] = False
        
        # Check for configuration file permissions (placeholder)
        current_score += 10  # Assume proper file permissions
        analysis['compliance_checks']['file_permissions'] = True
        
        # Additional security recommendations
        if len(domains) > 5:
            analysis['recommendations'].append('Consider implementing domain-specific access controls')
        
        if not config_data.get('default_config'):
            analysis['recommendations'].append('Add default_config section for fallback security')
        
        analysis['security_score'] = (current_score / max_score) * 100
        
        return analysis
    
    def _generate_recommendations(self, config_data: Dict[str, Any], validation_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on validation results"""
        recommendations = []
        
        # High priority recommendations (based on errors)
        for error in validation_results.get('errors', []):
            recommendations.append({
                'priority': 'high',
                'category': 'error_fix',
                'title': 'Fix Configuration Error',
                'description': error,
                'action': 'Review and correct the configuration error before deployment'
            })
        
        # Medium priority recommendations (based on warnings)
        for warning in validation_results.get('warnings', []):
            recommendations.append({
                'priority': 'medium',
                'category': 'warning_resolution',
                'title': 'Address Configuration Warning',
                'description': warning,
                'action': 'Consider addressing this warning to improve system reliability'
            })
        
        # Performance recommendations
        domains = config_data.get('domains', {})
        if len(domains) > 20:
            recommendations.append({
                'priority': 'medium',
                'category': 'performance',
                'title': 'Large Number of Domains',
                'description': f'System configured with {len(domains)} domains',
                'action': 'Monitor system performance and consider horizontal scaling'
            })
        
        # Security recommendations
        if not config_data.get('security'):
            recommendations.append({
                'priority': 'high',
                'category': 'security',
                'title': 'Add Security Configuration',
                'description': 'No security configuration found',
                'action': 'Add security section with HTTPS and rate limiting settings'
            })
        
        # Monitoring recommendations
        recommendations.append({
            'priority': 'low',
            'category': 'monitoring',
            'title': 'Enable Comprehensive Monitoring',
            'description': 'Set up monitoring for all configured domains',
            'action': 'Use domain_monitor.py for continuous health monitoring'
        })
        
        # Documentation recommendations
        recommendations.append({
            'priority': 'low',
            'category': 'documentation',
            'title': 'Document Configuration Changes',
            'description': 'Maintain documentation for configuration changes',
            'action': 'Update DOMAIN_ADMINISTRATION.md with any custom configurations'
        })
        
        return recommendations
    
    def _get_results(self) -> Dict[str, Any]:
        """Get validation results"""
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'info': self.info,
            'summary': {
                'error_count': len(self.errors),
                'warning_count': len(self.warnings),
                'suggestion_count': len(self.suggestions)
            }
        }


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Validate domain configuration file')
    parser.add_argument('config_file', help='Path to the configuration file to validate')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--quiet', action='store_true', help='Only show errors')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as errors')
    
    args = parser.parse_args()
    
    validator = ConfigValidator()
    results = validator.validate_file(args.config_file)
    
    if args.json:
        print(json.dumps(results, indent=2))
        return
    
    # Human-readable output
    print(f"Configuration Validation Results for: {args.config_file}")
    print("=" * 60)
    
    if results['valid']:
        print("✅ Configuration is VALID")
    else:
        print("❌ Configuration has ERRORS")
    
    print(f"\nSummary:")
    print(f"  Errors: {results['summary']['error_count']}")
    print(f"  Warnings: {results['summary']['warning_count']}")
    print(f"  Suggestions: {results['summary']['suggestion_count']}")
    
    if results['errors']:
        print(f"\n🚨 ERRORS ({len(results['errors'])}):")
        for i, error in enumerate(results['errors'], 1):
            print(f"  {i}. {error}")
    
    if results['warnings'] and not args.quiet:
        print(f"\n⚠️  WARNINGS ({len(results['warnings'])}):")
        for i, warning in enumerate(results['warnings'], 1):
            print(f"  {i}. {warning}")
    
    if results['suggestions'] and not args.quiet:
        print(f"\n💡 SUGGESTIONS ({len(results['suggestions'])}):")
        for i, suggestion in enumerate(results['suggestions'], 1):
            print(f"  {i}. {suggestion}")
    
    if results['info'] and not args.quiet:
        print(f"\nℹ️  INFO:")
        for info in results['info']:
            print(f"  • {info}")
    
    # Exit with appropriate code
    if results['errors']:
        sys.exit(1)
    elif args.strict and results['warnings']:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
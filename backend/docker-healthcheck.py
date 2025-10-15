#!/usr/bin/env python3
"""
Docker health check script for multi-domain dashboard backend.
This script performs comprehensive health checks including domain-specific validation.
"""

import os
import sys
import json
import requests
from datetime import datetime

def check_basic_health():
    """Check basic Flask application health"""
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Basic health check failed: {e}")
        return False

def check_domains_health():
    """Check multi-domain functionality health"""
    try:
        response = requests.get('http://localhost:5000/api/admin/domains/health', timeout=10)
        if response.status_code != 200:
            print(f"Domains health check failed with status: {response.status_code}")
            return False
        
        data = response.json()
        if not data.get('success', False):
            print("Domains health check returned unsuccessful response")
            return False
        
        health_summary = data.get('health_summary', {})
        total_domains = health_summary.get('total_domains', 0)
        healthy_domains = health_summary.get('healthy_domains', 0)
        
        # At least one domain should be healthy
        if total_domains == 0:
            print("No domains configured")
            return False
        
        if healthy_domains == 0:
            print("No healthy domains found")
            return False
        
        print(f"Health check passed: {healthy_domains}/{total_domains} domains healthy")
        return True
        
    except Exception as e:
        print(f"Domains health check failed: {e}")
        return False

def check_configuration():
    """Check if domain configuration is properly loaded"""
    try:
        domains_config_path = os.environ.get('DOMAINS_CONFIG_PATH', '/app/domains.json')
        
        if not os.path.exists(domains_config_path):
            print(f"Domain configuration file not found: {domains_config_path}")
            return False
        
        with open(domains_config_path, 'r') as f:
            config = json.load(f)
        
        if 'domains' not in config:
            print("Invalid domain configuration: missing 'domains' key")
            return False
        
        if len(config['domains']) == 0:
            print("No domains configured in configuration file")
            return False
        
        print(f"Configuration check passed: {len(config['domains'])} domains configured")
        return True
        
    except Exception as e:
        print(f"Configuration check failed: {e}")
        return False

def main():
    """Main health check function"""
    print(f"Starting health check at {datetime.now().isoformat()}")
    
    # Check if multi-domain mode is enabled
    multi_domain_mode = os.environ.get('MULTI_DOMAIN_MODE', 'false').lower() == 'true'
    
    if not multi_domain_mode:
        print("Multi-domain mode disabled, performing basic health check only")
        if check_basic_health():
            print("Health check passed")
            sys.exit(0)
        else:
            print("Health check failed")
            sys.exit(1)
    
    # Perform comprehensive health checks for multi-domain mode
    checks = [
        ("Configuration", check_configuration),
        ("Basic Health", check_basic_health),
        ("Domains Health", check_domains_health)
    ]
    
    failed_checks = []
    
    for check_name, check_func in checks:
        print(f"Running {check_name} check...")
        if not check_func():
            failed_checks.append(check_name)
            print(f"❌ {check_name} check failed")
        else:
            print(f"✅ {check_name} check passed")
    
    if failed_checks:
        print(f"Health check failed. Failed checks: {', '.join(failed_checks)}")
        sys.exit(1)
    else:
        print("All health checks passed")
        sys.exit(0)

if __name__ == "__main__":
    main()
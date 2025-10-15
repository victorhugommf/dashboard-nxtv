#!/usr/bin/env python3
"""
Domain Security Module
Implements security and validation layers for multi-domain dashboard
"""

import time
import json
import os
import stat
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import threading
import re
from flask import request, g

from domain_logger import get_domain_logger, LogCategory, LogLevel


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    enabled: bool = True


@dataclass
class SecurityConfig:
    """Security configuration for domains"""
    domain_whitelist: Set[str] = field(default_factory=set)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    require_https: bool = False
    allowed_origins: Set[str] = field(default_factory=set)
    block_suspicious_patterns: bool = True
    max_request_size: int = 1024 * 1024  # 1MB


class DomainWhitelistValidator:
    """Validates domains against a whitelist"""
    
    def __init__(self, whitelist: Optional[Set[str]] = None):
        """Initialize with optional whitelist"""
        self.whitelist = whitelist or set()
        self.logger = get_domain_logger()
        
        # Load whitelist from configuration if not provided
        if not self.whitelist:
            self._load_whitelist_from_config()
    
    def _load_whitelist_from_config(self):
        """Load whitelist from domains.json configuration"""
        try:
            config_path = Path("domains.json")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Extract domains from configuration
                domains = config_data.get('domains', {})
                self.whitelist = set(domains.keys())
                
                # Add any additional whitelisted domains from security config
                security_config = config_data.get('security', {})
                additional_domains = security_config.get('additional_whitelist', [])
                self.whitelist.update(additional_domains)
                
                self.logger.info(f"Loaded domain whitelist: {len(self.whitelist)} domains")
            else:
                self.logger.warning("No domains.json found, using empty whitelist")
                
        except Exception as e:
            self.logger.error(
                LogCategory.SECURITY,
                f"Failed to load domain whitelist: {str(e)}",
                details={'config_file': 'domains.json'}
            )
    
    def is_domain_allowed(self, domain: str) -> bool:
        """Check if domain is in whitelist"""
        if not domain:
            return False
        
        # Normalize domain (lowercase, strip)
        normalized_domain = domain.lower().strip()
        
        # Normalize whitelist for comparison (convert to lowercase)
        normalized_whitelist = {d.lower().strip() for d in self.whitelist}
        
        # Check exact match
        if normalized_domain in normalized_whitelist:
            return True
        
        # Check wildcard patterns (e.g., *.example.com)
        for whitelisted_domain in normalized_whitelist:
            if whitelisted_domain.startswith('*.'):
                pattern = whitelisted_domain[2:]  # Remove *.
                if normalized_domain.endswith('.' + pattern) or normalized_domain == pattern:
                    return True
        
        return False
    
    def validate_domain(self, domain: str) -> Tuple[bool, Optional[str]]:
        """Validate domain and return result with error message"""
        if not domain:
            error_msg = "Domain is required"
            self.logger.log_security_event(
                "domain_validation_failed",
                details={'domain': domain, 'reason': error_msg}
            )
            return False, error_msg
        
        if not self.is_domain_allowed(domain):
            error_msg = f"Domain '{domain}' is not whitelisted"
            self.logger.log_security_event(
                "domain_not_whitelisted",
                details={'domain': domain, 'whitelist_size': len(self.whitelist)}
            )
            return False, error_msg
        
        # Additional domain format validation
        if not self._is_valid_domain_format(domain):
            error_msg = f"Invalid domain format: {domain}"
            self.logger.log_security_event(
                "invalid_domain_format",
                details={'domain': domain}
            )
            return False, error_msg
        
        return True, None
    
    def _is_valid_domain_format(self, domain: str) -> bool:
        """Validate domain format"""
        if not domain or len(domain) > 253:
            return False
        
        # Check for valid characters (letters, numbers, dots, hyphens)
        domain_pattern = r'^[a-zA-Z0-9.-]+$'
        if not re.match(domain_pattern, domain):
            return False
        
        # Check that it doesn't start or end with dot or hyphen
        if domain.startswith('.') or domain.endswith('.'):
            return False
        if domain.startswith('-') or domain.endswith('-'):
            return False
        
        # Check for consecutive dots or hyphens
        if '..' in domain or '--' in domain:
            return False
        
        # Check each label (part between dots)
        labels = domain.split('.')
        for label in labels:
            if not label or len(label) > 63:
                return False
            if label.startswith('-') or label.endswith('-'):
                return False
        
        return True
    
    def add_domain(self, domain: str):
        """Add domain to whitelist"""
        normalized_domain = domain.lower().strip()
        self.whitelist.add(normalized_domain)
        
        self.logger.log_security_event(
            "domain_added_to_whitelist",
            details={'domain': normalized_domain, 'whitelist_size': len(self.whitelist)}
        )
    
    def remove_domain(self, domain: str):
        """Remove domain from whitelist"""
        normalized_domain = domain.lower().strip()
        if normalized_domain in self.whitelist:
            self.whitelist.remove(normalized_domain)
            
            self.logger.log_security_event(
                "domain_removed_from_whitelist",
                details={'domain': normalized_domain, 'whitelist_size': len(self.whitelist)}
            )
    
    def get_whitelist(self) -> Set[str]:
        """Get current whitelist"""
        return self.whitelist.copy()


class RateLimiter:
    """Rate limiter with per-domain tracking"""
    
    def __init__(self, config: RateLimitConfig):
        """Initialize rate limiter with configuration"""
        self.config = config
        self.logger = get_domain_logger()
        
        # Track requests per domain
        self.domain_requests: Dict[str, deque] = defaultdict(deque)
        self.domain_hourly_requests: Dict[str, deque] = defaultdict(deque)
        self.domain_burst_requests: Dict[str, deque] = defaultdict(deque)
        
        # Thread lock for thread safety
        self.lock = threading.Lock()
    
    def is_allowed(self, domain: str, client_ip: str = None) -> Tuple[bool, Optional[str]]:
        """Check if request is allowed for domain"""
        if not self.config.enabled:
            return True, None
        
        current_time = time.time()
        
        with self.lock:
            # Clean old requests
            self._clean_old_requests(domain, current_time)
            
            # Check burst limit (last 10 seconds)
            burst_requests = self.domain_burst_requests[domain]
            burst_window = current_time - 10  # 10 seconds
            
            # Count recent burst requests
            recent_burst = sum(1 for req_time in burst_requests if req_time > burst_window)
            
            if recent_burst >= self.config.burst_limit:
                error_msg = f"Burst limit exceeded for domain {domain}"
                self.logger.log_security_event(
                    "rate_limit_burst_exceeded",
                    details={
                        'domain': domain,
                        'client_ip': client_ip,
                        'burst_count': recent_burst,
                        'burst_limit': self.config.burst_limit
                    }
                )
                return False, error_msg
            
            # Check per-minute limit
            minute_requests = self.domain_requests[domain]
            minute_window = current_time - 60  # 1 minute
            
            # Count recent minute requests
            recent_minute = sum(1 for req_time in minute_requests if req_time > minute_window)
            
            if recent_minute >= self.config.requests_per_minute:
                error_msg = f"Per-minute rate limit exceeded for domain {domain}"
                self.logger.log_security_event(
                    "rate_limit_minute_exceeded",
                    details={
                        'domain': domain,
                        'client_ip': client_ip,
                        'minute_count': recent_minute,
                        'minute_limit': self.config.requests_per_minute
                    }
                )
                return False, error_msg
            
            # Check per-hour limit
            hourly_requests = self.domain_hourly_requests[domain]
            hour_window = current_time - 3600  # 1 hour
            
            # Count recent hourly requests
            recent_hour = sum(1 for req_time in hourly_requests if req_time > hour_window)
            
            if recent_hour >= self.config.requests_per_hour:
                error_msg = f"Per-hour rate limit exceeded for domain {domain}"
                self.logger.log_security_event(
                    "rate_limit_hour_exceeded",
                    details={
                        'domain': domain,
                        'client_ip': client_ip,
                        'hour_count': recent_hour,
                        'hour_limit': self.config.requests_per_hour
                    }
                )
                return False, error_msg
            
            # Record this request
            burst_requests.append(current_time)
            minute_requests.append(current_time)
            hourly_requests.append(current_time)
            
            return True, None
    
    def _clean_old_requests(self, domain: str, current_time: float):
        """Clean old request records to prevent memory leaks"""
        # Clean burst requests (older than 10 seconds)
        burst_requests = self.domain_burst_requests[domain]
        burst_cutoff = current_time - 10
        while burst_requests and burst_requests[0] <= burst_cutoff:
            burst_requests.popleft()
        
        # Clean minute requests (older than 1 minute)
        minute_requests = self.domain_requests[domain]
        minute_cutoff = current_time - 60
        while minute_requests and minute_requests[0] <= minute_cutoff:
            minute_requests.popleft()
        
        # Clean hourly requests (older than 1 hour)
        hourly_requests = self.domain_hourly_requests[domain]
        hour_cutoff = current_time - 3600
        while hourly_requests and hourly_requests[0] <= hour_cutoff:
            hourly_requests.popleft()
    
    def get_stats(self, domain: str) -> Dict[str, int]:
        """Get rate limiting statistics for domain"""
        current_time = time.time()
        
        with self.lock:
            self._clean_old_requests(domain, current_time)
            
            return {
                'burst_requests': len(self.domain_burst_requests[domain]),
                'minute_requests': len(self.domain_requests[domain]),
                'hourly_requests': len(self.domain_hourly_requests[domain]),
                'burst_limit': self.config.burst_limit,
                'minute_limit': self.config.requests_per_minute,
                'hour_limit': self.config.requests_per_hour
            }
    
    def reset_domain_limits(self, domain: str):
        """Reset rate limits for a specific domain"""
        with self.lock:
            self.domain_requests[domain].clear()
            self.domain_hourly_requests[domain].clear()
            self.domain_burst_requests[domain].clear()
            
            self.logger.log_security_event(
                "rate_limit_reset",
                details={'domain': domain}
            )


class ConfigurationProtector:
    """Protects configuration files from unauthorized access"""
    
    def __init__(self, config_file_path: str = "domains.json"):
        """Initialize with configuration file path"""
        self.config_file_path = Path(config_file_path)
        self.logger = get_domain_logger()
        
        # Ensure proper file permissions
        self._secure_config_file()
    
    def _secure_config_file(self):
        """Set secure permissions on configuration file"""
        try:
            from domain_logger import LogCategory
            
            if self.config_file_path.exists():
                # Set file permissions to read/write for owner only (600)
                os.chmod(self.config_file_path, stat.S_IRUSR | stat.S_IWUSR)
                
                if hasattr(self.logger, 'info') and hasattr(self.logger.info, '__code__') and self.logger.info.__code__.co_argcount > 2:
                    # Domain logger with category parameter
                    self.logger.info(LogCategory.SECURITY, f"Secured configuration file: {self.config_file_path}")
                else:
                    # Standard logger
                    self.logger.info(f"Secured configuration file: {self.config_file_path}")
            else:
                if hasattr(self.logger, 'warning') and hasattr(self.logger.warning, '__code__') and self.logger.warning.__code__.co_argcount > 2:
                    # Domain logger with category parameter
                    self.logger.warning(LogCategory.SECURITY, f"Configuration file not found: {self.config_file_path}")
                else:
                    # Standard logger
                    self.logger.warning(f"Configuration file not found: {self.config_file_path}")
                
        except Exception as e:
            try:
                from domain_logger import LogCategory
                self.logger.error(
                    LogCategory.SECURITY,
                    f"Failed to secure configuration file: {str(e)}",
                    details={'config_file': str(self.config_file_path)}
                )
            except:
                # Fallback to standard logging
                import logging
                logging.error(f"Failed to secure configuration file: {str(e)}")
    
    def validate_file_access(self) -> Tuple[bool, List[str]]:
        """Validate configuration file access and permissions"""
        errors = []
        
        try:
            # Check if file exists
            if not self.config_file_path.exists():
                errors.append(f"Configuration file does not exist: {self.config_file_path}")
                return False, errors
            
            # Check file permissions
            file_stat = self.config_file_path.stat()
            file_mode = file_stat.st_mode
            
            # Check if file is readable by owner
            if not (file_mode & stat.S_IRUSR):
                errors.append("Configuration file is not readable by owner")
            
            # Check if file is writable by owner
            if not (file_mode & stat.S_IWUSR):
                errors.append("Configuration file is not writable by owner")
            
            # Check if file is accessible by group (should not be)
            if file_mode & (stat.S_IRGRP | stat.S_IWGRP):
                errors.append("Configuration file is accessible by group (security risk)")
            
            # Check if file is accessible by others (should not be)
            if file_mode & (stat.S_IROTH | stat.S_IWOTH):
                errors.append("Configuration file is accessible by others (security risk)")
            
            # Check file size (prevent extremely large files)
            file_size = file_stat.st_size
            max_size = 10 * 1024 * 1024  # 10MB
            if file_size > max_size:
                errors.append(f"Configuration file is too large: {file_size} bytes (max: {max_size})")
            
            # Log validation results
            if errors:
                self.logger.log_security_event(
                    "config_file_validation_failed",
                    details={
                        'config_file': str(self.config_file_path),
                        'errors': errors,
                        'file_mode': oct(file_mode),
                        'file_size': file_size
                    }
                )
            else:
                if hasattr(self.logger, 'info') and hasattr(self.logger.info, '__code__') and self.logger.info.__code__.co_argcount > 2:
                    # Domain logger with category parameter
                    from domain_logger import LogCategory
                    self.logger.info(LogCategory.SECURITY, f"Configuration file validation passed: {self.config_file_path}")
                else:
                    # Standard logger
                    self.logger.info(f"Configuration file validation passed: {self.config_file_path}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            error_msg = f"Failed to validate configuration file access: {str(e)}"
            errors.append(error_msg)
            
            self.logger.error(
                LogCategory.SECURITY,
                error_msg,
                details={'config_file': str(self.config_file_path)}
            )
            
            return False, errors
    
    def create_backup(self) -> Optional[str]:
        """Create a backup of the configuration file"""
        try:
            if not self.config_file_path.exists():
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.config_file_path.parent / f"{self.config_file_path.stem}_backup_{timestamp}.json"
            
            # Copy file content
            with open(self.config_file_path, 'r', encoding='utf-8') as src:
                content = src.read()
            
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(content)
            
            # Set secure permissions on backup
            os.chmod(backup_path, stat.S_IRUSR | stat.S_IWUSR)
            
            self.logger.log_security_event(
                "config_backup_created",
                details={
                    'original_file': str(self.config_file_path),
                    'backup_file': str(backup_path)
                }
            )
            
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(
                LogCategory.SECURITY,
                f"Failed to create configuration backup: {str(e)}",
                details={'config_file': str(self.config_file_path)}
            )
            return None


class DomainSecurityManager:
    """Main security manager that coordinates all security components"""
    
    def __init__(self, config: SecurityConfig = None):
        """Initialize security manager"""
        self.config = config or SecurityConfig()
        self.logger = get_domain_logger()
        
        # Initialize security components
        self.whitelist_validator = DomainWhitelistValidator(self.config.domain_whitelist)
        self.rate_limiter = RateLimiter(self.config.rate_limit)
        self.config_protector = ConfigurationProtector()
        
        # Initialize security
        self._initialize_security()
    
    def _initialize_security(self):
        """Initialize security measures"""
        # Validate configuration file access
        is_valid, errors = self.config_protector.validate_file_access()
        if not is_valid:
            self.logger.error(
                LogCategory.SECURITY,
                f"Configuration file security validation failed: {'; '.join(errors)}",
                details={'errors': errors}
            )
        
        # Log security initialization
        self.logger.log_security_event(
            "security_manager_initialized",
            details={
                'whitelist_domains': len(self.whitelist_validator.get_whitelist()),
                'rate_limiting_enabled': self.config.rate_limit.enabled,
                'require_https': self.config.require_https
            }
        )
    
    def validate_request(self, domain: str, client_ip: str = None) -> Tuple[bool, Optional[str]]:
        """Validate incoming request against all security measures"""
        # Validate domain whitelist
        is_valid, error_msg = self.whitelist_validator.validate_domain(domain)
        if not is_valid:
            return False, error_msg
        
        # Check rate limits
        is_allowed, error_msg = self.rate_limiter.is_allowed(domain, client_ip)
        if not is_allowed:
            return False, error_msg
        
        # Additional security checks
        try:
            # Import request here to avoid circular imports and context issues
            from flask import request as flask_request
            
            if self.config.require_https and flask_request and not flask_request.is_secure:
                error_msg = "HTTPS is required"
                self.logger.log_security_event(
                    "https_required_violation",
                    details={'domain': domain, 'client_ip': client_ip}
                )
                return False, error_msg
            
            # Check request size
            if flask_request and hasattr(flask_request, 'content_length') and flask_request.content_length:
                if flask_request.content_length > self.config.max_request_size:
                    error_msg = f"Request size too large: {flask_request.content_length} bytes"
                    self.logger.log_security_event(
                        "request_size_exceeded",
                        details={
                            'domain': domain,
                            'client_ip': client_ip,
                            'request_size': flask_request.content_length,
                            'max_size': self.config.max_request_size
                        }
                    )
                    return False, error_msg
        except RuntimeError:
            # No request context available (e.g., during testing)
            # Skip request-specific validations
            pass
        
        return True, None
    
    def get_security_stats(self, domain: str = None) -> Dict[str, any]:
        """Get security statistics"""
        stats = {
            'whitelist_size': len(self.whitelist_validator.get_whitelist()),
            'rate_limiting_enabled': self.config.rate_limit.enabled,
            'require_https': self.config.require_https,
            'max_request_size': self.config.max_request_size
        }
        
        if domain:
            stats['rate_limit_stats'] = self.rate_limiter.get_stats(domain)
        
        return stats
    
    def add_domain_to_whitelist(self, domain: str):
        """Add domain to whitelist"""
        self.whitelist_validator.add_domain(domain)
    
    def remove_domain_from_whitelist(self, domain: str):
        """Remove domain from whitelist"""
        self.whitelist_validator.remove_domain(domain)
    
    def reset_rate_limits(self, domain: str):
        """Reset rate limits for domain"""
        self.rate_limiter.reset_domain_limits(domain)


# Global security manager instance
_security_manager = None


def get_security_manager() -> DomainSecurityManager:
    """Get global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = DomainSecurityManager()
    return _security_manager


def init_domain_security(app, config: SecurityConfig = None):
    """Initialize domain security for Flask app"""
    global _security_manager
    _security_manager = DomainSecurityManager(config)
    
    # Add before_request handler for security validation
    @app.before_request
    def validate_request_security():
        """Validate request security before processing"""
        # Skip security validation for certain paths (health checks, etc.)
        if request.path in ['/health', '/ping']:
            return
        
        # Get domain from request
        domain = getattr(g, 'domain', None)
        if not domain:
            # Try to extract from Host header for early validation
            host_header = request.headers.get('Host')
            if host_header:
                domain = host_header.split(':')[0].lower().strip()
        
        if domain:
            client_ip = request.remote_addr
            is_valid, error_msg = _security_manager.validate_request(domain, client_ip)
            
            if not is_valid:
                from flask import jsonify
                return jsonify({
                    'error': 'Security validation failed',
                    'message': error_msg,
                    'domain': domain,
                    'timestamp': datetime.now().isoformat()
                }), 403
    
    return _security_manager
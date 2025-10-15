#!/usr/bin/env python3
"""
Domain Resolution Middleware
Handles domain resolution and context injection for multi-domain support
"""

from flask import Flask, request, g
from werkzeug.wrappers import Request, Response
from typing import Optional, Callable, Any
import logging
from urllib.parse import urlparse

from domain_config import DomainConfigManager, DomainConfig
from domain_cache import get_cache_manager as get_global_cache_manager, DomainCacheManager
from domain_logger import get_domain_logger, LogCategory


class DomainContext:
    """Context object to hold domain-specific information"""
    
    def __init__(self, domain: str, config: DomainConfig, cache_manager: DomainCacheManager):
        self.domain = domain
        self.config = config
        self.cache_manager = cache_manager
        self.analyzer = None  # Will be set by MultiDomainDataAnalyzer
        self.theme_manager = None  # Will be set by ThemeManager


class DomainResolverMiddleware:
    """Middleware to resolve domain and inject domain-specific configuration"""
    
    def __init__(self, app: Flask, config_manager: DomainConfigManager):
        """Initialize middleware with Flask app and domain config manager"""
        self.app = app
        self.config_manager = config_manager
        self.cache_manager = get_global_cache_manager()  # Get global cache manager instance
        self.logger = logging.getLogger(__name__)
        self.domain_logger = get_domain_logger()
        
        # Register middleware with Flask
        app.wsgi_app = self._wrap_wsgi_app(app.wsgi_app)
        
        # Add before_request handler to inject domain context
        app.before_request(self._inject_domain_context)
    
    def _wrap_wsgi_app(self, wsgi_app: Callable) -> Callable:
        """Wrap WSGI application to handle domain resolution"""
        def middleware(environ, start_response):
            # Create request object to extract domain
            request_obj = Request(environ)
            
            try:
                # Resolve domain from request
                domain = self.resolve_domain(request_obj)
                
                # Validate domain and get configuration
                domain_config = self.config_manager.get_config_by_domain(domain)
                
                # Store domain info in environ for Flask to access
                environ['DOMAIN_NAME'] = domain
                environ['DOMAIN_CONFIG'] = domain_config
                
                self.logger.info(f"Resolved domain: {domain} -> {domain_config.client_name}")
                
                # Log domain resolution success
                self.domain_logger.log_domain_resolution(
                    domain=domain,
                    success=True,
                    details={
                        'client_name': domain_config.client_name,
                        'google_sheet_id': domain_config.google_sheet_id,
                        'cache_timeout': domain_config.cache_timeout
                    }
                )
                
            except ValueError as e:
                # Domain not found or invalid
                self.logger.warning(f"Domain resolution failed: {str(e)}")
                
                # Log domain resolution failure
                self.domain_logger.log_domain_resolution(
                    domain=domain if 'domain' in locals() else 'unknown',
                    success=False,
                    details={
                        'error': str(e),
                        'host_header': request_obj.headers.get('Host')
                    }
                )
                
                # Return 404 for unknown domains
                response = Response(
                    response=f"Domain not configured: {str(e)}",
                    status=404,
                    headers={'Content-Type': 'text/plain'}
                )
                return response(environ, start_response)
            
            except Exception as e:
                # Unexpected error
                self.logger.error(f"Unexpected error in domain resolution: {str(e)}")
                
                # Log unexpected error
                self.domain_logger.error(
                    LogCategory.DOMAIN_RESOLUTION,
                    f"Unexpected error in domain resolution: {str(e)}",
                    details={
                        'host_header': request_obj.headers.get('Host'),
                        'error_type': type(e).__name__
                    }
                )
                
                # Return 500 for server errors
                response = Response(
                    response=f"Internal server error: {str(e)}",
                    status=500,
                    headers={'Content-Type': 'text/plain'}
                )
                return response(environ, start_response)
            
            # Continue with normal request processing
            return wsgi_app(environ, start_response)
        
        return middleware
    
    def resolve_domain(self, request_obj: Request) -> str:
        """Extract domain from HTTP request headers or query parameters"""
        # Try to get domain from query parameter first (for CORS compatibility)
        domain_param = request_obj.args.get('domain')
        
        if domain_param:
            domain = domain_param.lower().strip()
        else:
            # Try to get domain from X-Domain header
            x_domain_header = request_obj.headers.get('X-Domain')
            
            if x_domain_header:
                domain = x_domain_header.lower().strip()
            else:
                # Fallback to Host header
                host_header = request_obj.headers.get('Host')
                
                if not host_header:
                    raise ValueError("No domain specified in query parameter, X-Domain header, or Host header")
                
                # Parse the host header to extract domain
                # Remove port number if present
                domain = host_header.split(':')[0].lower().strip()
        
        if not domain:
            raise ValueError("Invalid or empty domain")
        
        # Additional validation for domain format
        if not self._is_valid_domain_format(domain):
            raise ValueError(f"Invalid domain format: {domain}")
        
        return domain
    
    def _is_valid_domain_format(self, domain: str) -> bool:
        """Validate domain format (basic validation)"""
        # Basic domain validation
        if not domain or len(domain) > 253:
            return False
        
        # Check for valid characters (letters, numbers, dots, hyphens)
        import re
        domain_pattern = r'^[a-zA-Z0-9.-]+$'
        if not re.match(domain_pattern, domain):
            return False
        
        # Check that it doesn't start or end with dot or hyphen
        if domain.startswith('.') or domain.endswith('.'):
            return False
        if domain.startswith('-') or domain.endswith('-'):
            return False
        
        # Check for consecutive dots (invalid)
        if '..' in domain:
            return False
        
        # Check for consecutive hyphens at domain boundaries
        if '--' in domain:
            return False
        
        return True
    
    def _inject_domain_context(self):
        """Inject domain context into Flask's g object"""
        # Get domain info from environ (set by WSGI middleware)
        domain_name = request.environ.get('DOMAIN_NAME')
        domain_config = request.environ.get('DOMAIN_CONFIG')
        
        if domain_name and domain_config:
            # Create domain context and store in Flask's g
            g.domain_context = DomainContext(domain_name, domain_config, self.cache_manager)
            
            # Also store individual components for easier access
            g.domain = domain_name
            g.domain_config = domain_config
            g.cache_manager = self.cache_manager
            
            self.logger.debug(f"Injected domain context for: {domain_name}")
        else:
            # Handle cases where no domain context is available (e.g., testing, legacy mode)
            self.logger.debug("No domain context found in request environ - using defaults")
            g.domain_context = None
            g.domain = None
            g.domain_config = None
            g.cache_manager = self.cache_manager
    
    def get_domain_context(self) -> Optional[DomainContext]:
        """Get current domain context from Flask's g object"""
        return getattr(g, 'domain_context', None)
    
    def get_current_domain(self) -> Optional[str]:
        """Get current domain name"""
        return getattr(g, 'domain', None)
    
    def get_current_config(self) -> Optional[DomainConfig]:
        """Get current domain configuration"""
        return getattr(g, 'domain_config', None)


def create_domain_middleware(app: Flask, config_file_path: str = "domains.json") -> DomainResolverMiddleware:
    """Factory function to create and configure domain middleware"""
    # Create domain config manager
    config_manager = DomainConfigManager(config_file_path)
    
    # Create and return middleware
    middleware = DomainResolverMiddleware(app, config_manager)
    
    return middleware


# Utility functions for accessing domain context in Flask routes
def get_current_domain() -> Optional[str]:
    """Get current domain name from Flask context"""
    return getattr(g, 'domain', None)


def get_current_config() -> Optional[DomainConfig]:
    """Get current domain configuration from Flask context"""
    return getattr(g, 'domain_config', None)


def get_domain_context() -> Optional[DomainContext]:
    """Get current domain context from Flask context"""
    return getattr(g, 'domain_context', None)


def get_cache_manager() -> Optional[DomainCacheManager]:
    """Get current cache manager from Flask context"""
    return getattr(g, 'cache_manager', None)


def require_domain_context():
    """Decorator to ensure domain context is available (flexible for backward compatibility)"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            # Allow endpoints to work without domain context for backward compatibility
            # The endpoints themselves will handle fallback to legacy configuration
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
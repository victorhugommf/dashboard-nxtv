#!/usr/bin/env python3
"""
Domain-Aware Logging System
Provides comprehensive logging with domain identification and audit trails
"""

import logging
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from flask import g, request


class LogLevel(Enum):
    """Log levels for domain logging"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    AUDIT = "AUDIT"


class LogCategory(Enum):
    """Categories for domain logging"""
    DOMAIN_RESOLUTION = "domain_resolution"
    DATA_ACCESS = "data_access"
    CACHE_OPERATION = "cache_operation"
    CONFIGURATION = "configuration"
    THEME_OPERATION = "theme_operation"
    API_REQUEST = "api_request"
    ERROR_HANDLING = "error_handling"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class LogEntry:
    """Structured log entry with domain context"""
    timestamp: str
    level: str
    category: str
    domain: Optional[str]
    client_name: Optional[str]
    message: str
    details: Dict[str, Any]
    request_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    endpoint: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert log entry to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class DomainLogger:
    """Domain-aware logger with structured logging and audit trails"""
    
    def __init__(self, name: str = "domain_logger", log_dir: str = "logs"):
        """Initialize domain logger"""
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create separate loggers for different purposes
        self._setup_loggers()
        
        # Track configuration changes for audit
        self._audit_entries: List[LogEntry] = []
    
    def _setup_loggers(self):
        """Setup different loggers for various log types"""
        # Main application logger
        self.app_logger = logging.getLogger(f"{self.name}.app")
        self.app_logger.setLevel(logging.DEBUG)
        
        # Domain-specific logger
        self.domain_logger = logging.getLogger(f"{self.name}.domain")
        self.domain_logger.setLevel(logging.DEBUG)
        
        # Audit logger for configuration changes
        self.audit_logger = logging.getLogger(f"{self.name}.audit")
        self.audit_logger.setLevel(logging.INFO)
        
        # Error logger for domain-specific errors
        self.error_logger = logging.getLogger(f"{self.name}.error")
        self.error_logger.setLevel(logging.WARNING)
        
        # Setup file handlers
        self._setup_file_handlers()
        
        # Setup console handler for development
        self._setup_console_handler()
    
    def _setup_file_handlers(self):
        """Setup file handlers for different log types"""
        # Main application log
        app_handler = logging.FileHandler(
            self.log_dir / "application.log", 
            encoding='utf-8'
        )
        app_handler.setLevel(logging.DEBUG)
        app_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        app_handler.setFormatter(app_formatter)
        self.app_logger.addHandler(app_handler)
        
        # Domain-specific log
        domain_handler = logging.FileHandler(
            self.log_dir / "domain.log", 
            encoding='utf-8'
        )
        domain_handler.setLevel(logging.DEBUG)
        domain_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        domain_handler.setFormatter(domain_formatter)
        self.domain_logger.addHandler(domain_handler)
        
        # Audit log
        audit_handler = logging.FileHandler(
            self.log_dir / "audit.log", 
            encoding='utf-8'
        )
        audit_handler.setLevel(logging.INFO)
        audit_formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(message)s'
        )
        audit_handler.setFormatter(audit_formatter)
        self.audit_logger.addHandler(audit_handler)
        
        # Error log
        error_handler = logging.FileHandler(
            self.log_dir / "errors.log", 
            encoding='utf-8'
        )
        error_handler.setLevel(logging.WARNING)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        self.error_logger.addHandler(error_handler)
    
    def _setup_console_handler(self):
        """Setup console handler for development"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add console handler to main logger only
        self.app_logger.addHandler(console_handler)
    
    def _get_domain_context(self) -> tuple[Optional[str], Optional[str]]:
        """Get current domain context from Flask g object"""
        try:
            # Check if we're in a Flask context
            from flask import has_request_context
            if not has_request_context():
                return None, None
                
            domain = getattr(g, 'domain', None)
            domain_config = getattr(g, 'domain_config', None)
            client_name = domain_config.client_name if domain_config else None
            return domain, client_name
        except (RuntimeError, ImportError):
            # Outside Flask context or Flask not available
            return None, None
    
    def _get_request_context(self) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Get current request context"""
        try:
            # Check if we're in a Flask context
            from flask import has_request_context
            if not has_request_context():
                return None, None, None, None
                
            request_id = getattr(g, 'request_id', None)
            user_agent = request.headers.get('User-Agent') if request else None
            ip_address = request.remote_addr if request else None
            endpoint = request.endpoint if request else None
            return request_id, user_agent, ip_address, endpoint
        except (RuntimeError, ImportError):
            # Outside Flask context or Flask not available
            return None, None, None, None
    
    def _create_log_entry(
        self, 
        level: LogLevel, 
        category: LogCategory, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> LogEntry:
        """Create structured log entry with domain context"""
        domain, client_name = self._get_domain_context()
        request_id, user_agent, ip_address, endpoint = self._get_request_context()
        
        return LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.value,
            category=category.value,
            domain=domain,
            client_name=client_name,
            message=message,
            details=details or {},
            request_id=request_id,
            user_agent=user_agent,
            ip_address=ip_address,
            endpoint=endpoint
        )
    
    def log(
        self, 
        level: LogLevel, 
        category: LogCategory, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        """Log a message with domain context"""
        log_entry = self._create_log_entry(level, category, message, details)
        
        # Format message with domain context
        formatted_message = self._format_message(log_entry)
        
        # Log to appropriate logger based on level and category
        if level == LogLevel.AUDIT:
            self.audit_logger.info(formatted_message)
            self._audit_entries.append(log_entry)
        elif level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self.error_logger.error(formatted_message)
        elif category == LogCategory.DOMAIN_RESOLUTION:
            self.domain_logger.info(formatted_message)
        else:
            # Map log levels to standard logging levels
            log_level_map = {
                LogLevel.DEBUG: logging.DEBUG,
                LogLevel.INFO: logging.INFO,
                LogLevel.WARNING: logging.WARNING,
                LogLevel.ERROR: logging.ERROR,
                LogLevel.CRITICAL: logging.CRITICAL
            }
            
            self.app_logger.log(log_level_map[level], formatted_message)
        
        # Also write structured JSON log for analysis
        self._write_structured_log(log_entry)
    
    def _format_message(self, log_entry: LogEntry) -> str:
        """Format log message with domain context"""
        domain_info = ""
        if log_entry.domain:
            domain_info = f"[{log_entry.domain}]"
            if log_entry.client_name:
                domain_info += f"[{log_entry.client_name}]"
        
        category_info = f"[{log_entry.category}]"
        
        base_message = f"{domain_info}{category_info} {log_entry.message}"
        
        if log_entry.details:
            details_str = json.dumps(log_entry.details, ensure_ascii=False, default=str)
            base_message += f" - Details: {details_str}"
        
        return base_message
    
    def _write_structured_log(self, log_entry: LogEntry):
        """Write structured JSON log for analysis"""
        json_log_file = self.log_dir / "structured.jsonl"
        
        try:
            with open(json_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry.to_json() + '\n')
        except Exception as e:
            # Fallback to regular logging if JSON logging fails
            self.app_logger.error(f"Failed to write structured log: {str(e)}")
    
    def debug(self, category: LogCategory, message: str, details: Optional[Dict[str, Any]] = None):
        """Log debug message"""
        self.log(LogLevel.DEBUG, category, message, details)
    
    def info(self, category: LogCategory, message: str, details: Optional[Dict[str, Any]] = None):
        """Log info message"""
        self.log(LogLevel.INFO, category, message, details)
    
    def warning(self, category: LogCategory, message: str, details: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        self.log(LogLevel.WARNING, category, message, details)
    
    def error(self, category: LogCategory, message: str, details: Optional[Dict[str, Any]] = None):
        """Log error message"""
        self.log(LogLevel.ERROR, category, message, details)
    
    def critical(self, category: LogCategory, message: str, details: Optional[Dict[str, Any]] = None):
        """Log critical message"""
        self.log(LogLevel.CRITICAL, category, message, details)
    
    def audit(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log audit message for configuration changes"""
        self.log(LogLevel.AUDIT, LogCategory.CONFIGURATION, message, details)
    
    def log_domain_resolution(self, domain: str, success: bool, details: Optional[Dict[str, Any]] = None):
        """Log domain resolution attempt"""
        level = LogLevel.INFO if success else LogLevel.WARNING
        message = f"Domain resolution {'successful' if success else 'failed'}: {domain}"
        self.log(level, LogCategory.DOMAIN_RESOLUTION, message, details)
    
    def log_data_access(self, operation: str, success: bool, details: Optional[Dict[str, Any]] = None):
        """Log data access operation"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Data access {operation} {'successful' if success else 'failed'}"
        self.log(level, LogCategory.DATA_ACCESS, message, details)
    
    def log_cache_operation(self, operation: str, cache_key: str, success: bool, details: Optional[Dict[str, Any]] = None):
        """Log cache operation"""
        level = LogLevel.DEBUG if success else LogLevel.WARNING
        message = f"Cache {operation} for key '{cache_key}' {'successful' if success else 'failed'}"
        self.log(level, LogCategory.CACHE_OPERATION, message, details)
    
    def log_configuration_change(self, change_type: str, details: Optional[Dict[str, Any]] = None):
        """Log configuration change for audit trail"""
        message = f"Configuration change: {change_type}"
        self.audit(message, details)
    
    def log_api_request(self, endpoint: str, method: str, status_code: int, details: Optional[Dict[str, Any]] = None):
        """Log API request"""
        level = LogLevel.INFO if 200 <= status_code < 400 else LogLevel.WARNING
        message = f"API {method} {endpoint} - Status: {status_code}"
        self.log(level, LogCategory.API_REQUEST, message, details)
    
    def log_security_event(self, event_type: str, details: Optional[Dict[str, Any]] = None):
        """Log security-related event"""
        message = f"Security event: {event_type}"
        self.log(LogLevel.WARNING, LogCategory.SECURITY, message, details)
    
    def get_domain_logs(self, domain: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent logs for a specific domain"""
        domain_logs = []
        
        try:
            json_log_file = self.log_dir / "structured.jsonl"
            if not json_log_file.exists():
                return domain_logs
            
            with open(json_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # Process lines in reverse order (most recent first)
                for line in reversed(lines[-1000:]):  # Only check last 1000 lines for performance
                    try:
                        log_data = json.loads(line.strip())
                        if log_data.get('domain') == domain:
                            domain_logs.append(log_data)
                            if len(domain_logs) >= limit:
                                break
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            self.error(LogCategory.ERROR_HANDLING, f"Failed to retrieve domain logs: {str(e)}")
        
        return domain_logs
    
    def get_audit_trail(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent audit trail entries"""
        return [entry.to_dict() for entry in self._audit_entries[-limit:]]
    
    def get_error_summary(self, domain: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for monitoring"""
        error_summary = {
            'total_errors': 0,
            'error_by_category': {},
            'recent_errors': [],
            'domain': domain,
            'time_range_hours': hours
        }
        
        try:
            json_log_file = self.log_dir / "structured.jsonl"
            if not json_log_file.exists():
                return error_summary
            
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            
            with open(json_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_data = json.loads(line.strip())
                        
                        # Check if log is within time range
                        log_time = datetime.fromisoformat(log_data['timestamp']).timestamp()
                        if log_time < cutoff_time:
                            continue
                        
                        # Filter by domain if specified
                        if domain and log_data.get('domain') != domain:
                            continue
                        
                        # Count errors and warnings
                        if log_data['level'] in ['ERROR', 'CRITICAL', 'WARNING']:
                            error_summary['total_errors'] += 1
                            
                            category = log_data['category']
                            error_summary['error_by_category'][category] = \
                                error_summary['error_by_category'].get(category, 0) + 1
                            
                            # Keep recent errors (last 10)
                            if len(error_summary['recent_errors']) < 10:
                                error_summary['recent_errors'].append({
                                    'timestamp': log_data['timestamp'],
                                    'level': log_data['level'],
                                    'category': log_data['category'],
                                    'message': log_data['message'],
                                    'domain': log_data.get('domain')
                                })
                    
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            self.error(LogCategory.ERROR_HANDLING, f"Failed to generate error summary: {str(e)}")
        
        return error_summary


# Global logger instance
_domain_logger: Optional[DomainLogger] = None


def get_domain_logger() -> DomainLogger:
    """Get global domain logger instance"""
    global _domain_logger
    if _domain_logger is None:
        _domain_logger = DomainLogger()
    return _domain_logger


def init_domain_logging(app, log_dir: str = "logs"):
    """Initialize domain logging for Flask app"""
    global _domain_logger
    _domain_logger = DomainLogger(name="multi_domain_dashboard", log_dir=log_dir)
    
    # Add request ID generation
    @app.before_request
    def generate_request_id():
        import uuid
        g.request_id = str(uuid.uuid4())[:8]
    
    # Log all requests
    @app.after_request
    def log_request(response):
        logger = get_domain_logger()
        logger.log_api_request(
            endpoint=request.endpoint or request.path,
            method=request.method,
            status_code=response.status_code,
            details={
                'request_id': getattr(g, 'request_id', None),
                'response_size': len(response.get_data()) if response.get_data() else 0
            }
        )
        return response
    
    return _domain_logger
#!/usr/bin/env python3
"""
Domain Configuration Module
Handles multi-domain configuration for the dashboard system
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json
import os
from pathlib import Path


@dataclass
class ThemeConfig:
    """Configuration for domain-specific theming"""
    primary_color: str
    secondary_color: str
    accent_colors: List[str]
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThemeConfig':
        """Create ThemeConfig from dictionary"""
        return cls(
            primary_color=data.get('primary_color', '#059669'),
            secondary_color=data.get('secondary_color', '#10b981'),
            accent_colors=data.get('accent_colors', ['#34d399', '#6ee7b7', '#a7f3d0']),
            logo_url=data.get('logo_url'),
            favicon_url=data.get('favicon_url')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ThemeConfig to dictionary"""
        return {
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_colors': self.accent_colors,
            'logo_url': self.logo_url,
            'favicon_url': self.favicon_url
        }


@dataclass
class DomainConfig:
    """Configuration for a specific domain"""
    domain: str
    google_sheet_id: str
    client_name: str
    theme: ThemeConfig
    cache_timeout: int
    enabled: bool
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, domain: str, data: Dict[str, Any]) -> 'DomainConfig':
        """Create DomainConfig from dictionary"""
        theme_data = data.get('theme', {})
        theme = ThemeConfig.from_dict(theme_data)
        
        return cls(
            domain=domain,
            google_sheet_id=data.get('google_sheet_id', ''),
            client_name=data.get('client_name', ''),
            theme=theme,
            cache_timeout=data.get('cache_timeout', 300),
            enabled=data.get('enabled', True),
            custom_settings=data.get('custom_settings', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert DomainConfig to dictionary"""
        return {
            'google_sheet_id': self.google_sheet_id,
            'client_name': self.client_name,
            'theme': self.theme.to_dict(),
            'cache_timeout': self.cache_timeout,
            'enabled': self.enabled,
            'custom_settings': self.custom_settings
        }

    def validate(self) -> List[str]:
        """Validate domain configuration and return list of errors"""
        errors = []
        
        if not self.domain:
            errors.append("Domain name is required")
        
        if not self.google_sheet_id:
            errors.append("Google Sheet ID is required")
        
        if not self.client_name:
            errors.append("Client name is required")
        
        if self.cache_timeout < 0:
            errors.append("Cache timeout must be non-negative")
        
        if not self.theme.primary_color:
            errors.append("Primary color is required")
        
        if not self.theme.secondary_color:
            errors.append("Secondary color is required")
        
        if not isinstance(self.theme.accent_colors, list) or len(self.theme.accent_colors) == 0:
            errors.append("At least one accent color is required")
        
        return errors


class DomainConfigManager:
    """Manager for domain configurations"""
    
    def __init__(self, config_file_path: str = "domains.json"):
        """Initialize with configuration file path"""
        self.config_file_path = Path(config_file_path)
        self._domains: Dict[str, DomainConfig] = {}
        self._default_config: Optional[DomainConfig] = None
        
        # Initialize logger (import here to avoid circular imports)
        self._logger = None
        
        self._load_configurations()
    
    def _get_logger(self):
        """Get logger instance (lazy loading to avoid circular imports)"""
        if self._logger is None:
            try:
                from domain_logger import get_domain_logger
                self._logger = get_domain_logger()
            except ImportError:
                # Fallback to standard logging if domain_logger not available
                import logging
                self._logger = logging.getLogger(__name__)
        return self._logger
    
    def _load_configurations(self) -> None:
        """Load configurations from file"""
        try:
            if not self.config_file_path.exists():
                self._create_default_config_file()
            
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Load domains
            domains_data = config_data.get('domains', {})
            old_domains = set(self._domains.keys()) if hasattr(self, '_domains') else set()
            self._domains = {}
            
            for domain_name, domain_data in domains_data.items():
                domain_config = DomainConfig.from_dict(domain_name, domain_data)
                self._domains[domain_name] = domain_config
            
            # Load default config
            default_data = config_data.get('default_config', {})
            if default_data:
                self._default_config = DomainConfig.from_dict('default', default_data)
            
            # Log configuration changes
            new_domains = set(self._domains.keys())
            added_domains = new_domains - old_domains
            removed_domains = old_domains - new_domains
            
            if added_domains or removed_domains:
                logger = self._get_logger()
                if hasattr(logger, 'log_configuration_change'):
                    logger.log_configuration_change(
                        "domains_updated",
                        details={
                            'added_domains': list(added_domains),
                            'removed_domains': list(removed_domains),
                            'total_domains': len(new_domains),
                            'config_file': str(self.config_file_path)
                        }
                    )
            
        except Exception as e:
            logger = self._get_logger()
            if hasattr(logger, 'error'):
                from domain_logger import LogCategory
                logger.error(
                    LogCategory.CONFIGURATION,
                    f"Failed to load domain configurations: {str(e)}",
                    details={'config_file': str(self.config_file_path)}
                )
            raise Exception(f"Failed to load domain configurations: {str(e)}")
    
    def _create_default_config_file(self) -> None:
        """Create default configuration file with Desktop domain"""
        default_config = {
            "domains": {
                "dashboard-desktop.com": {
                    "google_sheet_id": "1vPoodpppoT0CF0ly7RSaEGjYzaHvWchYiimNPcUyHTI",
                    "client_name": "Desktop",
                    "theme": {
                        "primary_color": "#059669",
                        "secondary_color": "#10b981",
                        "accent_colors": ["#34d399", "#6ee7b7", "#a7f3d0"]
                    },
                    "cache_timeout": 300,
                    "enabled": True
                }
            },
            "default_config": {
                "google_sheet_id": "1vPoodpppoT0CF0ly7RSaEGjYzaHvWchYiimNPcUyHTI",
                "client_name": "Desktop",
                "theme": {
                    "primary_color": "#059669",
                    "secondary_color": "#10b981",
                    "accent_colors": ["#34d399", "#6ee7b7", "#a7f3d0"]
                },
                "cache_timeout": 300,
                "enabled": True
            }
        }
        
        with open(self.config_file_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    def get_config_by_domain(self, domain: str) -> DomainConfig:
        """Get configuration for a specific domain"""
        if domain in self._domains and self._domains[domain].enabled:
            return self._domains[domain]
        
        if self._default_config:
            return self._default_config
        
        raise ValueError(f"Domain '{domain}' not found and no default configuration available")
    
    def get_all_domains(self) -> List[str]:
        """Get list of all configured domains"""
        return [domain for domain, config in self._domains.items() if config.enabled]
    
    def validate_config(self, config_data: Dict[str, Any]) -> List[str]:
        """Validate configuration data and return list of errors"""
        errors = []
        
        if 'domains' not in config_data:
            errors.append("'domains' section is required")
            return errors
        
        domains = config_data['domains']
        if not isinstance(domains, dict):
            errors.append("'domains' must be a dictionary")
            return errors
        
        if len(domains) == 0:
            errors.append("At least one domain must be configured")
        
        # Validate each domain
        for domain_name, domain_data in domains.items():
            if not isinstance(domain_data, dict):
                errors.append(f"Domain '{domain_name}' configuration must be a dictionary")
                continue
            
            try:
                domain_config = DomainConfig.from_dict(domain_name, domain_data)
                domain_errors = domain_config.validate()
                for error in domain_errors:
                    errors.append(f"Domain '{domain_name}': {error}")
            except Exception as e:
                errors.append(f"Domain '{domain_name}': Invalid configuration - {str(e)}")
        
        # Validate default config if present
        if 'default_config' in config_data:
            default_data = config_data['default_config']
            if not isinstance(default_data, dict):
                errors.append("'default_config' must be a dictionary")
            else:
                try:
                    default_config = DomainConfig.from_dict('default', default_data)
                    default_errors = default_config.validate()
                    for error in default_errors:
                        errors.append(f"Default config: {error}")
                except Exception as e:
                    errors.append(f"Default config: Invalid configuration - {str(e)}")
        
        return errors
    
    def reload_configurations(self) -> None:
        """Reload configurations from file"""
        logger = self._get_logger()
        if hasattr(logger, 'log_configuration_change'):
            logger.log_configuration_change(
                "configuration_reload_requested",
                details={'config_file': str(self.config_file_path)}
            )
        
        try:
            self._load_configurations()
            
            if hasattr(logger, 'log_configuration_change'):
                logger.log_configuration_change(
                    "configuration_reload_successful",
                    details={
                        'total_domains': len(self._domains),
                        'domains': list(self._domains.keys())
                    }
                )
        except Exception as e:
            if hasattr(logger, 'error'):
                from domain_logger import LogCategory
                logger.error(
                    LogCategory.CONFIGURATION,
                    f"Configuration reload failed: {str(e)}",
                    details={'config_file': str(self.config_file_path)}
                )
            raise
    
    def add_domain(self, domain_name: str, domain_config: DomainConfig) -> None:
        """Add or update a domain configuration"""
        # Validate the configuration
        errors = domain_config.validate()
        if errors:
            raise ValueError(f"Invalid domain configuration: {'; '.join(errors)}")
        
        is_new_domain = domain_name not in self._domains
        self._domains[domain_name] = domain_config
        self._save_configurations()
        
        # Log configuration change
        logger = self._get_logger()
        if hasattr(logger, 'log_configuration_change'):
            action = "domain_added" if is_new_domain else "domain_updated"
            logger.log_configuration_change(
                action,
                details={
                    'domain': domain_name,
                    'client_name': domain_config.client_name,
                    'google_sheet_id': domain_config.google_sheet_id,
                    'enabled': domain_config.enabled
                }
            )
    
    def remove_domain(self, domain_name: str) -> None:
        """Remove a domain configuration"""
        if domain_name in self._domains:
            removed_config = self._domains[domain_name]
            del self._domains[domain_name]
            self._save_configurations()
            
            # Log configuration change
            logger = self._get_logger()
            if hasattr(logger, 'log_configuration_change'):
                logger.log_configuration_change(
                    "domain_removed",
                    details={
                        'domain': domain_name,
                        'client_name': removed_config.client_name
                    }
                )
        else:
            raise ValueError(f"Domain '{domain_name}' not found")
    
    def _save_configurations(self) -> None:
        """Save current configurations to file"""
        config_data = {
            "domains": {
                domain: config.to_dict() 
                for domain, config in self._domains.items()
            }
        }
        
        if self._default_config:
            config_data["default_config"] = self._default_config.to_dict()
        
        with open(self.config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
#!/usr/bin/env python3
"""
Configuration Migration System
Handles migration from legacy configuration to multi-domain format
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from domain_config import DomainConfig, ThemeConfig, DomainConfigManager


@dataclass
class LegacyConfig:
    """Represents legacy configuration found in environment or files"""
    google_sheet_id: str
    client_name: str
    domain: Optional[str] = None
    theme_color: Optional[str] = None
    cache_timeout: Optional[int] = None
    source: str = "unknown"  # environment, .env file, etc.


class ConfigMigrationManager:
    """Manages migration from legacy configuration to multi-domain format"""
    
    def __init__(self, config_file_path: str = "domains.json"):
        self.config_file_path = Path(config_file_path)
        self.backup_dir = Path("config_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize logger
        self._logger = None
    
    def _get_logger(self):
        """Get logger instance (lazy loading to avoid circular imports)"""
        if self._logger is None:
            try:
                from domain_logger import get_domain_logger
                self._logger = get_domain_logger()
            except ImportError:
                import logging
                self._logger = logging.getLogger(__name__)
        return self._logger
    
    def detect_legacy_configuration(self) -> List[LegacyConfig]:
        """Detect legacy configuration from various sources"""
        legacy_configs = []
        
        # Check environment variables
        env_config = self._detect_env_variables()
        if env_config:
            legacy_configs.append(env_config)
        
        # Check .env files
        env_file_configs = self._detect_env_files()
        legacy_configs.extend(env_file_configs)
        
        # Check docker-compose files
        docker_configs = self._detect_docker_compose_config()
        legacy_configs.extend(docker_configs)
        
        return legacy_configs
    
    def _detect_env_variables(self) -> Optional[LegacyConfig]:
        """Detect legacy configuration from environment variables"""
        google_sheet_id = os.getenv('GOOGLE_SHEET_ID')
        client_name = os.getenv('CLIENT_NAME')
        
        if google_sheet_id or client_name:
            return LegacyConfig(
                google_sheet_id=google_sheet_id or '',
                client_name=client_name or 'Desktop',
                domain=os.getenv('DOMAIN'),
                theme_color=os.getenv('THEME_COLOR'),
                cache_timeout=int(os.getenv('CACHE_TIMEOUT', 300)),
                source="environment_variables"
            )
        
        return None
    
    def _detect_env_files(self) -> List[LegacyConfig]:
        """Detect legacy configuration from .env files"""
        configs = []
        env_files = ['.env', '.env.production', '.env.development', 'backend/.env']
        
        for env_file in env_files:
            env_path = Path(env_file)
            if env_path.exists():
                config = self._parse_env_file(env_path)
                if config:
                    configs.append(config)
        
        return configs
    
    def _parse_env_file(self, env_path: Path) -> Optional[LegacyConfig]:
        """Parse a .env file for legacy configuration"""
        try:
            env_vars = {}
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
            
            google_sheet_id = env_vars.get('GOOGLE_SHEET_ID')
            client_name = env_vars.get('CLIENT_NAME')
            
            if google_sheet_id or client_name:
                cache_timeout = 300
                if 'CACHE_TIMEOUT' in env_vars:
                    try:
                        cache_timeout = int(env_vars['CACHE_TIMEOUT'])
                    except ValueError:
                        pass
                
                return LegacyConfig(
                    google_sheet_id=google_sheet_id or '',
                    client_name=client_name or 'Desktop',
                    domain=env_vars.get('DOMAIN'),
                    theme_color=env_vars.get('THEME_COLOR'),
                    cache_timeout=cache_timeout,
                    source=f"env_file:{env_path}"
                )
        
        except Exception as e:
            logger = self._get_logger()
            if hasattr(logger, 'error') and hasattr(logger, 'LogCategory'):
                try:
                    from domain_logger import LogCategory
                    logger.error(
                        LogCategory.CONFIGURATION,
                        f"Failed to parse env file {env_path}: {str(e)}",
                        details={'env_file': str(env_path)}
                    )
                except ImportError:
                    logger.error(f"Failed to parse env file {env_path}: {str(e)}")
            elif hasattr(logger, 'error'):
                logger.error(f"Failed to parse env file {env_path}: {str(e)}")
        
        return None
    
    def _detect_docker_compose_config(self) -> List[LegacyConfig]:
        """Detect legacy configuration from docker-compose files"""
        configs = []
        compose_files = ['docker-compose.yml', 'docker-compose.dev.yml', 'docker-compose.prod.yml']
        
        for compose_file in compose_files:
            compose_path = Path(compose_file)
            if compose_path.exists():
                config = self._parse_docker_compose(compose_path)
                if config:
                    configs.append(config)
        
        return configs
    
    def _parse_docker_compose(self, compose_path: Path) -> Optional[LegacyConfig]:
        """Parse docker-compose file for legacy environment variables"""
        try:
            with open(compose_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple parsing for environment variables
            google_sheet_id = None
            client_name = None
            domain = None
            cache_timeout = 300
            
            for line in content.split('\n'):
                line = line.strip()
                if 'GOOGLE_SHEET_ID=' in line:
                    google_sheet_id = line.split('GOOGLE_SHEET_ID=')[1].strip()
                elif 'CLIENT_NAME=' in line:
                    client_name = line.split('CLIENT_NAME=')[1].strip()
                elif 'DOMAIN=' in line:
                    domain = line.split('DOMAIN=')[1].strip()
                elif 'CACHE_TIMEOUT=' in line:
                    try:
                        cache_timeout = int(line.split('CACHE_TIMEOUT=')[1].strip())
                    except ValueError:
                        pass
            
            if google_sheet_id or client_name:
                return LegacyConfig(
                    google_sheet_id=google_sheet_id or '',
                    client_name=client_name or 'Desktop',
                    domain=domain,
                    cache_timeout=cache_timeout,
                    source=f"docker_compose:{compose_path}"
                )
        
        except Exception as e:
            logger = self._get_logger()
            if hasattr(logger, 'error') and hasattr(logger, 'LogCategory'):
                try:
                    from domain_logger import LogCategory
                    logger.error(
                        LogCategory.CONFIGURATION,
                        f"Failed to parse docker-compose file {compose_path}: {str(e)}",
                        details={'compose_file': str(compose_path)}
                    )
                except ImportError:
                    logger.error(f"Failed to parse docker-compose file {compose_path}: {str(e)}")
            elif hasattr(logger, 'error'):
                logger.error(f"Failed to parse docker-compose file {compose_path}: {str(e)}")
        
        return None
    
    def validate_desktop_compatibility(self) -> Tuple[bool, List[str]]:
        """Validate that existing Desktop configuration is compatible"""
        issues = []
        
        try:
            # Check if domains.json exists and has Desktop configuration
            if not self.config_file_path.exists():
                issues.append("domains.json file does not exist")
                return False, issues
            
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Check for Desktop domain
            domains = config_data.get('domains', {})
            desktop_domain = None
            
            # Look for Desktop configuration
            for domain, domain_config in domains.items():
                if domain_config.get('client_name') == 'Desktop':
                    desktop_domain = domain
                    break
            
            if not desktop_domain:
                issues.append("No Desktop domain configuration found")
            else:
                # Validate Desktop configuration
                desktop_config = domains[desktop_domain]
                
                if not desktop_config.get('google_sheet_id'):
                    issues.append("Desktop configuration missing google_sheet_id")
                
                if not desktop_config.get('client_name'):
                    issues.append("Desktop configuration missing client_name")
                
                theme = desktop_config.get('theme', {})
                if not theme.get('primary_color'):
                    issues.append("Desktop configuration missing theme.primary_color")
                
                if not isinstance(desktop_config.get('enabled'), bool):
                    issues.append("Desktop configuration missing or invalid 'enabled' field")
            
            # Check default configuration
            default_config = config_data.get('default_config')
            if not default_config:
                issues.append("Missing default_config section")
            elif default_config.get('client_name') != 'Desktop':
                issues.append("default_config does not reference Desktop configuration")
            
        except Exception as e:
            issues.append(f"Failed to validate configuration: {str(e)}")
        
        return len(issues) == 0, issues
    
    def create_backup(self) -> Path:
        """Create backup of current configuration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"domains_backup_{timestamp}.json"
        
        if self.config_file_path.exists():
            # Ensure backup directory exists
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.config_file_path, backup_path)
            
            logger = self._get_logger()
            if hasattr(logger, 'log_configuration_change'):
                logger.log_configuration_change(
                    "configuration_backup_created",
                    details={
                        'backup_path': str(backup_path),
                        'original_path': str(self.config_file_path)
                    }
                )
        
        return backup_path
    
    def migrate_legacy_config(self, legacy_config: LegacyConfig, force: bool = False) -> bool:
        """Migrate legacy configuration to multi-domain format"""
        try:
            # Create backup first
            backup_path = self.create_backup()
            
            # Determine domain name
            domain_name = legacy_config.domain or "dashboard-desktop.com"
            
            # Create theme configuration
            theme_config = self._create_theme_from_legacy(legacy_config)
            
            # Create domain configuration
            domain_config = DomainConfig(
                domain=domain_name,
                google_sheet_id=legacy_config.google_sheet_id,
                client_name=legacy_config.client_name,
                theme=theme_config,
                cache_timeout=legacy_config.cache_timeout or 300,
                enabled=True
            )
            
            # Validate the configuration
            errors = domain_config.validate()
            if errors and not force:
                logger = self._get_logger()
                if hasattr(logger, 'error'):
                    logger.error(f"Legacy configuration validation failed: {'; '.join(errors)}")
                return False
            
            # Create or update domains.json
            config_data = {
                "domains": {
                    domain_name: domain_config.to_dict()
                },
                "default_config": domain_config.to_dict()
            }
            
            # If domains.json already exists, merge configurations
            if self.config_file_path.exists():
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
                
                existing_domains = existing_config.get('domains', {})
                config_data['domains'].update(existing_domains)
            
            # Write new configuration
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Log migration
            logger = self._get_logger()
            if hasattr(logger, 'log_configuration_change'):
                logger.log_configuration_change(
                    "legacy_configuration_migrated",
                    details={
                        'source': legacy_config.source,
                        'domain': domain_name,
                        'client_name': legacy_config.client_name,
                        'google_sheet_id': legacy_config.google_sheet_id,
                        'backup_path': str(backup_path)
                    }
                )
            
            return True
            
        except Exception as e:
            logger = self._get_logger()
            if hasattr(logger, 'error') and hasattr(logger, 'LogCategory'):
                from domain_logger import LogCategory
                logger.error(
                    LogCategory.CONFIGURATION,
                    f"Migration failed: {str(e)}",
                    details={'legacy_source': legacy_config.source}
                )
            elif hasattr(logger, 'error'):
                logger.error(f"Migration failed: {str(e)}")
            return False
    
    def _create_theme_from_legacy(self, legacy_config: LegacyConfig) -> ThemeConfig:
        """Create theme configuration from legacy settings"""
        # Default Desktop theme
        primary_color = "#059669"
        secondary_color = "#10b981"
        accent_colors = ["#34d399", "#6ee7b7", "#a7f3d0"]
        
        # Map legacy theme colors
        if legacy_config.theme_color:
            color_map = {
                'green': ("#059669", "#10b981", ["#34d399", "#6ee7b7", "#a7f3d0"]),
                'blue': ("#3b82f6", "#60a5fa", ["#93c5fd", "#bfdbfe", "#dbeafe"]),
                'red': ("#dc2626", "#ef4444", ["#f87171", "#fca5a5", "#fecaca"]),
                'purple': ("#7c3aed", "#8b5cf6", ["#a78bfa", "#c4b5fd", "#ddd6fe"])
            }
            
            if legacy_config.theme_color.lower() in color_map:
                primary_color, secondary_color, accent_colors = color_map[legacy_config.theme_color.lower()]
        
        return ThemeConfig(
            primary_color=primary_color,
            secondary_color=secondary_color,
            accent_colors=accent_colors
        )
    
    def auto_migrate(self) -> Dict[str, Any]:
        """Automatically detect and migrate legacy configurations"""
        migration_results = {
            'success': False,
            'legacy_configs_found': [],
            'migrations_performed': [],
            'errors': [],
            'backup_created': None
        }
        
        try:
            # Detect legacy configurations
            legacy_configs = self.detect_legacy_configuration()
            migration_results['legacy_configs_found'] = [
                {
                    'source': config.source,
                    'client_name': config.client_name,
                    'google_sheet_id': config.google_sheet_id,
                    'domain': config.domain
                }
                for config in legacy_configs
            ]
            
            if not legacy_configs:
                migration_results['success'] = True
                migration_results['errors'].append("No legacy configuration found")
                return migration_results
            
            # Create backup
            backup_path = self.create_backup()
            migration_results['backup_created'] = str(backup_path)
            
            # Migrate each configuration
            for legacy_config in legacy_configs:
                try:
                    success = self.migrate_legacy_config(legacy_config)
                    if success:
                        migration_results['migrations_performed'].append({
                            'source': legacy_config.source,
                            'domain': legacy_config.domain or "dashboard-desktop.com",
                            'client_name': legacy_config.client_name
                        })
                    else:
                        migration_results['errors'].append(
                            f"Failed to migrate configuration from {legacy_config.source}"
                        )
                except Exception as e:
                    migration_results['errors'].append(
                        f"Error migrating {legacy_config.source}: {str(e)}"
                    )
            
            # Validate final configuration only if we have Desktop configuration
            has_desktop = any(
                config.client_name == 'Desktop' 
                for config in legacy_configs
            )
            
            if has_desktop:
                is_compatible, compatibility_issues = self.validate_desktop_compatibility()
                if not is_compatible:
                    migration_results['errors'].extend(compatibility_issues)
                else:
                    migration_results['success'] = True
            else:
                # If no Desktop config, just check that migration was successful
                migration_results['success'] = len(migration_results['migrations_performed']) > 0
            
        except Exception as e:
            migration_results['errors'].append(f"Auto-migration failed: {str(e)}")
        
        return migration_results
    
    def generate_migration_report(self) -> str:
        """Generate a detailed migration report"""
        report_lines = []
        report_lines.append("=== Configuration Migration Report ===")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Check current configuration
        report_lines.append("Current Configuration Status:")
        if self.config_file_path.exists():
            report_lines.append(f"✓ domains.json exists at {self.config_file_path}")
            
            is_compatible, issues = self.validate_desktop_compatibility()
            if is_compatible:
                report_lines.append("✓ Desktop configuration is compatible")
            else:
                report_lines.append("✗ Desktop configuration has issues:")
                for issue in issues:
                    report_lines.append(f"  - {issue}")
        else:
            report_lines.append(f"✗ domains.json not found at {self.config_file_path}")
        
        report_lines.append("")
        
        # Check for legacy configurations
        report_lines.append("Legacy Configuration Detection:")
        legacy_configs = self.detect_legacy_configuration()
        
        if legacy_configs:
            report_lines.append(f"Found {len(legacy_configs)} legacy configuration(s):")
            for config in legacy_configs:
                report_lines.append(f"  Source: {config.source}")
                report_lines.append(f"    Client Name: {config.client_name}")
                report_lines.append(f"    Google Sheet ID: {config.google_sheet_id}")
                report_lines.append(f"    Domain: {config.domain or 'Not specified'}")
                report_lines.append("")
        else:
            report_lines.append("No legacy configurations detected")
        
        report_lines.append("")
        
        # Migration recommendations
        report_lines.append("Migration Recommendations:")
        if legacy_configs and not self.config_file_path.exists():
            report_lines.append("1. Run auto-migration to create domains.json from legacy config")
            report_lines.append("2. Validate the migrated configuration")
            report_lines.append("3. Test the application with new configuration")
        elif legacy_configs and self.config_file_path.exists():
            # Check if legacy configs are already migrated
            is_compatible, _ = self.validate_desktop_compatibility()
            if is_compatible and len(legacy_configs) == 1:
                # Check if the legacy config matches existing config
                legacy_config = legacy_configs[0]
                if legacy_config.client_name == 'Desktop':
                    report_lines.append("No migration needed - Desktop configuration appears to be up to date")
                else:
                    report_lines.append("1. Review existing domains.json configuration")
                    report_lines.append("2. Consider if legacy configurations need to be merged")
                    report_lines.append("3. Validate Desktop compatibility")
            else:
                report_lines.append("1. Review existing domains.json configuration")
                report_lines.append("2. Consider if legacy configurations need to be merged")
                report_lines.append("3. Validate Desktop compatibility")
        else:
            report_lines.append("No migration needed - configuration appears to be up to date")
        
        return "\n".join(report_lines)


def main():
    """CLI interface for migration system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Configuration Migration Tool")
    parser.add_argument('--detect', action='store_true', help='Detect legacy configurations')
    parser.add_argument('--migrate', action='store_true', help='Auto-migrate legacy configurations')
    parser.add_argument('--validate', action='store_true', help='Validate Desktop compatibility')
    parser.add_argument('--report', action='store_true', help='Generate migration report')
    parser.add_argument('--config-file', default='domains.json', help='Path to domains.json file')
    
    args = parser.parse_args()
    
    migration_manager = ConfigMigrationManager(args.config_file)
    
    if args.detect:
        legacy_configs = migration_manager.detect_legacy_configuration()
        if legacy_configs:
            print(f"Found {len(legacy_configs)} legacy configuration(s):")
            for config in legacy_configs:
                print(f"  - {config.source}: {config.client_name} ({config.google_sheet_id})")
        else:
            print("No legacy configurations detected")
    
    elif args.migrate:
        results = migration_manager.auto_migrate()
        if results['success']:
            print("Migration completed successfully!")
            if results['migrations_performed']:
                print("Migrated configurations:")
                for migration in results['migrations_performed']:
                    print(f"  - {migration['source']} -> {migration['domain']}")
        else:
            print("Migration failed:")
            for error in results['errors']:
                print(f"  - {error}")
    
    elif args.validate:
        is_compatible, issues = migration_manager.validate_desktop_compatibility()
        if is_compatible:
            print("✓ Desktop configuration is compatible")
        else:
            print("✗ Desktop configuration has issues:")
            for issue in issues:
                print(f"  - {issue}")
    
    elif args.report:
        report = migration_manager.generate_migration_report()
        print(report)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
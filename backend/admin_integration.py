#!/usr/bin/env python3
"""
Administration Tools Integration
Integrates all administration and monitoring tools into the main Flask application
"""

from flask import Flask
from typing import Optional

# Import all administration modules
from domain_admin import register_admin_blueprint
from domain_status_dashboard import register_dashboard_blueprint
from domain_metrics_collector import get_metrics_collector, start_metrics_collection
from domain_config import DomainConfigManager
from domain_middleware import create_domain_middleware
from domain_logger import get_domain_logger, LogCategory


class AdminToolsManager:
    """Manager for all administration tools"""
    
    def __init__(self, app: Flask, config_file: str = "domains.json"):
        """Initialize administration tools"""
        self.app = app
        self.config_file = config_file
        self.logger = get_domain_logger()
        
        # Initialize components
        self.config_manager: Optional[DomainConfigManager] = None
        self.metrics_collector = None
        
        # Setup flags
        self.is_initialized = False
        self.metrics_enabled = False
    
    def initialize(self, enable_metrics: bool = True, enable_dashboard: bool = True):
        """Initialize all administration tools"""
        try:
            self.logger.info(
                LogCategory.CONFIGURATION,
                "Initializing administration tools",
                details={
                    'config_file': self.config_file,
                    'enable_metrics': enable_metrics,
                    'enable_dashboard': enable_dashboard
                }
            )
            
            # Initialize domain middleware (this creates the config manager)
            middleware = create_domain_middleware(self.app, self.config_file)
            self.config_manager = middleware.config_manager
            
            # Store config manager in app for access by blueprints
            self.app.config['DOMAIN_CONFIG_MANAGER'] = self.config_manager
            
            # Register admin API blueprint
            register_admin_blueprint(self.app)
            self.logger.info(LogCategory.CONFIGURATION, "Admin API blueprint registered")
            
            # Register dashboard blueprint if enabled
            if enable_dashboard:
                register_dashboard_blueprint(self.app)
                self.logger.info(LogCategory.CONFIGURATION, "Dashboard blueprint registered")
            
            # Initialize metrics collection if enabled
            if enable_metrics:
                self.metrics_collector = get_metrics_collector()
                start_metrics_collection()
                self.metrics_enabled = True
                self.logger.info(LogCategory.CONFIGURATION, "Metrics collection started")
            
            self.is_initialized = True
            
            self.logger.info(
                LogCategory.CONFIGURATION,
                "Administration tools initialized successfully",
                details={
                    'admin_api': True,
                    'dashboard': enable_dashboard,
                    'metrics': enable_metrics
                }
            )
            
        except Exception as e:
            self.logger.error(
                LogCategory.ERROR_HANDLING,
                f"Failed to initialize administration tools: {str(e)}"
            )
            raise
    
    def shutdown(self):
        """Shutdown administration tools"""
        try:
            if self.metrics_enabled and self.metrics_collector:
                self.metrics_collector.stop_collection()
                self.logger.info(LogCategory.CONFIGURATION, "Metrics collection stopped")
            
            self.is_initialized = False
            self.metrics_enabled = False
            
            self.logger.info(LogCategory.CONFIGURATION, "Administration tools shutdown completed")
            
        except Exception as e:
            self.logger.error(
                LogCategory.ERROR_HANDLING,
                f"Error during administration tools shutdown: {str(e)}"
            )
    
    def get_status(self) -> dict:
        """Get status of all administration tools"""
        return {
            'initialized': self.is_initialized,
            'config_manager': self.config_manager is not None,
            'metrics_enabled': self.metrics_enabled,
            'total_domains': len(self.config_manager.get_all_domains()) if self.config_manager else 0,
            'config_file': self.config_file
        }
    
    def reload_configuration(self):
        """Reload domain configuration"""
        if not self.config_manager:
            raise RuntimeError("Configuration manager not initialized")
        
        try:
            old_domains = set(self.config_manager.get_all_domains())
            self.config_manager.reload_configurations()
            new_domains = set(self.config_manager.get_all_domains())
            
            added = new_domains - old_domains
            removed = old_domains - new_domains
            
            self.logger.audit(
                "Configuration reloaded via admin tools",
                details={
                    'added_domains': list(added),
                    'removed_domains': list(removed),
                    'total_domains': len(new_domains)
                }
            )
            
            return {
                'success': True,
                'added_domains': list(added),
                'removed_domains': list(removed),
                'total_domains': len(new_domains)
            }
            
        except Exception as e:
            self.logger.error(
                LogCategory.ERROR_HANDLING,
                f"Configuration reload failed: {str(e)}"
            )
            raise


def setup_admin_tools(app: Flask, config_file: str = "domains.json", 
                     enable_metrics: bool = True, enable_dashboard: bool = True) -> AdminToolsManager:
    """
    Setup administration tools for a Flask application
    
    Args:
        app: Flask application instance
        config_file: Path to domain configuration file
        enable_metrics: Whether to enable metrics collection
        enable_dashboard: Whether to enable web dashboard
    
    Returns:
        AdminToolsManager instance
    """
    admin_manager = AdminToolsManager(app, config_file)
    admin_manager.initialize(enable_metrics, enable_dashboard)
    
    # Store manager in app for access
    app.admin_tools_manager = admin_manager
    
    # Register shutdown handler
    @app.teardown_appcontext
    def shutdown_admin_tools(exception):
        if hasattr(app, 'admin_tools_manager'):
            # Note: We don't shutdown here as it would stop metrics collection
            # Shutdown should be handled by the application lifecycle
            pass
    
    return admin_manager


def create_admin_cli_commands(app: Flask):
    """Create CLI commands for administration tools"""
    
    @app.cli.command()
    def admin_status():
        """Show administration tools status"""
        if hasattr(app, 'admin_tools_manager'):
            status = app.admin_tools_manager.get_status()
            print("Administration Tools Status:")
            print(f"  Initialized: {status['initialized']}")
            print(f"  Config Manager: {status['config_manager']}")
            print(f"  Metrics Enabled: {status['metrics_enabled']}")
            print(f"  Total Domains: {status['total_domains']}")
            print(f"  Config File: {status['config_file']}")
        else:
            print("Administration tools not initialized")
    
    @app.cli.command()
    def validate_config():
        """Validate domain configuration"""
        from validate_domain_config import ConfigValidator
        
        if hasattr(app, 'admin_tools_manager'):
            config_file = app.admin_tools_manager.config_file
        else:
            config_file = "domains.json"
        
        validator = ConfigValidator()
        result = validator.validate_file(config_file)
        
        print(f"Configuration Validation Results for: {config_file}")
        print("=" * 60)
        
        if result['valid']:
            print("✅ Configuration is VALID")
        else:
            print("❌ Configuration has ERRORS")
        
        print(f"\nSummary:")
        print(f"  Errors: {result['summary']['error_count']}")
        print(f"  Warnings: {result['summary']['warning_count']}")
        print(f"  Suggestions: {result['summary']['suggestion_count']}")
        
        if result['errors']:
            print(f"\n🚨 ERRORS:")
            for i, error in enumerate(result['errors'], 1):
                print(f"  {i}. {error}")
    
    @app.cli.command()
    def monitor_domains():
        """Run domain monitoring check"""
        from domain_monitor import DomainMonitor
        
        if hasattr(app, 'admin_tools_manager'):
            config_file = app.admin_tools_manager.config_file
        else:
            config_file = "domains.json"
        
        monitor = DomainMonitor(config_file)
        health_metrics = monitor.check_all_domains()
        monitor.print_health_report(health_metrics)
    
    @app.cli.command()
    def reload_config():
        """Reload domain configuration"""
        if hasattr(app, 'admin_tools_manager'):
            try:
                result = app.admin_tools_manager.reload_configuration()
                print("✅ Configuration reloaded successfully")
                print(f"  Total domains: {result['total_domains']}")
                if result['added_domains']:
                    print(f"  Added: {', '.join(result['added_domains'])}")
                if result['removed_domains']:
                    print(f"  Removed: {', '.join(result['removed_domains'])}")
            except Exception as e:
                print(f"❌ Configuration reload failed: {str(e)}")
        else:
            print("Administration tools not initialized")
    
    @app.cli.command()
    def export_metrics():
        """Export collected metrics"""
        if hasattr(app, 'admin_tools_manager') and app.admin_tools_manager.metrics_enabled:
            try:
                collector = get_metrics_collector()
                json_export = collector.export_metrics('json')
                
                # Save to file
                from datetime import datetime
                filename = f"metrics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                with open(filename, 'w') as f:
                    f.write(json_export)
                
                print(f"✅ Metrics exported to: {filename}")
                
                # Show summary
                summary = collector.get_system_metrics_summary()
                print(f"\nMetrics Summary:")
                print(f"  Total domains: {summary['total_domains']}")
                print(f"  Avg response time: {summary['avg_response_time']:.2f}ms")
                print(f"  Avg cache hit rate: {summary['avg_cache_hit_rate']:.1f}%")
                print(f"  Total requests: {summary['total_requests']}")
                
            except Exception as e:
                print(f"❌ Metrics export failed: {str(e)}")
        else:
            print("Metrics collection not enabled")


# Example usage function
def example_integration():
    """Example of how to integrate administration tools"""
    
    # Create Flask app
    app = Flask(__name__)
    
    # Setup administration tools
    admin_manager = setup_admin_tools(
        app, 
        config_file="domains.json",
        enable_metrics=True,
        enable_dashboard=True
    )
    
    # Create CLI commands
    create_admin_cli_commands(app)
    
    # Add some basic routes
    @app.route('/')
    def home():
        return "Multi-Domain Dashboard - Administration Tools Enabled"
    
    @app.route('/admin/status')
    def admin_status():
        return admin_manager.get_status()
    
    # Example of using metrics in a route
    @app.route('/api/data')
    def get_data():
        import time
        from flask import request
        
        start_time = time.time()
        
        # Simulate some work
        time.sleep(0.1)
        
        # Record metrics if available
        if admin_manager.metrics_enabled:
            domain = request.headers.get('Host', 'unknown')
            response_time = time.time() - start_time
            admin_manager.metrics_collector.record_request(domain, response_time)
        
        return {"message": "Data retrieved successfully"}
    
    return app


if __name__ == '__main__':
    # Run example integration
    app = example_integration()
    
    print("Administration Tools Integration Example")
    print("Available endpoints:")
    print("  / - Home page")
    print("  /admin/status - Admin tools status")
    print("  /api/admin/* - Admin API endpoints")
    print("  /admin/dashboard/ - Web dashboard")
    print("\nCLI commands:")
    print("  flask admin-status - Show admin tools status")
    print("  flask validate-config - Validate configuration")
    print("  flask monitor-domains - Run domain monitoring")
    print("  flask reload-config - Reload configuration")
    print("  flask export-metrics - Export metrics")
    
    # Run in debug mode
    app.run(debug=True, port=5000)
#!/usr/bin/env python3
"""
Docker Start Script
Inicialização otimizada para ambiente Docker com ferramentas de administração
"""

import os
import sys
import time
import signal
from pathlib import Path

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, admin_manager
from domain_logger import get_domain_logger, LogCategory


def setup_signal_handlers():
    """Configurar handlers para sinais do sistema"""
    def signal_handler(signum, frame):
        logger = get_domain_logger()
        logger.info(
            LogCategory.CONFIGURATION,
            f"Received signal {signum}, shutting down gracefully..."
        )
        
        # Shutdown admin tools
        if hasattr(app, 'admin_tools_manager'):
            app.admin_tools_manager.shutdown()
        
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


def validate_environment():
    """Validar ambiente antes de iniciar"""
    logger = get_domain_logger()
    
    # Verificar arquivo de configuração
    config_file = "domains.json"
    if not Path(config_file).exists():
        logger.error(
            LogCategory.CONFIGURATION,
            f"Configuration file {config_file} not found"
        )
        return False
    
    # Verificar diretórios necessários
    required_dirs = ['logs', 'data']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(
                LogCategory.CONFIGURATION,
                f"Created directory: {dir_name}"
            )
    
    # Validar configuração
    try:
        from validate_domain_config import ConfigValidator
        validator = ConfigValidator()
        result = validator.validate_file(config_file)
        
        if not result['valid']:
            logger.warning(
                LogCategory.CONFIGURATION,
                f"Configuration validation found {len(result['errors'])} errors and {len(result['warnings'])} warnings"
            )
            
            # Log errors
            for error in result['errors']:
                logger.error(LogCategory.CONFIGURATION, f"Config error: {error}")
            
            # Log warnings
            for warning in result['warnings']:
                logger.warning(LogCategory.CONFIGURATION, f"Config warning: {warning}")
            
            # Don't start if there are critical errors
            if result['errors']:
                return False
        
        logger.info(
            LogCategory.CONFIGURATION,
            "Configuration validation passed"
        )
        
    except Exception as e:
        logger.error(
            LogCategory.CONFIGURATION,
            f"Configuration validation failed: {str(e)}"
        )
        return False
    
    return True


def print_startup_info():
    """Imprimir informações de inicialização"""
    logger = get_domain_logger()
    
    print("\n" + "="*80)
    print("🚀 MULTI-DOMAIN DASHBOARD - STARTING UP")
    print("="*80)
    
    # Informações do sistema
    print(f"📍 Working Directory: {os.getcwd()}")
    print(f"🐍 Python Version: {sys.version}")
    print(f"🌐 Flask Environment: {os.getenv('FLASK_ENV', 'production')}")
    
    # Informações das ferramentas de administração
    if hasattr(app, 'admin_tools_manager'):
        status = app.admin_tools_manager.get_status()
        print(f"\n🔧 Administration Tools:")
        print(f"   ✅ Initialized: {status['initialized']}")
        print(f"   📊 Metrics Enabled: {status['metrics_enabled']}")
        print(f"   🏥 Dashboard Available: /admin/dashboard/")
        print(f"   🔌 Admin API: /api/admin/*")
        print(f"   📋 Total Domains: {status['total_domains']}")
    
    # URLs disponíveis
    print(f"\n🌐 Available Endpoints:")
    print(f"   📊 Dashboard: http://localhost:5000/admin/dashboard/")
    print(f"   🔌 Admin API: http://localhost:5000/api/admin/")
    print(f"   ❤️  Health Check: http://localhost:5000/api/health")
    print(f"   📈 Main API: http://localhost:5000/api/dashboard/")
    
    # Comandos CLI disponíveis
    print(f"\n💻 CLI Commands Available:")
    print(f"   flask admin-status - Show admin tools status")
    print(f"   flask validate-config - Validate configuration")
    print(f"   flask monitor-domains - Run domain monitoring")
    print(f"   flask reload-config - Reload configuration")
    print(f"   flask export-metrics - Export metrics")
    
    print("="*80)
    
    logger.info(
        LogCategory.CONFIGURATION,
        "Multi-domain dashboard startup completed",
        details={
            'admin_tools_enabled': hasattr(app, 'admin_tools_manager'),
            'total_domains': status['total_domains'] if hasattr(app, 'admin_tools_manager') else 0,
            'environment': os.getenv('FLASK_ENV', 'production')
        }
    )


def main():
    """Função principal de inicialização"""
    logger = get_domain_logger()
    
    try:
        # Configurar handlers de sinal
        setup_signal_handlers()
        
        # Validar ambiente
        if not validate_environment():
            logger.error(LogCategory.CONFIGURATION, "Environment validation failed")
            sys.exit(1)
        
        # Imprimir informações de inicialização
        print_startup_info()
        
        # Configurações do servidor
        host = os.getenv('FLASK_HOST', '0.0.0.0')
        port = int(os.getenv('FLASK_PORT', 5000))
        debug = os.getenv('FLASK_ENV') == 'development'
        
        logger.info(
            LogCategory.CONFIGURATION,
            f"Starting Flask server on {host}:{port}",
            details={
                'host': host,
                'port': port,
                'debug': debug
            }
        )
        
        # Iniciar servidor
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info(LogCategory.CONFIGURATION, "Received keyboard interrupt, shutting down...")
        
    except Exception as e:
        logger.critical(
            LogCategory.ERROR_HANDLING,
            f"Fatal error during startup: {str(e)}"
        )
        sys.exit(1)
    
    finally:
        # Cleanup
        if hasattr(app, 'admin_tools_manager'):
            app.admin_tools_manager.shutdown()
        
        logger.info(LogCategory.CONFIGURATION, "Application shutdown completed")


if __name__ == '__main__':
    main()
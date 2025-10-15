#!/usr/bin/env python3
"""
Configuration Migration Script
Provides easy migration from legacy configuration to multi-domain format
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from config_migration import ConfigMigrationManager


def main():
    """Main migration script"""
    print("🔄 Dashboard Configuration Migration Tool")
    print("=" * 50)
    
    # Change to backend directory for proper file paths
    os.chdir(backend_dir)
    
    migration_manager = ConfigMigrationManager()
    
    # Generate and display report
    print("\n📋 Current Configuration Status:")
    print("-" * 30)
    report = migration_manager.generate_migration_report()
    print(report)
    
    # Check for legacy configurations
    legacy_configs = migration_manager.detect_legacy_configuration()
    
    if not legacy_configs:
        print("\n✅ No legacy configuration detected. System appears to be up to date.")
        return
    
    print(f"\n🔍 Found {len(legacy_configs)} legacy configuration(s)")
    for i, config in enumerate(legacy_configs, 1):
        print(f"  {i}. Source: {config.source}")
        print(f"     Client: {config.client_name}")
        print(f"     Sheet ID: {config.google_sheet_id}")
        print(f"     Domain: {config.domain or 'Not specified'}")
    
    # Ask user for confirmation
    print("\n❓ Do you want to migrate these configurations? (y/N): ", end="")
    response = input().strip().lower()
    
    if response not in ['y', 'yes']:
        print("Migration cancelled.")
        return
    
    # Perform migration
    print("\n🚀 Starting migration...")
    results = migration_manager.auto_migrate()
    
    if results['success']:
        print("✅ Migration completed successfully!")
        
        if results['backup_created']:
            print(f"📦 Backup created: {results['backup_created']}")
        
        if results['migrations_performed']:
            print("\n📝 Migrated configurations:")
            for migration in results['migrations_performed']:
                print(f"  ✓ {migration['source']} -> {migration['domain']}")
        
        print("\n🎉 Your application is now configured for multi-domain support!")
        print("📖 Next steps:")
        print("  1. Review the generated domains.json file")
        print("  2. Test your application with the new configuration")
        print("  3. Add additional domains as needed")
        
    else:
        print("❌ Migration failed!")
        print("\n🚨 Errors encountered:")
        for error in results['errors']:
            print(f"  - {error}")
        
        if results['backup_created']:
            print(f"\n📦 Backup available at: {results['backup_created']}")
        
        print("\n🔧 Troubleshooting:")
        print("  1. Check that all required fields are present in legacy config")
        print("  2. Ensure GOOGLE_SHEET_ID is valid")
        print("  3. Verify file permissions for domains.json")


if __name__ == '__main__':
    main()
# Configuration Migration Guide

This guide explains how to migrate from legacy single-domain configuration to the new multi-domain system.

## Overview

The multi-domain dashboard system supports multiple clients with isolated configurations. The migration system automatically detects and converts legacy configurations to the new format while maintaining backward compatibility.

## Migration Process

### 1. Automatic Detection

The migration system automatically detects legacy configuration from:

- **Environment Variables**: `GOOGLE_SHEET_ID`, `CLIENT_NAME`, `DOMAIN`, etc.
- **.env Files**: `.env`, `.env.production`, `.env.development`
- **Docker Compose Files**: `docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.prod.yml`

### 2. Migration Tools

#### Command Line Tool

```bash
# Check current status
cd backend
python config_migration.py --report

# Detect legacy configurations
python config_migration.py --detect

# Validate Desktop compatibility
python config_migration.py --validate

# Perform automatic migration
python config_migration.py --migrate
```

#### Shell Script (Recommended)

```bash
# Generate migration report
./scripts/migrate.sh report

# Detect legacy configurations
./scripts/migrate.sh detect

# Validate configuration
./scripts/migrate.sh validate

# Perform migration with confirmation
./scripts/migrate.sh migrate

# Interactive migration wizard
./scripts/migrate.sh interactive
```

### 3. Migration Steps

1. **Backup**: Automatic backup of existing configuration
2. **Detection**: Scan for legacy configuration sources
3. **Validation**: Validate legacy configuration completeness
4. **Migration**: Convert to multi-domain format
5. **Verification**: Ensure Desktop compatibility

## Legacy Configuration Sources

### Environment Variables

```bash
GOOGLE_SHEET_ID=1vPoodpppoT0CF0ly7RSaEGjYzaHvWchYiimNPcUyHTI
CLIENT_NAME=Desktop
DOMAIN=dashboard-desktop.com
THEME_COLOR=green
CACHE_TIMEOUT=300
```

### .env Files

```env
# Dashboard Desktop - Production Configuration
GOOGLE_SHEET_ID=1vPoodpppoT0CF0ly7RSaEGjYzaHvWchYiimNPcUyHTI
CLIENT_NAME=Desktop
FLASK_ENV=production
DOMAIN=dashboard-desktop.com
THEME_COLOR=green
CACHE_TIMEOUT=300
```

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    environment:
      - GOOGLE_SHEET_ID=1vPoodpppoT0CF0ly7RSaEGjYzaHvWchYiimNPcUyHTI
      - CLIENT_NAME=Desktop
      - DOMAIN=dashboard-desktop.com
```

## Migrated Configuration Format

The migration creates a `domains.json` file:

```json
{
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
      "enabled": true
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
    "enabled": true
  }
}
```

## Theme Migration

Legacy theme colors are automatically converted:

| Legacy Color | Primary Color | Secondary Color | Accent Colors |
|--------------|---------------|-----------------|---------------|
| `green` (default) | `#059669` | `#10b981` | `["#34d399", "#6ee7b7", "#a7f3d0"]` |
| `blue` | `#3b82f6` | `#60a5fa` | `["#93c5fd", "#bfdbfe", "#dbeafe"]` |
| `red` | `#dc2626` | `#ef4444` | `["#f87171", "#fca5a5", "#fecaca"]` |
| `purple` | `#7c3aed` | `#8b5cf6` | `["#a78bfa", "#c4b5fd", "#ddd6fe"]` |

## Validation Rules

The migration system validates:

- **Required Fields**: `google_sheet_id`, `client_name`
- **Theme Configuration**: Valid colors and structure
- **Cache Settings**: Non-negative timeout values
- **Desktop Compatibility**: Ensures existing Desktop configuration works

## Backup and Recovery

### Automatic Backups

Backups are automatically created in `backend/config_backups/`:

```
config_backups/
├── domains_backup_20231003_143022.json
├── domains_backup_20231003_143045.json
└── domains_backup_20231003_143102.json
```

### Manual Backup

```bash
# Create manual backup
cp backend/domains.json backend/domains.json.backup

# Restore from backup
cp backend/domains.json.backup backend/domains.json
```

## Troubleshooting

### Common Issues

#### 1. Missing Required Fields

**Error**: "Google Sheet ID is required"

**Solution**: Ensure `GOOGLE_SHEET_ID` is set in your legacy configuration.

#### 2. Invalid Configuration

**Error**: "Invalid domain configuration"

**Solution**: Check that all required fields are present and valid.

#### 3. Permission Errors

**Error**: "Permission denied writing domains.json"

**Solution**: Ensure write permissions for the backend directory.

#### 4. Backup Directory Issues

**Error**: "Failed to create backup"

**Solution**: Ensure the `backend/config_backups` directory is writable.

### Manual Migration

If automatic migration fails, you can manually create the configuration:

1. **Create domains.json**:
   ```bash
   cp backend/domains.json.example backend/domains.json
   ```

2. **Edit Configuration**:
   Update the `google_sheet_id`, `client_name`, and other fields.

3. **Validate**:
   ```bash
   python backend/config_migration.py --validate
   ```

### Recovery Steps

If migration causes issues:

1. **Stop the application**
2. **Restore from backup**:
   ```bash
   cp backend/config_backups/domains_backup_YYYYMMDD_HHMMSS.json backend/domains.json
   ```
3. **Restart the application**
4. **Review migration logs**

## Testing Migration

### Test Environment

```bash
# Create test environment
mkdir test_migration
cd test_migration

# Copy migration tools
cp -r ../backend/config_migration.py .
cp -r ../scripts/migrate.sh .

# Create test legacy config
echo "GOOGLE_SHEET_ID=test_sheet_123" > .env
echo "CLIENT_NAME=Test Client" >> .env

# Test migration
python config_migration.py --migrate
```

### Validation Tests

```bash
# Run migration tests
cd backend
python tests/test_config_migration.py
python tests/test_migration_integration.py
```

## Post-Migration Steps

After successful migration:

1. **Test Application**: Verify the dashboard works with new configuration
2. **Add New Domains**: Use the multi-domain system to add new clients
3. **Update Documentation**: Update any deployment scripts or documentation
4. **Remove Legacy Config**: Clean up old environment variables and .env files

## Adding New Domains

After migration, add new domains to `domains.json`:

```json
{
  "domains": {
    "dashboard-desktop.com": { /* existing Desktop config */ },
    "dashboard-newclient.com": {
      "google_sheet_id": "NEW_SHEET_ID_HERE",
      "client_name": "New Client",
      "theme": {
        "primary_color": "#3b82f6",
        "secondary_color": "#60a5fa",
        "accent_colors": ["#93c5fd", "#bfdbfe", "#dbeafe"]
      },
      "cache_timeout": 600,
      "enabled": true
    }
  }
}
```

## Support

For migration issues:

1. **Check Logs**: Review application and migration logs
2. **Run Report**: Use `./scripts/migrate.sh report` for status
3. **Validate Config**: Use `./scripts/migrate.sh validate`
4. **Restore Backup**: Use automatic backups if needed

## Migration Checklist

- [ ] Backup current configuration
- [ ] Run migration report
- [ ] Detect legacy configurations
- [ ] Perform migration
- [ ] Validate Desktop compatibility
- [ ] Test application functionality
- [ ] Update deployment scripts
- [ ] Clean up legacy configuration files
- [ ] Document new domain addition process
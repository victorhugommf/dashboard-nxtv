# Dynamic Theme System

This document describes the dynamic theme system implemented for the multi-domain dashboard.

## Overview

The theme system allows each domain to have its own visual identity including:
- Primary and secondary colors
- Accent colors for charts and UI elements
- Client branding (name, logo, favicon)
- Dynamic CSS variables for consistent styling

## Architecture

### Backend Components

1. **ThemeManager** (`backend/theme_manager.py`)
   - Generates CSS variables from theme configuration
   - Validates color formats
   - Provides API-ready theme data

2. **Theme API Endpoint** (`/api/theme/config`)
   - Returns complete theme configuration for current domain
   - Includes CSS variables, branding, and theme colors
   - Supports fallback to default configuration

### Frontend Components

1. **useTheme Hook** (`frontend/src/hooks/useTheme.js`)
   - Fetches theme configuration from backend
   - Applies CSS variables to document
   - Handles loading states and errors
   - Provides fallback theme

2. **ThemeContext** (`frontend/src/contexts/ThemeContext.js`)
   - React context for theme state management
   - Provides theme data to all components

3. **ThemeErrorBoundary** (`frontend/src/components/ThemeErrorBoundary.js`)
   - Catches theme-related errors
   - Provides graceful error handling

## Usage

### CSS Classes

The system provides CSS classes that use dynamic variables:

```css
/* Text colors */
.theme-primary { color: var(--color-primary); }
.theme-secondary { color: var(--color-secondary); }

/* Background colors */
.theme-bg-primary { background-color: var(--color-primary); }
.theme-bg-primary-light { background-color: var(--color-primary-bg); }

/* Buttons */
.theme-btn-primary { /* Primary button styling */ }
.theme-btn-secondary { /* Secondary button styling */ }

/* Borders */
.theme-border-primary { border-color: var(--color-primary); }
```

### React Components

```jsx
import { useThemeContext } from './contexts/ThemeContext';

function MyComponent() {
  const { 
    getThemeColors, 
    getClientName, 
    loading, 
    error 
  } = useThemeContext();

  const colors = getThemeColors();
  const clientName = getClientName();

  if (loading) return <div>Loading theme...</div>;
  if (error) return <div>Theme error: {error}</div>;

  return (
    <div>
      <h1 className="theme-primary">{clientName} Dashboard</h1>
      <button className="theme-btn-primary">Action</button>
    </div>
  );
}
```

### Chart Colors

Charts automatically use theme colors:

```jsx
// Colors are dynamically applied from theme
const colors = getThemeColors();
<AreaChart data={data}>
  <Area stroke={colors.primary} fill={colors.secondary} />
</AreaChart>
```

## Configuration

### Domain Configuration

Each domain can specify its theme in `domains.json`:

```json
{
  "domains": {
    "client-domain.com": {
      "client_name": "Client Name",
      "theme": {
        "primary_color": "#059669",
        "secondary_color": "#10b981",
        "accent_colors": ["#34d399", "#6ee7b7", "#a7f3d0"]
      }
    }
  }
}
```

### CSS Variables Generated

The system automatically generates CSS variables:

```css
:root {
  --color-primary: #059669;
  --color-secondary: #10b981;
  --color-accent-1: #34d399;
  --color-accent-2: #6ee7b7;
  --color-accent-3: #a7f3d0;
  --color-primary-hover: #059669dd;
  --color-primary-active: #059669bb;
  --color-secondary-hover: #10b981dd;
  --color-secondary-active: #10b981bb;
  --color-primary-bg: #0596691a;
  --color-secondary-bg: #10b9811a;
}
```

## Error Handling

The system includes comprehensive error handling:

1. **Network Errors**: Fallback to default theme
2. **Invalid Configuration**: Validation with specific error messages
3. **Missing Theme**: Graceful degradation to default colors
4. **Component Errors**: Error boundary prevents app crashes

## Testing

Run theme integration tests:

```bash
python backend/test_theme_integration.py
```

Test components include:
- Theme manager functionality
- API endpoint responses
- Color validation
- Default configuration fallback
- CSS variable generation

## Modes

### Normal Mode
- Theme loaded from domain configuration
- Full dynamic theming active

### Legacy Mode
- Using default configuration due to missing domain config
- Backward compatibility maintained

### Fallback Mode
- Theme loading failed, using hardcoded defaults
- Application continues to function with basic styling

## Browser Support

The theme system uses CSS custom properties (variables) which are supported in:
- Chrome 49+
- Firefox 31+
- Safari 9.1+
- Edge 16+

For older browsers, the default CSS values will be used as fallbacks.
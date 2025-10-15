#!/usr/bin/env python3
"""
Theme Manager Module
Handles dynamic theme application and CSS variable generation for multi-domain support
"""

from typing import Dict, Any, Optional
from domain_config import DomainConfig, ThemeConfig


class ThemeManager:
    """Manager for domain-specific themes and branding"""
    
    def __init__(self):
        """Initialize ThemeManager"""
        pass
    
    def get_theme_config(self, domain_config: DomainConfig) -> Dict[str, Any]:
        """
        Get complete theme configuration for a domain
        
        Args:
            domain_config: Domain configuration containing theme settings
            
        Returns:
            Dictionary containing complete theme configuration
        """
        theme = domain_config.theme
        
        return {
            'primary_color': theme.primary_color,
            'secondary_color': theme.secondary_color,
            'accent_colors': theme.accent_colors,
            'logo_url': theme.logo_url,
            'favicon_url': theme.favicon_url,
            'client_name': domain_config.client_name,
            'domain': domain_config.domain
        }
    
    def generate_css_variables(self, theme_config: Dict[str, Any]) -> str:
        """
        Generate CSS variables string for domain-specific colors
        
        Args:
            theme_config: Theme configuration dictionary
            
        Returns:
            CSS variables string ready for injection into HTML
        """
        css_vars = []
        
        # Primary and secondary colors
        css_vars.append(f"--color-primary: {theme_config['primary_color']};")
        css_vars.append(f"--color-secondary: {theme_config['secondary_color']};")
        
        # Accent colors with indexed variables
        accent_colors = theme_config.get('accent_colors', [])
        for i, color in enumerate(accent_colors):
            css_vars.append(f"--color-accent-{i + 1}: {color};")
        
        # Generate additional color variations for primary and secondary
        css_vars.extend(self._generate_color_variations(theme_config))
        
        # Wrap in :root selector
        css_content = ":root {\n  " + "\n  ".join(css_vars) + "\n}"
        
        return css_content
    
    def _generate_color_variations(self, theme_config: Dict[str, Any]) -> list:
        """
        Generate color variations for better theming support
        
        Args:
            theme_config: Theme configuration dictionary
            
        Returns:
            List of CSS variable strings for color variations
        """
        variations = []
        
        # For now, we'll create some basic variations
        # In a real implementation, you might want to use a color manipulation library
        primary = theme_config['primary_color']
        secondary = theme_config['secondary_color']
        
        # Create hover and active variations (simplified approach)
        variations.append(f"--color-primary-hover: {primary}dd;")  # Add transparency
        variations.append(f"--color-primary-active: {primary}bb;")
        variations.append(f"--color-secondary-hover: {secondary}dd;")
        variations.append(f"--color-secondary-active: {secondary}bb;")
        
        # Background variations
        variations.append(f"--color-primary-bg: {primary}1a;")  # Very light background
        variations.append(f"--color-secondary-bg: {secondary}1a;")
        
        return variations
    
    def get_client_branding(self, domain_config: DomainConfig) -> Dict[str, Any]:
        """
        Get client branding configuration
        
        Args:
            domain_config: Domain configuration containing branding settings
            
        Returns:
            Dictionary containing client branding information
        """
        theme = domain_config.theme
        
        branding = {
            'client_name': domain_config.client_name,
            'domain': domain_config.domain,
            'logo_url': theme.logo_url,
            'favicon_url': theme.favicon_url,
            'primary_color': theme.primary_color,
            'secondary_color': theme.secondary_color
        }
        
        # Add custom branding settings if available
        custom_branding = domain_config.custom_settings.get('branding', {})
        branding.update(custom_branding)
        
        return branding
    
    def generate_theme_css_file(self, domain_config: DomainConfig) -> str:
        """
        Generate complete CSS file content for a domain theme
        
        Args:
            domain_config: Domain configuration
            
        Returns:
            Complete CSS file content as string
        """
        theme_config = self.get_theme_config(domain_config)
        css_variables = self.generate_css_variables(theme_config)
        
        # Add additional CSS rules that use the variables
        additional_css = self._generate_component_styles()
        
        return f"{css_variables}\n\n{additional_css}"
    
    def _generate_component_styles(self) -> str:
        """
        Generate CSS styles for components using the CSS variables
        
        Returns:
            CSS styles string
        """
        return """
/* Component styles using theme variables */
.btn-primary {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
}

.btn-primary:hover {
  background-color: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

.btn-primary:active {
  background-color: var(--color-primary-active);
  border-color: var(--color-primary-active);
}

.btn-secondary {
  background-color: var(--color-secondary);
  border-color: var(--color-secondary);
}

.btn-secondary:hover {
  background-color: var(--color-secondary-hover);
  border-color: var(--color-secondary-hover);
}

.text-primary {
  color: var(--color-primary);
}

.text-secondary {
  color: var(--color-secondary);
}

.bg-primary {
  background-color: var(--color-primary-bg);
}

.bg-secondary {
  background-color: var(--color-secondary-bg);
}

.border-primary {
  border-color: var(--color-primary);
}

.border-secondary {
  border-color: var(--color-secondary);
}
"""
    
    def validate_theme_config(self, theme_config: Dict[str, Any]) -> list:
        """
        Validate theme configuration
        
        Args:
            theme_config: Theme configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        required_fields = ['primary_color', 'secondary_color', 'accent_colors']
        for field in required_fields:
            if field not in theme_config:
                errors.append(f"Missing required field: {field}")
        
        # Validate color format (basic hex color validation)
        color_fields = ['primary_color', 'secondary_color']
        for field in color_fields:
            if field in theme_config:
                color = theme_config[field]
                if not self._is_valid_hex_color(color):
                    errors.append(f"Invalid hex color format for {field}: {color}")
        
        # Validate accent colors
        if 'accent_colors' in theme_config:
            accent_colors = theme_config['accent_colors']
            if not isinstance(accent_colors, list):
                errors.append("accent_colors must be a list")
            elif len(accent_colors) == 0:
                errors.append("At least one accent color is required")
            else:
                for i, color in enumerate(accent_colors):
                    if not self._is_valid_hex_color(color):
                        errors.append(f"Invalid hex color format for accent_colors[{i}]: {color}")
        
        return errors
    
    def _is_valid_hex_color(self, color: str) -> bool:
        """
        Validate if a string is a valid hex color
        
        Args:
            color: Color string to validate
            
        Returns:
            True if valid hex color, False otherwise
        """
        if not isinstance(color, str):
            return False
        
        # Remove # if present
        color = color.lstrip('#')
        
        # Check if it's 3 or 6 characters and all hex digits
        if len(color) not in [3, 6]:
            return False
        
        try:
            int(color, 16)
            return True
        except ValueError:
            return False
    
    def get_theme_for_api(self, domain_config: DomainConfig) -> Dict[str, Any]:
        """
        Get theme configuration formatted for API response
        
        Args:
            domain_config: Domain configuration
            
        Returns:
            Theme configuration suitable for API response
        """
        theme_config = self.get_theme_config(domain_config)
        branding = self.get_client_branding(domain_config)
        css_variables = self.generate_css_variables(theme_config)
        
        return {
            'theme': theme_config,
            'branding': branding,
            'css_variables': css_variables,
            'css_content': self.generate_theme_css_file(domain_config)
        }
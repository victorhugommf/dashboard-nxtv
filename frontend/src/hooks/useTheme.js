import { useState, useEffect } from 'react';
import { buildApiUrl, getDomainHeaders } from '../config/api';

/**
 * Custom hook for managing dynamic themes
 * Fetches theme configuration from backend and applies CSS variables
 */
export const useTheme = () => {
  const [themeConfig, setThemeConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchThemeConfig = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get domain parameter for multi-domain support
      const urlParams = new URLSearchParams(window.location.search);
      const domain = urlParams.get('domain');
      const domainParam = domain ? `?domain=${encodeURIComponent(domain)}` : '';

      const response = await fetch(buildApiUrl(`/api/theme/config${domainParam}`));

      if (!response.ok) {
        throw new Error(`Failed to fetch theme config: ${response.status}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to load theme configuration');
      }

      setThemeConfig(data);

      // Apply CSS variables to document root
      if (data.css_variables) {
        applyCSSVariables(data.css_variables);
      }

    } catch (err) {
      console.error('Error fetching theme config:', err);
      setError(err.message);

      // Apply fallback theme
      applyFallbackTheme();
    } finally {
      setLoading(false);
    }
  };

  const applyCSSVariables = (cssVariables) => {
    try {
      // Remove existing theme style element if it exists
      const existingStyle = document.getElementById('dynamic-theme-styles');
      if (existingStyle) {
        existingStyle.remove();
      }

      // Create new style element
      const styleElement = document.createElement('style');
      styleElement.id = 'dynamic-theme-styles';
      styleElement.textContent = cssVariables;

      // Append to head
      document.head.appendChild(styleElement);

      console.log('Theme CSS variables applied successfully');
    } catch (err) {
      console.error('Error applying CSS variables:', err);
    }
  };

  const applyFallbackTheme = () => {
    const fallbackCSS = `
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
    `;

    applyCSSVariables(fallbackCSS);

    // Set fallback theme config
    setThemeConfig({
      success: true,
      domain: 'fallback',
      client_name: 'Desktop',
      theme: {
        primary_color: '#059669',
        secondary_color: '#10b981',
        accent_colors: ['#34d399', '#6ee7b7', '#a7f3d0'],
        client_name: 'Desktop'
      },
      branding: {
        client_name: 'Desktop',
        primary_color: '#059669',
        secondary_color: '#10b981'
      },
      fallback_mode: true
    });
  };

  const getThemeColors = () => {
    if (!themeConfig?.theme) {
      return {
        primary: '#059669',
        secondary: '#10b981',
        accents: ['#34d399', '#6ee7b7', '#a7f3d0']
      };
    }

    return {
      primary: themeConfig.theme.primary_color,
      secondary: themeConfig.theme.secondary_color,
      accents: themeConfig.theme.accent_colors || []
    };
  };

  const getClientName = () => {
    return themeConfig?.client_name || themeConfig?.branding?.client_name || 'Desktop';
  };

  const retryFetch = () => {
    fetchThemeConfig();
  };

  useEffect(() => {
    fetchThemeConfig();
  }, []);

  return {
    themeConfig,
    loading,
    error,
    getThemeColors,
    getClientName,
    retryFetch,
    isLegacyMode: themeConfig?.legacy_mode || false,
    isFallbackMode: themeConfig?.fallback_mode || false
  };
};

export default useTheme;
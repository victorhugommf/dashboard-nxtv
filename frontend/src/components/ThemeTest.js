import React from 'react';
import { useThemeContext } from '../contexts/ThemeContext';

/**
 * Test component to verify theme functionality
 * This can be used for debugging and testing theme changes
 */
const ThemeTest = () => {
  const {
    themeConfig,
    loading,
    error,
    getThemeColors,
    getClientName,
    isLegacyMode,
    isFallbackMode
  } = useThemeContext();

  const colors = getThemeColors();

  if (loading) {
    return (
      <div className="p-4 bg-gray-100 rounded">
        <p>Loading theme...</p>
      </div>
    );
  }

  if (error && !isFallbackMode) {
    return (
      <div className="p-4 bg-red-100 rounded">
        <p className="text-red-600">Theme Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-white rounded shadow">
      <h3 className="text-lg font-semibold mb-4">Theme Configuration</h3>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <strong>Client:</strong> {getClientName()}
        </div>
        <div>
          <strong>Domain:</strong> {themeConfig?.domain || 'unknown'}
        </div>
        <div>
          <strong>Legacy Mode:</strong> {isLegacyMode ? 'Yes' : 'No'}
        </div>
        <div>
          <strong>Fallback Mode:</strong> {isFallbackMode ? 'Yes' : 'No'}
        </div>
      </div>

      <div className="mb-4">
        <h4 className="font-semibold mb-2">Colors:</h4>
        <div className="flex space-x-4">
          <div className="flex items-center space-x-2">
            <div
              className="w-6 h-6 rounded border"
              style={{ backgroundColor: colors.primary }}
            ></div>
            <span className="text-sm">Primary: {colors.primary}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div
              className="w-6 h-6 rounded border"
              style={{ backgroundColor: colors.secondary }}
            ></div>
            <span className="text-sm">Secondary: {colors.secondary}</span>
          </div>
        </div>
      </div>

      <div className="mb-4">
        <h4 className="font-semibold mb-2">Accent Colors:</h4>
        <div className="flex space-x-2">
          {colors.accents.map((color, index) => (
            <div key={index} className="flex items-center space-x-1">
              <div
                className="w-4 h-4 rounded border"
                style={{ backgroundColor: color }}
              ></div>
              <span className="text-xs">{color}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <h4 className="font-semibold">Theme Classes Test:</h4>
        <div className="flex space-x-2">
          <button className="theme-btn-primary px-3 py-1 rounded text-sm">
            Primary Button
          </button>
          <button className="theme-btn-secondary px-3 py-1 rounded text-sm">
            Secondary Button
          </button>
        </div>
        <div className="flex space-x-2">
          <span className="theme-primary font-semibold">Primary Text</span>
          <span className="theme-secondary font-semibold">Secondary Text</span>
        </div>
        <div className="flex space-x-2">
          <div className="theme-bg-primary-light theme-primary px-2 py-1 rounded text-sm">
            Primary Background
          </div>
          <div className="theme-bg-secondary-light theme-secondary px-2 py-1 rounded text-sm">
            Secondary Background
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThemeTest;
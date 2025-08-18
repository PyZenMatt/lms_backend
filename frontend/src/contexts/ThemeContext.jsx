/**
 * 🌙 Dark Theme Context for SchoolPlatform
 *
 * Provides comprehensive dark theme support with:
 * - System preference detection
 * - Manual theme switching
 * - Local storage persistence
 * - Component-level theme awareness
 */

import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  const [isDark, setIsDark] = useState(false);
  const [systemPreference, setSystemPreference] = useState('light');

  // Initialize theme on component mount
  useEffect(() => {
    initializeTheme();
    setupSystemPreferenceListener();
  }, []);

  // Apply theme changes to DOM
  useEffect(() => {
    applyTheme(isDark);
  }, [isDark]);

  /**
   * Initialize theme from localStorage or system preference
   */
  const initializeTheme = () => {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('schoolplatform-theme');

    // Detect system preference
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setSystemPreference(systemDark ? 'dark' : 'light');

    if (savedTheme) {
      setIsDark(savedTheme === 'dark');
    } else {
      // Use system preference if no saved preference
      setIsDark(systemDark);
    }
  };

  /**
   * Setup listener for system preference changes
   */
  const setupSystemPreferenceListener = () => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = (e) => {
      setSystemPreference(e.matches ? 'dark' : 'light');

      // Only auto-switch if user hasn't manually set a preference
      if (!localStorage.getItem('schoolplatform-theme')) {
        setIsDark(e.matches);
      }
    };

    mediaQuery.addEventListener('change', handleChange);

    return () => mediaQuery.removeEventListener('change', handleChange);
  };

  /**
   * Apply theme to DOM
   */
  const applyTheme = (dark) => {
    const root = document.documentElement;
    const body = document.body;

    if (dark) {
      // Add dark mode classes
      body.classList.add('dark-mode', 'dark-layout');
      body.classList.remove('light-mode');

      // Set CSS custom properties for dark theme
      root.style.setProperty('--bs-body-bg', '#1a1d21');
      root.style.setProperty('--bs-body-color', '#adb7be');
  root.style.setProperty('--bs-bg-card text-card-foreground rounded-lg border border-border shadow-sm-bg', '#2d3748');
      root.style.setProperty('--bs-navbar-bg', '#1a202c');
      root.style.setProperty('--bs-sidebar-bg', '#2d3748');
      root.style.setProperty('--bs-primary', 'var(--primary)');
      root.style.setProperty('--bs-secondary', '#4a5568');
      root.style.setProperty('--bs-success', '#38a169');
      root.style.setProperty('--bs-warning', '#ed8936');
      root.style.setProperty('--bs-danger', 'var(--destructive)');
      root.style.setProperty('--bs-info', '#3182ce');
      root.style.setProperty('--bs-light', '#4a5568');
      root.style.setProperty('--bs-dark', 'var(--border)');
      root.style.setProperty('--bs-border-color', 'hsl(var(--background) / 0.125)');
      root.style.setProperty('--bs-text-muted', '#a0aec0');

      // Update meta theme-color for mobile browsers
      updateMetaThemeColor('#1a1d21');
    } else {
      // Add light mode classes
      body.classList.add('light-mode');
      body.classList.remove('dark-mode', 'dark-layout');

      // Reset CSS custom properties to default light theme
      root.style.setProperty('--bs-body-bg', 'var(--background)');
      root.style.setProperty('--bs-body-color', '#888');
  root.style.setProperty('--bs-bg-card text-card-foreground rounded-lg border border-border shadow-sm-bg', 'var(--background)');
      root.style.setProperty('--bs-navbar-bg', 'var(--background)');
      root.style.setProperty('--bs-sidebar-bg', 'var(--background)');
      root.style.setProperty('--bs-primary', 'var(--primary)');
      root.style.setProperty('--bs-secondary', '#748892');
      root.style.setProperty('--bs-success', 'color-mix(in srgb, var(--success) 75%, cyan)');
      root.style.setProperty('--bs-warning', '#f4c22b');
      root.style.setProperty('--bs-danger', '#f44236');
      root.style.setProperty('--bs-info', 'var(--info)');
      root.style.setProperty('--bs-light', '#f2f2f2');
      root.style.setProperty('--bs-dark', '#37474f');
      root.style.setProperty('--bs-border-color', '#eaeaea');
      root.style.setProperty('--bs-text-muted', '#888');

      // Update meta theme-color for mobile browsers
      updateMetaThemeColor('var(--background)');
    }
  };

  /**
   * Update meta theme-color for mobile browsers
   */
  const updateMetaThemeColor = (color) => {
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', color);
    }
  };

  /**
   * Toggle theme and save preference
   */
  const toggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    localStorage.setItem('schoolplatform-theme', newTheme ? 'dark' : 'light');
  };

  /**
   * Set specific theme
   */
  const setTheme = (theme) => {
    const dark = theme === 'dark';
    setIsDark(dark);
    localStorage.setItem('schoolplatform-theme', theme);
  };

  /**
   * Reset to system preference
   */
  const resetToSystemPreference = () => {
    localStorage.removeItem('schoolplatform-theme');
    setIsDark(systemPreference === 'dark');
  };

  /**
   * Get current theme name
   */
  const getThemeName = () => {
    return isDark ? 'dark' : 'light';
  };

  /**
   * Check if theme is manually set
   */
  const isManuallySet = () => {
    return localStorage.getItem('schoolplatform-theme') !== null;
  };

  /**
   * Get theme colors for dynamic styling
   */
  const getThemeColors = () => {
    if (isDark) {
      return {
        primary: 'var(--primary)',
        secondary: '#4a5568',
        success: '#38a169',
        warning: '#ed8936',
        danger: 'var(--destructive)',
        info: '#3182ce',
        light: '#4a5568',
        dark: 'var(--border)',
        background: '#1a1d21',
        surface: '#2d3748',
        text: '#adb7be',
        textMuted: '#a0aec0',
        border: 'hsl(var(--background) / 0.125)'
      };
    } else {
      return {
        primary: 'var(--primary)',
        secondary: '#748892',
        success: 'color-mix(in srgb, var(--success) 75%, cyan)',
        warning: '#f4c22b',
        danger: '#f44236',
        info: 'var(--info)',
        light: '#f2f2f2',
        dark: '#37474f',
        background: 'var(--background)',
        surface: 'var(--background)',
        text: '#888',
        textMuted: '#888',
        border: '#eaeaea'
      };
    }
  };

  const value = {
    isDark,
    systemPreference,
    isManuallySet,
    toggleTheme,
    setTheme,
    resetToSystemPreference,
    getThemeName,
    getThemeColors
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export default ThemeContext;

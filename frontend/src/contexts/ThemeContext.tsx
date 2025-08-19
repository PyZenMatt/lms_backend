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
      root.style.setProperty('--bs-body-bg', 'hsl(var(--foreground))');
      root.style.setProperty('--bs-body-color', 'hsl(var(--muted-foreground))');
  root.style.setProperty('--bs-bg-card text-card-foreground rounded-lg border border-border shadow-sm-bg', 'hsl(var(--muted-foreground))');
      root.style.setProperty('--bs-navbar-bg', 'hsl(var(--foreground))');
      root.style.setProperty('--bs-sidebar-bg', 'hsl(var(--muted-foreground))');
      root.style.setProperty('--bs-primary', 'var(--primary)');
      root.style.setProperty('--bs-secondary', 'hsl(var(--muted-foreground))');
      root.style.setProperty('--bs-success', 'hsl(var(--success))');
      root.style.setProperty('--bs-warning', 'hsl(var(--warning-600))');
      root.style.setProperty('--bs-danger', 'var(--destructive)');
      root.style.setProperty('--bs-info', 'hsl(var(--info))');
      root.style.setProperty('--bs-light', 'hsl(var(--muted-foreground))');
      root.style.setProperty('--bs-dark', 'var(--border)');
      root.style.setProperty('--bs-border-color', 'hsl(var(--background) / 0.125)');
      root.style.setProperty('--bs-text-muted', 'hsl(var(--muted-foreground))');

      // Update meta theme-color for mobile browsers
      updateMetaThemeColor('hsl(var(--foreground))');
    } else {
      // Add light mode classes
      body.classList.add('light-mode');
      body.classList.remove('dark-mode', 'dark-layout');

      // Reset CSS custom properties to default light theme
      root.style.setProperty('--bs-body-bg', 'var(--background)');
      root.style.setProperty('--bs-body-color', 'hsl(var(--muted-foreground))');
  root.style.setProperty('--bs-bg-card text-card-foreground rounded-lg border border-border shadow-sm-bg', 'var(--background)');
      root.style.setProperty('--bs-navbar-bg', 'var(--background)');
      root.style.setProperty('--bs-sidebar-bg', 'var(--background)');
      root.style.setProperty('--bs-primary', 'var(--primary)');
      root.style.setProperty('--bs-secondary', 'hsl(var(--muted-foreground))');
      root.style.setProperty('--bs-success', 'color-mix(in srgb, var(--success) 75%, cyan)');
      root.style.setProperty('--bs-warning', 'hsl(var(--warning))');
      root.style.setProperty('--bs-danger', 'hsl(var(--destructive))');
      root.style.setProperty('--bs-info', 'var(--info)');
      root.style.setProperty('--bs-light', 'hsl(var(--muted))');
      root.style.setProperty('--bs-dark', 'hsl(var(--foreground))');
      root.style.setProperty('--bs-border-color', 'hsl(var(--muted))');
      root.style.setProperty('--bs-text-muted', 'hsl(var(--muted-foreground))');

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
        secondary: 'hsl(var(--muted-foreground))',
        success: 'hsl(var(--success))',
        warning: 'hsl(var(--warning-600))',
        danger: 'var(--destructive)',
        info: 'hsl(var(--info))',
        light: 'hsl(var(--muted-foreground))',
        dark: 'var(--border)',
        background: 'hsl(var(--foreground))',
        surface: 'hsl(var(--muted-foreground))',
        text: 'hsl(var(--muted-foreground))',
        textMuted: 'hsl(var(--muted-foreground))',
        border: 'hsl(var(--background) / 0.125)'
      };
    } else {
      return {
        primary: 'var(--primary)',
        secondary: 'hsl(var(--muted-foreground))',
        success: 'color-mix(in srgb, var(--success) 75%, cyan)',
        warning: 'hsl(var(--warning))',
        danger: 'hsl(var(--destructive))',
        info: 'var(--info)',
        light: 'hsl(var(--muted))',
        dark: 'hsl(var(--foreground))',
        background: 'var(--background)',
        surface: 'var(--background)',
        text: 'hsl(var(--muted-foreground))',
        textMuted: 'hsl(var(--muted-foreground))',
        border: 'hsl(var(--muted))'
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

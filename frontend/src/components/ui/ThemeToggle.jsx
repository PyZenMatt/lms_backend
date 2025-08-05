/**
 * 🌙 Theme Toggle Component for SchoolPlatform
 * 
 * Provides an elegant theme switching interface with:
 * - Sun/moon icon animation
 * - Smooth transitions
 * - Accessibility support
 * - System preference detection
 */

import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import './ThemeToggle.css';

const ThemeToggle = ({ className = '', size = 'md', showLabel = false }) => {
  const { isDark, toggleTheme, systemPreference, isManuallySet } = useTheme();

  const sizeClasses = {
    sm: 'theme-toggle-sm',
    md: 'theme-toggle-md',
    lg: 'theme-toggle-lg'
  };

  return (
    <div className={`theme-toggle-container ${className}`}>
      <button
        type="button"
        className={`theme-toggle ${sizeClasses[size]} ${isDark ? 'dark' : 'light'}`}
        onClick={toggleTheme}
        aria-label={`Switch to ${isDark ? 'light' : 'dark'} theme`}
        title={`Currently using ${isDark ? 'dark' : 'light'} theme. Click to switch.`}
      >
        <div className="theme-toggle-track">
          <div className="theme-toggle-thumb">
            <div className="theme-icon">
              {isDark ? (
                // Moon Icon
                <svg
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="theme-icon-svg moon-icon"
                >
                  <path d="M21.64,13a1,1,0,0,0-1.05-.14,8.05,8.05,0,0,1-3.37.73A8.15,8.15,0,0,1,9.08,5.49a8.59,8.59,0,0,1,.25-2A1,1,0,0,0,8,2.36,10.14,10.14,0,1,0,22,14.05,1,1,0,0,0,21.64,13Zm-9.5,6.69A8.14,8.14,0,0,1,7.08,5.22v.27A10.15,10.15,0,0,0,17.22,15.63a9.79,9.79,0,0,0,2.1-.22A8.11,8.11,0,0,1,12.14,19.73Z"/>
                </svg>
              ) : (
                // Sun Icon
                <svg
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="theme-icon-svg sun-icon"
                >
                  <path d="M12,18.5A6.5,6.5,0,1,1,18.5,12,6.51,6.51,0,0,1,12,18.5ZM12,7A5,5,0,1,0,17,12,5,5,0,0,0,12,7Z"/>
                  <path d="M12,1a1,1,0,0,0-1,1V4a1,1,0,0,0,2,0V2A1,1,0,0,0,12,1Z"/>
                  <path d="M12,20a1,1,0,0,0-1,1v2a1,1,0,0,0,2,0V21A1,1,0,0,0,12,20Z"/>
                  <path d="M6.34,7.76A1,1,0,0,0,4.93,6.34L3.51,7.76a1,1,0,0,0,0,1.41,1,1,0,0,0,1.41,0L6.34,7.76Z"/>
                  <path d="M19.07,17.66a1,1,0,0,0-1.41,0l-1.42,1.42a1,1,0,0,0,0,1.41,1,1,0,0,0,1.41,0l1.42-1.42A1,1,0,0,0,19.07,17.66Z"/>
                  <path d="M23,11H21a1,1,0,0,0,0,2h2a1,1,0,0,0,0-2Z"/>
                  <path d="M3,11H1a1,1,0,0,0,0,2H3a1,1,0,0,0,0-2Z"/>
                  <path d="M18.66,6.34a1,1,0,0,0,0-1.41L17.24,3.51a1,1,0,0,0-1.41,0,1,1,0,0,0,0,1.41l1.42,1.42A1,1,0,0,0,18.66,6.34Z"/>
                  <path d="M8.17,17.66,6.75,19.07a1,1,0,0,0,0,1.41,1,1,0,0,0,1.41,0l1.42-1.42a1,1,0,0,0,0-1.41A1,1,0,0,0,8.17,17.66Z"/>
                </svg>
              )}
            </div>
          </div>
        </div>
      </button>
      
      {showLabel && (
        <div className="theme-toggle-label">
          <span className="theme-toggle-text">
            {isDark ? 'Dark' : 'Light'} Theme
          </span>
          {!isManuallySet() && (
            <small className="theme-toggle-auto">
              (Following system: {systemPreference})
            </small>
          )}
        </div>
      )}
    </div>
  );
};

export default ThemeToggle;

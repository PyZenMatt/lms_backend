import React from 'react';

export const Button = ({ 
  children, 
  className = '', 
  variant = 'primary',
  size = 'medium',
  disabled = false,
  type = 'button',
  ...props 
}) => {
  const baseClasses = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none';
  
  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    outline: 'border border-gray-300 bg-transparent text-gray-700 hover:bg-gray-50 focus:ring-gray-500',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-500',
    destructive: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
  };
  
  const sizes = {
    small: 'h-8 px-3 text-sm',
    medium: 'h-10 px-4 py-2',
    large: 'h-12 px-6 text-lg'
  };
  
  const variantClasses = variants[variant] || variants.primary;
  const sizeClasses = sizes[size] || sizes.medium;
  
  return (
    <button
      type={type}
      className={`${baseClasses} ${variantClasses} ${sizeClasses} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};

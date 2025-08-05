import React from 'react';
import { Toast, ToastContainer } from 'react-bootstrap';

const CustomToast = ({ show, onClose, variant = 'success', title, message, delay = 5000 }) => {
  const getVariantClasses = (variant) => {
    switch(variant) {
      case 'success':
        return { header: 'bg-success text-white', body: 'text-success' };
      case 'error':
        return { header: 'bg-danger text-white', body: 'text-danger' };
      case 'warning':
        return { header: 'bg-warning text-dark', body: 'text-warning' };
      case 'info':
        return { header: 'bg-info text-white', body: 'text-info' };
      default:
        return { header: 'bg-primary text-white', body: 'text-primary' };
    }
  };

  const variantClasses = getVariantClasses(variant);

  return (
    <ToastContainer position="top-end" className="p-3">
      <Toast show={show} onClose={onClose} delay={delay} autohide>
        <Toast.Header className={variantClasses.header}>
          <strong className="me-auto">
            {variant === 'success' && '✅'} 
            {variant === 'error' && '❌'} 
            {variant === 'warning' && '⚠️'} 
            {variant === 'info' && 'ℹ️'} 
            {title}
          </strong>
        </Toast.Header>
        <Toast.Body className={variantClasses.body}>
          {message}
        </Toast.Body>
      </Toast>
    </ToastContainer>
  );
};

export default CustomToast;

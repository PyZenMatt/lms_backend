import React from 'react';
import { ProgressBar } from 'react-bootstrap';

const ProgressIndicator = ({ 
  progress, 
  variant = 'primary', 
  showPercentage = true, 
  label = 'Completamento form',
  animated = true 
}) => {
  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-2">
        <small className="text-muted fw-semibold">{label}</small>
        {showPercentage && (
          <small className="text-muted">
            <span className={`fw-bold ${progress >= 100 ? 'text-success' : ''}`}>
              {progress}%
            </span>
          </small>
        )}
      </div>
      <ProgressBar 
        now={progress} 
        variant={progress >= 100 ? 'success' : variant}
        animated={animated}
      />
      {progress >= 100 && (
        <div className="mt-2">
          <small className="text-success">
            <i className="bi bi-check-circle-fill me-1"></i>
            Form completato! ✨
          </small>
        </div>
      )}
    </div>
  );
};

export default ProgressIndicator;

import React from 'react';
import { Card } from 'react-bootstrap';

const StatWidget = ({ 
  title, 
  value, 
  icon, 
  trend, 
  changeValue, 
  trendValue, 
  color = 'progress-c-theme',
  subtitle,
  gradientFrom,
  gradientTo
}) => {
  const getTrendIcon = () => {
    if (trend === 'up') return 'icon-arrow-up text-c-green';
    if (trend === 'down') return 'icon-arrow-down text-c-red';
    return 'icon-minus text-c-yellow';
  };

  // Use either changeValue or trendValue for compatibility
  const displayValue = changeValue || trendValue;
  
  // Remove percentage sign if it's already included in changeValue
  const numericValue = displayValue && typeof displayValue === 'string' && displayValue.includes('%') 
    ? parseInt(displayValue.replace('%', ''), 10) 
    : displayValue;

  return (
    <Card>
      <Card.Body>
        <h6 className="mb-4">{title}</h6>
        <div className="row d-flex align-items-center">
          <div className="col-9">
            <h3 className="f-w-300 d-flex align-items-center m-b-0">
              {icon && <i className={`feather icon-${icon} f-30 m-r-5`} />}
              {value}
            </h3>
            {subtitle && <p className="mb-0 text-muted">{subtitle}</p>}
          </div>
          {displayValue && (
            <div className="col-3 text-end">
              <p className="m-b-0 d-flex align-items-center justify-content-end">
                {trend && <i className={`feather ${getTrendIcon()} me-2`}></i>}
                {displayValue}
              </p>
            </div>
          )}
        </div>
        {numericValue && typeof numericValue === 'number' && (
          <div className="progress m-t-30" style={{ height: '7px' }}>
            <div
              className={`progress-bar ${color}`}
              role="progressbar"
              style={{ width: `${numericValue}%` }}
              aria-valuenow={numericValue}
              aria-valuemin="0"
              aria-valuemax="100"
            />
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

export default StatWidget;

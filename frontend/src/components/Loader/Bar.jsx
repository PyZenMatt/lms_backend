import PropTypes from 'prop-types';
import React from 'react';
import './Loader.css';

const Bar = ({ animationDuration, progress }) => {
  return (
    <div className="loader-bar">
      <div 
        className="loader-bar-progress"
        style={{
          marginLeft: `${(-1 + progress) * 100}%`,
          transition: `margin-left ${animationDuration}ms linear`
        }}
      />
    </div>
  );
};

Bar.propTypes = {
  animationDuration: PropTypes.number,
  progress: PropTypes.number
};

export default Bar;

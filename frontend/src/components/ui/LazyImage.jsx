import React, { useState, useRef, useEffect, memo } from 'react';
import '../../assets/css/components/LazyImage.css';

/**
 * Optimized lazy-loading image component
 * Reduces initial page load time and improves performance
 */
const LazyImage = memo(({ src, alt, placeholder, className, style, onLoad, onError, ...props }) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      {
        rootMargin: '50px' // Load images 50px before they come into view
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, []);

  const handleLoad = (e) => {
    setIsLoaded(true);
    onLoad?.(e);
  };

  const handleError = (e) => {
    setHasError(true);
    onError?.(e);
  };

  const shouldShowPlaceholder = !isLoaded && !hasError;
  const shouldShowImage = isInView && !hasError;

  return (
    <div 
      ref={imgRef}
      className={`lazy-image-container ${className || ''}`}
      style={style}
      {...props}
    >
      {/* Placeholder */}
      {shouldShowPlaceholder && (
        <div className="lazy-image-loading">
          {placeholder || (
            <i className="feather icon-image lazy-image-loading-icon" />
          )}
        </div>
      )}

      {/* Actual Image */}
      {shouldShowImage && (
        <img
          src={src}
          alt={alt}
          onLoad={handleLoad}
          onError={handleError}
          className={`lazy-image ${isLoaded ? 'loaded' : 'loading'}`}
        />
      )}

      {/* Error State */}
      {hasError && (
        <div className="lazy-image-error">
          <i className="feather icon-alert-triangle lazy-image-error-icon" />
          <small className="lazy-image-error-text">Errore caricamento</small>
        </div>
      )}
    </div>
  );
});

LazyImage.displayName = 'LazyImage';

export default LazyImage;

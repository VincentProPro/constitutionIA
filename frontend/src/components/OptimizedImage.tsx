import React, { useState } from 'react';

interface OptimizedImageProps {
  src: string;
  alt: string;
  className?: string;
  fallbackSrc?: string;
  loading?: 'lazy' | 'eager';
}

const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  className = '',
  fallbackSrc,
  loading = 'lazy'
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const handleLoad = () => {
    setImageLoaded(true);
  };

  const handleError = () => {
    setImageError(true);
  };

  return (
    <div className={`relative ${className}`}>
      {/* Placeholder pendant le chargement */}
      {!imageLoaded && !imageError && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse flex items-center justify-center">
          <div className="text-gray-400 text-sm">Chargement...</div>
        </div>
      )}

      {/* Image principale */}
      <img
        src={imageError && fallbackSrc ? fallbackSrc : src}
        alt={alt}
        loading={loading}
        onLoad={handleLoad}
        onError={handleError}
        className={`w-full h-full object-cover transition-opacity duration-300 ${
          imageLoaded ? 'opacity-100' : 'opacity-0'
        }`}
      />

      {/* Indicateur d'erreur */}
      {imageError && !fallbackSrc && (
        <div className="absolute inset-0 bg-gray-300 flex items-center justify-center">
          <div className="text-gray-500 text-sm">Image non disponible</div>
        </div>
      )}
    </div>
  );
};

export default OptimizedImage; 
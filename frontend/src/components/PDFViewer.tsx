import React, { useState, useEffect, useRef, useMemo } from 'react';
import { XMarkIcon, ChevronLeftIcon, ChevronRightIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { downloadFileFromUrl } from '../utils/downloadFile';

interface PDFViewerProps {
  filename: string;
  isOpen: boolean;
  onClose: () => void;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ filename, isOpen, onClose }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const basePdfUrl = `/api/constitutions/files/${encodeURIComponent(filename)}`;
  const cacheBuster = useMemo(() => Date.now(), [isOpen, filename]);
  const pdfUrlWithBuster = `${basePdfUrl}?v=${cacheBuster}`;

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      setError(null);
    }
  }, [isOpen]);

  // Navigation par clavier
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isOpen) return;
      
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleIframeLoad = () => {
    setLoading(false);
  };

  const handleIframeError = () => {
    setLoading(false);
    setError('Erreur lors du chargement du PDF');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-2 sm:p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full h-full max-w-6xl max-h-[95vh] sm:max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-start sm:items-center justify-between p-3 sm:p-4 border-b border-gray-200">
          <div className="flex items-start sm:items-center space-x-2 sm:space-x-4 flex-1 min-w-0">
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 break-words leading-tight" title={filename}>
              {filename.length > 20 ? `${filename.slice(0, 20)}...` : filename}
            </h2>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={async () => {
                const safeName = filename.endsWith('.pdf') ? filename : `${filename}.pdf`;
                try {
                  await downloadFileFromUrl(pdfUrlWithBuster, safeName);
                } catch (e) {
                  console.error(e);
                }
              }}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              title="Télécharger"
            >
              <DocumentTextIcon className="w-5 h-5 text-gray-500" />
            </button>
            <button
              onClick={onClose}
              className="p-1 sm:p-2 hover:bg-gray-100 rounded-full transition-colors flex-shrink-0 ml-2 sm:ml-0"
            >
              <XMarkIcon className="w-5 h-5 sm:w-6 sm:h-6 text-gray-500" />
            </button>
          </div>
        </div>

        {/* PDF Content */}
        <div className="flex-1 relative overflow-hidden">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50 z-10">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Chargement du PDF...</p>
              </div>
            </div>
          )}
          
          {error ? (
            <div className="flex items-center justify-center h-full bg-gray-50 p-4">
              <div className="text-center max-w-sm sm:max-w-md">
                <DocumentTextIcon className="h-12 w-12 sm:h-16 sm:w-16 text-red-500 mx-auto mb-3 sm:mb-4" />
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-2 break-words leading-tight">
                  Erreur de chargement
                </h3>
                <p className="text-sm sm:text-base text-gray-600 mb-4 sm:mb-6">
                  {error}
                </p>
                <div className="flex flex-col sm:flex-row gap-2 sm:space-x-3">
                  <button
                    onClick={() => window.open(pdfUrlWithBuster, '_blank')}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 sm:px-6 py-2 rounded-lg font-medium transition-colors text-sm sm:text-base"
                  >
                    Ouvrir dans un nouvel onglet
                  </button>
                  <button
                    onClick={async () => {
                      const safeName = filename.endsWith('.pdf') ? filename : `${filename}.pdf`;
                      try {
                        await downloadFileFromUrl(pdfUrlWithBuster, safeName);
                      } catch (e) {
                        console.error(e);
                      }
                    }}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 sm:px-6 py-2 rounded-lg font-medium transition-colors text-sm sm:text-base"
                  >
                    Télécharger
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <iframe
              src={pdfUrlWithBuster}
              className="w-full h-full border-0"
              onLoad={handleIframeLoad}
              onError={handleIframeError}
              title={filename}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default PDFViewer; 
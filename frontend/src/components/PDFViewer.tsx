import React, { useState, useEffect, useRef } from 'react';
import { XMarkIcon, ChevronLeftIcon, ChevronRightIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

interface PDFViewerProps {
  filename: string;
  isOpen: boolean;
  onClose: () => void;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ filename, isOpen, onClose }) => {
  const [loading, setLoading] = useState(false);

  const pdfUrl = `/api/constitutions/files/${encodeURIComponent(filename)}`;

  useEffect(() => {
    if (isOpen) {
      setLoading(false);
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-2 sm:p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full h-full max-w-6xl max-h-[95vh] sm:max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-start sm:items-center justify-between p-3 sm:p-4 border-b border-gray-200">
          <div className="flex items-start sm:items-center space-x-2 sm:space-x-4 flex-1 min-w-0">
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 break-words leading-tight">
              {filename}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 sm:p-2 hover:bg-gray-100 rounded-full transition-colors flex-shrink-0 ml-2 sm:ml-0"
          >
            <XMarkIcon className="w-5 h-5 sm:w-6 sm:h-6 text-gray-500" />
          </button>
        </div>

        {/* PDF Content */}
        <div className="flex-1 relative overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-full bg-gray-50">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Chargement du PDF...</p>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full bg-gray-50 p-4">
              <div className="text-center max-w-sm sm:max-w-md">
                <DocumentTextIcon className="h-12 w-12 sm:h-16 sm:w-16 text-blue-600 mx-auto mb-3 sm:mb-4" />
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-2 break-words leading-tight">
                  {filename}
                </h3>
                <p className="text-sm sm:text-base text-gray-600 mb-4 sm:mb-6">
                  Le PDF est maintenant correctement servi. Utilisez les boutons ci-dessous pour l'ouvrir ou le télécharger.
                </p>
                <div className="flex flex-col sm:flex-row gap-2 sm:space-x-3">
                  <button
                    onClick={() => window.open(pdfUrl, '_blank')}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 sm:px-6 py-2 rounded-lg font-medium transition-colors text-sm sm:text-base"
                  >
                    Ouvrir le PDF
                  </button>
                  <button
                    onClick={() => {
                      const link = document.createElement('a');
                      link.href = pdfUrl;
                      link.download = filename;
                      link.click();
                    }}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 sm:px-6 py-2 rounded-lg font-medium transition-colors text-sm sm:text-base"
                  >
                    Télécharger
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>



        {/* Footer */}
        <div className="flex flex-col sm:flex-row items-center justify-between p-3 sm:p-4 border-t border-gray-200 bg-gray-50 gap-2 sm:gap-0">
          <div className="flex flex-col sm:flex-row gap-2 sm:space-x-4">
            <button
              onClick={() => window.open(pdfUrl, '_blank')}
              className="text-blue-600 hover:text-blue-700 text-xs sm:text-sm font-medium"
            >
              Ouvrir dans un nouvel onglet
            </button>
            <button
              onClick={() => {
                const link = document.createElement('a');
                link.href = pdfUrl;
                link.download = filename;
                link.click();
              }}
              className="text-blue-600 hover:text-blue-700 text-xs sm:text-sm font-medium"
            >
              Télécharger
            </button>
          </div>
          <div className="text-xs sm:text-sm text-gray-500">
            Appuyez sur Échap pour fermer
          </div>
        </div>
      </div>
    </div>
  );
};

export default PDFViewer; 
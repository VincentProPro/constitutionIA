import React, { useState, useEffect, useRef } from 'react';
import { XMarkIcon, ChevronLeftIcon, ChevronRightIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

interface PDFViewerProps {
  filename: string;
  isOpen: boolean;
  onClose: () => void;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ filename, isOpen, onClose }) => {
  const [loading, setLoading] = useState(false);

  const pdfUrl = `http://localhost:8000/api/constitutions/files/${encodeURIComponent(filename)}`;

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
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-2xl w-full h-full max-w-6xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold text-gray-900">
              {filename}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <XMarkIcon className="w-6 h-6 text-gray-500" />
          </button>
        </div>

        {/* PDF Content */}
        <div className="flex-1 relative overflow-hidden">
          <div className="flex items-center justify-center h-full bg-gray-50">
            <div className="text-center max-w-md">
              <DocumentTextIcon className="h-16 w-16 text-blue-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {filename}
              </h3>
              <p className="text-gray-600 mb-6">
                Le PDF sera ouvert dans un nouvel onglet pour une meilleure expérience de lecture.
              </p>
              <div className="flex space-x-3">
                <button
                  onClick={() => window.open(pdfUrl, '_blank')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
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
                  className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-2 rounded-lg font-medium transition-colors"
                >
                  Télécharger
                </button>
              </div>
            </div>
          </div>
        </div>



        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex space-x-4">
            <button
              onClick={() => window.open(pdfUrl, '_blank')}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
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
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              Télécharger
            </button>
          </div>
          <div className="text-sm text-gray-500">
            Appuyez sur Échap pour fermer
          </div>
        </div>
      </div>
    </div>
  );
};

export default PDFViewer; 
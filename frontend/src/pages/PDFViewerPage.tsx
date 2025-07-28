import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeftIcon, DocumentTextIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';
import AIChat from '../components/AIChat.js';

const PDFViewerPage: React.FC = () => {
  const { filename } = useParams<{ filename: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(true); // Ouvrir automatiquement

  console.log('PDFViewerPage - isChatOpen:', isChatOpen, 'filename:', filename);

  const pdfUrl = `http://localhost:8000/api/constitutions/files/${filename || ''}`;

  useEffect(() => {
    console.log('PDFViewerPage - filename:', filename);
    console.log('PDFViewerPage - pdfUrl:', pdfUrl);
    
    if (!filename) {
      setError('Nom de fichier manquant');
      setLoading(false);
      return;
    }

    // Vérifier que le fichier existe
    fetch(pdfUrl)
      .then(response => {
        console.log('PDFViewerPage - response status:', response.status);
        console.log('PDFViewerPage - response ok:', response.ok);
        
        if (!response.ok) {
          throw new Error(`Fichier non trouvé (${response.status})`);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Erreur lors du chargement:', err);
        setError(`Erreur lors du chargement du PDF: ${err.message}`);
        setLoading(false);
      });
  }, [filename, pdfUrl]);

  const handleBack = () => {
    navigate('/constitutions');
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = filename || 'constitution.pdf';
    link.click();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement du PDF...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <DocumentTextIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Erreur</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={handleBack}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            Retour aux constitutions
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={handleBack}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeftIcon className="w-5 h-5" />
                <span>Retour</span>
              </button>
              <div className="h-6 w-px bg-gray-300"></div>
              <h1 className="text-lg font-semibold text-gray-900 truncate">
                {filename}
              </h1>
            </div>
            
                                <div className="flex items-center space-x-3">
                      <button
                        onClick={() => {
                          console.log('Bouton IA cliqué - isChatOpen avant:', isChatOpen);
                          setIsChatOpen(!isChatOpen);
                          console.log('Bouton IA cliqué - isChatOpen après:', !isChatOpen);
                        }}
                        className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                          isChatOpen 
                            ? 'bg-red-600 hover:bg-red-700 text-white' 
                            : 'bg-green-600 hover:bg-green-700 text-white'
                        }`}
                      >
                        <ChatBubbleLeftRightIcon className="w-4 h-4" />
                        <span>{isChatOpen ? 'Fermer IA' : 'Assistant IA'}</span>
                      </button>
                      <button
                        onClick={() => window.open(pdfUrl, '_blank')}
                        className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                      >
                        Ouvrir dans un nouvel onglet
                      </button>
                      <button
                        onClick={handleDownload}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                      >
                        Télécharger
                      </button>
                    </div>
          </div>
        </div>
      </div>

      {/* PDF Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="h-[calc(100vh-200px)] min-h-[600px]">
            <iframe
              src={pdfUrl}
              className="w-full h-full border-0"
              title={filename}
            />
          </div>
        </div>
      </div>

      {/* Chat IA */}
      <AIChat
        filename={filename || ''}
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  );
};

export default PDFViewerPage; 
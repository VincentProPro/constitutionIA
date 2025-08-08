import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  DocumentTextIcon, 
  ChatBubbleLeftRightIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  XMarkIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import AIChat from '../components/AIChat.js';

const PDFViewerPage: React.FC = () => {
  const { filename } = useParams<{ filename: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isChatExpanded, setIsChatExpanded] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [showAssistant, setShowAssistant] = useState(true);

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

  const formatFilename = (name: string) => {
    return name.replace(/%20/g, ' ').replace('.pdf', '');
  };

  const handleOpenChat = () => {
    setIsChatOpen(true);
    setShowAssistant(false);
  };

  const handleCloseChat = () => {
    setIsChatOpen(false);
    setIsChatExpanded(false);
  };

  const handleToggleChatExpanded = (expanded: boolean) => {
    setIsChatExpanded(expanded);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mx-auto mb-6"></div>
            <div className="absolute inset-0 rounded-full h-16 w-16 border-4 border-transparent border-t-blue-400 animate-ping"></div>
          </div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Chargement en cours...</h3>
          <p className="text-gray-600">Préparation du document PDF</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-100 flex items-center justify-center">
        <div className="text-center max-w-md mx-4">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <DocumentTextIcon className="h-10 w-10 text-red-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Document non trouvé</h2>
            <p className="text-gray-600 mb-8 leading-relaxed">{error}</p>
            <button
              onClick={handleBack}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-medium transition-all duration-200 transform hover:scale-105 shadow-lg"
            >
              Retour aux constitutions
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Header amélioré */}
      <div className="bg-white/80 backdrop-blur-sm shadow-lg border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            {/* Section gauche */}
            <div className="flex items-center space-x-6">
              <button
                onClick={handleBack}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-all duration-200 hover:bg-gray-100 px-3 py-2 rounded-lg group"
              >
                <ArrowLeftIcon className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                <span className="font-medium">Retour</span>
              </button>
              
              <div className="h-8 w-px bg-gray-300"></div>
              
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <DocumentTextIcon className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900 truncate max-w-md">
                    {formatFilename(filename || '')}
                  </h1>
                  <p className="text-sm text-gray-500">Document PDF</p>
                </div>
              </div>
            </div>
            
            {/* Section droite - Actions */}
            <div className="flex items-center space-x-3">
              {/* Bouton Info */}
              <button
                onClick={() => setShowInfo(!showInfo)}
                className="p-2 text-gray-500 hover:text-blue-600 transition-colors duration-200 hover:bg-blue-50 rounded-lg"
                title="Informations"
              >
                <InformationCircleIcon className="w-5 h-5" />
              </button>

              {/* Bouton Assistant IA */}
              <button
                onClick={() => setIsChatOpen(!isChatOpen)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 transform hover:scale-105 ${
                  isChatOpen 
                    ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg' 
                    : 'bg-green-500 hover:bg-green-600 text-white shadow-lg'
                }`}
              >
                <ChatBubbleLeftRightIcon className="w-4 h-4" />
                <span>{isChatOpen ? 'Fermer IA' : 'Assistant IA'}</span>
              </button>

              {/* Bouton Ouvrir dans nouvel onglet */}
              <button
                onClick={() => window.open(pdfUrl, '_blank')}
                className="flex items-center space-x-2 px-4 py-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-xl text-sm font-medium transition-all duration-200"
              >
                <EyeIcon className="w-4 h-4" />
                <span>Nouvel onglet</span>
              </button>

              {/* Bouton Télécharger */}
              <button
                onClick={handleDownload}
                className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 transform hover:scale-105 shadow-lg"
              >
                <ArrowDownTrayIcon className="w-4 h-4" />
                <span>Télécharger</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Panel d'informations */}
      {showInfo && (
        <div className="bg-blue-50 border-b border-blue-200 px-4 py-3">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <InformationCircleIcon className="w-5 h-5 text-blue-600" />
              <div>
                <p className="text-sm text-blue-800">
                  <strong>Document :</strong> {formatFilename(filename || '')}
                </p>
                <p className="text-xs text-blue-600">
                  Utilisez l'Assistant IA pour poser des questions sur ce document
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowInfo(false)}
              className="text-blue-600 hover:text-blue-800 transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* Contenu principal avec animation */}
      <div className="flex transition-all duration-500 ease-in-out">
        {/* Zone PDF avec animation */}
        <div className={`transition-all duration-500 ease-in-out ${
          isChatOpen 
            ? isChatExpanded 
              ? 'w-1/3 pr-4' 
              : 'w-2/3 pr-4'
            : 'w-full'
        }`}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-200">
              <div className="h-[calc(100vh-280px)] min-h-[600px] relative">
                {/* Indicateur de chargement du PDF */}
                <div className="absolute inset-0 bg-gray-100 flex items-center justify-center z-10" id="pdf-loading">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent mx-auto mb-2"></div>
                    <p className="text-sm text-gray-600">Chargement du PDF...</p>
                  </div>
                </div>
                
                <iframe
                  src={pdfUrl}
                  className="w-full h-full border-0"
                  title={filename}
                  onLoad={() => {
                    const loadingElement = document.getElementById('pdf-loading');
                    if (loadingElement) {
                      loadingElement.style.display = 'none';
                    }
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Zone Chat IA avec animation */}
        <div className={`transition-all duration-500 ease-in-out ${
          isChatOpen 
            ? isChatExpanded 
              ? 'w-2/3 opacity-100' 
              : 'w-1/3 opacity-100'
            : 'w-0 opacity-0'
        }`}>
          {isChatOpen && (
            <div className="h-[calc(100vh-200px)] bg-white rounded-2xl shadow-2xl border border-gray-200 m-6 overflow-hidden">
              <AIChat
                filename={filename || ''}
                isOpen={isChatOpen}
                onClose={handleCloseChat}
                onToggleExpanded={handleToggleChatExpanded}
              />
            </div>
          )}
        </div>
      </div>

      {/* Assistant flottant avec image */}
      {showAssistant && !isChatOpen && (
        <div className="fixed bottom-6 right-6 z-40">
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-200 p-4 max-w-sm animate-fade-in">
            <div className="flex items-center space-x-3 mb-3">
              <img 
                src="/images/assistant.png" 
                alt="Assistant IA" 
                className="w-12 h-12 rounded-full object-cover"
              />
              <div>
                <h3 className="font-semibold text-gray-900">Assistant IA</h3>
                <p className="text-sm text-gray-600">Besoin d'aide ?</p>
              </div>
              <button
                onClick={() => setShowAssistant(false)}
                className="ml-auto text-gray-400 hover:text-gray-600 transition-colors"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
            <button
              onClick={handleOpenChat}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-xl font-medium transition-all duration-200 transform hover:scale-105 shadow-lg"
            >
              Discuter avec l'IA
            </button>
          </div>
        </div>
      )}

      {/* Bouton flottant pour réafficher l'assistant */}
      {!showAssistant && !isChatOpen && (
        <button
          onClick={() => setShowAssistant(true)}
          className="fixed bottom-6 right-6 z-40 bg-green-500 hover:bg-green-600 text-white p-4 rounded-full shadow-2xl transition-all duration-200 transform hover:scale-110 animate-bounce"
          title="Afficher l'Assistant IA"
        >
          <ChatBubbleLeftRightIcon className="w-6 h-6" />
        </button>
      )}
    </div>
  );
};

export default PDFViewerPage; 
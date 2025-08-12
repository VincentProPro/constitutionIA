import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNotificationContext } from '../contexts/NotificationContext';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  constitution?: string;
}

const ChatNowPage: React.FC = () => {
  const { user } = useAuth();
  const { showError } = useNotificationContext();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedConstitution, setSelectedConstitution] = useState('');
  const [constitutions, setConstitutions] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load constitutions on component mount
  useEffect(() => {
    fetchConstitutions();
  }, []);

  const fetchConstitutions = async () => {
    try {
      const response = await fetch('/api/constitutions/');
      if (response.ok) {
        const data = await response.json();
        setConstitutions(data);
        if (data.length > 0) {
          setSelectedConstitution(data[0].filename);
        }
      }
    } catch (error) {
      console.error('Erreur lors du chargement des constitutions:', error);
      showError('Erreur', 'Erreur lors du chargement des constitutions');
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !selectedConstitution) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputMessage,
      isUser: true,
      timestamp: new Date(),
      constitution: selectedConstitution
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/ai/chat/pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: inputMessage,
          filename: selectedConstitution
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.response,
          isUser: false,
          timestamp: new Date(),
          constitution: selectedConstitution
        };
        setMessages(prev => [...prev, aiMessage]);
      } else {
        const errorData = await response.json();
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: `Erreur: ${errorData.detail || 'Une erreur s\'est produite'}`,
          isUser: false,
          timestamp: new Date(),
          constitution: selectedConstitution
        };
        setMessages(prev => [...prev, errorMessage]);
        showError('Erreur', 'Erreur lors de la communication avec l\'IA');
      }
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Erreur de connexion. Veuillez réessayer.',
        isUser: false,
        timestamp: new Date(),
        constitution: selectedConstitution
      };
      setMessages(prev => [...prev, errorMessage]);
      showError('Erreur', 'Erreur de connexion');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  const getConstitutionTitle = (filename: string) => {
    const constitution = constitutions.find(c => c.filename === filename);
    return constitution ? constitution.title : filename;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            💬 ChatNow
          </h1>
          <p className="text-lg text-gray-600">
            Posez vos questions sur les constitutions et obtenez des réponses instantanées
          </p>
        </div>

        {/* Constitution Selector */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            📄 Constitution à consulter
          </label>
          <select
            value={selectedConstitution}
            onChange={(e) => setSelectedConstitution(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {constitutions.map((constitution) => (
              <option key={constitution.id} value={constitution.filename}>
                {constitution.title}
              </option>
            ))}
          </select>
          {selectedConstitution && (
            <p className="text-sm text-gray-500 mt-2">
              Constitution active: <span className="font-medium">{getConstitutionTitle(selectedConstitution)}</span>
            </p>
          )}
        </div>

        {/* Chat Container */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Chat Header */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-semibold text-white">
                  Assistant ConstitutionIA
                </h2>
                <p className="text-blue-100 text-sm">
                  {selectedConstitution ? getConstitutionTitle(selectedConstitution) : 'Sélectionnez une constitution'}
                </p>
              </div>
              <button
                onClick={clearChat}
                className="bg-white/20 hover:bg-white/30 text-white px-4 py-2 rounded-lg transition-colors"
              >
                🗑️ Effacer
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="h-96 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <div className="text-6xl mb-4">🤖</div>
                <p className="text-lg font-medium mb-2">Bienvenue dans ChatNow !</p>
                <p className="text-sm">
                  Posez vos questions sur la constitution sélectionnée et obtenez des réponses précises.
                </p>
                <div className="mt-4 text-xs text-gray-400">
                  💡 Exemples de questions :
                  <ul className="mt-2 space-y-1">
                    <li>• "Quelle est la durée du mandat présidentiel ?"</li>
                    <li>• "Que dit l'article 44 sur les droits des citoyens ?"</li>
                    <li>• "Comment fonctionne le pouvoir judiciaire ?"</li>
                  </ul>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.isUser
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    <div className="text-sm">{message.text}</div>
                    <div className={`text-xs mt-1 ${
                      message.isUser ? 'text-blue-100' : 'text-gray-500'
                    }`}>
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-800 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span className="text-sm">L'assistant réfléchit...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex space-x-4">
              <div className="flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Posez votre question sur la constitution..."
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={2}
                  disabled={isLoading || !selectedConstitution}
                />
              </div>
              <button
                onClick={sendMessage}
                disabled={!inputMessage.trim() || isLoading || !selectedConstitution}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg transition-colors flex items-center space-x-2"
              >
                <span>📤</span>
                <span>Envoyer</span>
              </button>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              Appuyez sur Entrée pour envoyer, Shift+Entrée pour une nouvelle ligne
            </div>
          </div>
        </div>

        {/* Tips */}
        <div className="mt-6 bg-blue-50 rounded-lg p-4">
          <h3 className="font-semibold text-blue-800 mb-2">💡 Conseils d'utilisation</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Sélectionnez d'abord la constitution que vous souhaitez consulter</li>
            <li>• Posez des questions précises pour obtenir des réponses détaillées</li>
            <li>• Vous pouvez demander des informations sur des articles spécifiques</li>
            <li>• L'assistant cite toujours les sources exactes de ses réponses</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ChatNowPage;

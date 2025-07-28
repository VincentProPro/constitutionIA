import React, { useState, useEffect, useRef } from 'react';
import { 
  PaperAirplaneIcon,
  SparklesIcon,
  DocumentTextIcon,
  LightBulbIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  sources?: any[];
  confidence?: number;
}

interface Suggestion {
  text: string;
  category: string;
}

const AICopilotPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const defaultSuggestions = [
    { text: "Quels sont les droits fondamentaux garantis par la constitution ?", category: "droits" },
    { text: "Comment est organisé le pouvoir exécutif ?", category: "pouvoirs" },
    { text: "Quelles sont les procédures de révision constitutionnelle ?", category: "procédures" },
    { text: "Comment sont protégés les droits des citoyens ?", category: "protection" },
    { text: "Quelle est la structure du pouvoir judiciaire ?", category: "pouvoirs" },
    { text: "Comment fonctionne le système électoral ?", category: "élections" },
    { text: "Quels sont les principes de la démocratie ?", category: "principes" },
    { text: "Comment est organisée l'administration publique ?", category: "administration" }
  ];

  useEffect(() => {
    setSuggestions(defaultSuggestions);
    // Message de bienvenue
    setMessages([
      {
        id: '1',
        type: 'ai',
        content: "Bonjour ! Je suis votre assistant IA spécialisé dans les constitutions de la Guinée. Posez-moi vos questions sur les droits, les pouvoirs, les procédures ou tout autre aspect constitutionnel. Je peux vous aider à trouver des informations précises dans les documents constitutionnels.",
        timestamp: new Date()
      }
    ]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/api/ai/chat', {
        query: content,
        max_results: 5
      });

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: response.data.answer,
        timestamp: new Date(),
        sources: response.data.sources,
        confidence: response.data.confidence
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: "Désolé, je n'ai pas pu traiter votre demande. Veuillez réessayer.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <SparklesIcon className="h-8 w-8 text-primary-600" />
            <h1 className="text-3xl font-bold text-gray-900">
              Copilot IA
            </h1>
          </div>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Posez vos questions sur les constitutions de la Guinée. Notre assistant IA vous aidera 
            à trouver des informations précises et pertinentes.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Chat Interface */}
          <div className="lg:col-span-2">
            <div className="card h-[600px] flex flex-col">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        message.type === 'user'
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      
                      {/* Sources pour les messages IA */}
                      {message.type === 'ai' && message.sources && message.sources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <p className="text-xs font-medium mb-2">Sources :</p>
                          <div className="space-y-1">
                            {message.sources.slice(0, 3).map((source, index) => (
                              <div key={index} className="flex items-center space-x-2 text-xs">
                                <DocumentTextIcon className="h-3 w-3" />
                                <span>
                                  Constitution {source.year} - {source.title}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      <p className={`text-xs mt-2 ${
                        message.type === 'user' ? 'text-primary-100' : 'text-gray-500'
                      }`}>
                        {formatTimestamp(message.timestamp)}
                      </p>
                    </div>
                  </div>
                ))}
                
                {/* Loading indicator */}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 rounded-lg p-3">
                      <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                        <span className="text-sm text-gray-600">IA réfléchit...</span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="border-t border-gray-200 p-4">
                <form onSubmit={handleSubmit} className="flex space-x-2">
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Posez votre question..."
                    className="flex-1 input-field"
                    disabled={isLoading}
                  />
                  <button
                    type="submit"
                    disabled={isLoading || !inputValue.trim()}
                    className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <PaperAirplaneIcon className="h-5 w-5" />
                  </button>
                </form>
              </div>
            </div>
          </div>

          {/* Suggestions Sidebar */}
          <div className="lg:col-span-1">
            <div className="card">
              <div className="flex items-center space-x-2 mb-4">
                <LightBulbIcon className="h-5 w-5 text-primary-600" />
                <h3 className="font-semibold text-gray-900">Suggestions</h3>
              </div>
              
              <div className="space-y-3">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion.text)}
                    className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200"
                  >
                    <div className="flex items-start space-x-2">
                      <ChatBubbleLeftRightIcon className="h-4 w-4 text-primary-600 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-700">{suggestion.text}</span>
                    </div>
                  </button>
                ))}
              </div>

              <div className="mt-6 pt-4 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Conseils d'utilisation</h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• Posez des questions spécifiques</li>
                  <li>• Mentionnez l'année si nécessaire</li>
                  <li>• Demandez des comparaisons entre versions</li>
                  <li>• Interrogez sur les droits et obligations</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AICopilotPage; 
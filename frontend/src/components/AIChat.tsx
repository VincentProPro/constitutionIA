import React, { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon, ChatBubbleLeftRightIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

interface AIChatProps {
  filename: string;
  isOpen: boolean;
  onClose: () => void;
}

const AIChat: React.FC<AIChatProps> = ({ filename, isOpen, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Message de bienvenue de l'assistant
  const welcomeMessage: Message = {
    id: 'welcome',
    text: "Bonjour ! Je suis votre assistant IA spécialisé dans l'analyse des constitutions. Comment puis-je vous aider à mieux comprendre ce document ?",
    isUser: false,
    timestamp: new Date()
  };

  // Suggestions de questions
  const suggestedQuestions = [
    "Quels sont les droits fondamentaux mentionnés ?",
    "Comment est organisé le pouvoir exécutif ?",
    "Quelles sont les procédures de révision ?",
    "Expliquez la structure du document"
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Ajouter le message de bienvenue quand le chat s'ouvre
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([welcomeMessage]);
    }
  }, [isOpen, messages.length]);

  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    const startTime = Date.now();

    try {
      const response = await fetch('http://localhost:8000/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: inputText,
          context: 'Constitution Guinée',
          max_results: 5
        })
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la communication avec l\'IA');
      }

      const data = await response.json();
      const backendTime = Math.round((data.search_time || 0) * 1000); // Convertir en ms
      const totalTime = Date.now() - startTime;
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.answer,
        isUser: false,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);
      
      // Afficher les suggestions si disponibles
      if (data.suggestions && data.suggestions.length > 0) {
        setTimeout(() => {
          const suggestionsMessage: Message = {
            id: (Date.now() + 3).toString(),
            text: `💡 Suggestions: ${data.suggestions.join(', ')}`,
            isUser: false,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, suggestionsMessage]);
        }, 1000);
      }
    } catch (error) {
      console.error('Erreur:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Désolé, une erreur s\'est produite lors de la communication avec l\'assistant IA.',
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
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

  const handleSuggestedQuestion = (question: string) => {
    setInputText(question);
    // Envoyer automatiquement la question suggérée
    setTimeout(() => {
      setInputText(question);
      const userMessage: Message = {
        id: Date.now().toString(),
        text: question,
        isUser: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);
      setInputText('');
      setIsLoading(true);
      
      // Appeler l'API
      fetch('http://localhost:8000/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: question,
          context: 'Constitution Guinée',
          max_results: 5
        })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Erreur lors de la communication avec l\'IA');
        }
        return response.json();
      })
      .then(data => {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.answer,
          isUser: false,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiMessage]);
      })
      .catch(error => {
        console.error('Erreur:', error);
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: 'Désolé, une erreur s\'est produite lors de la communication avec l\'assistant IA.',
          isUser: false,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      })
      .finally(() => {
        setIsLoading(false);
      });
    }, 100);
  };

  if (!isOpen) return null;

  console.log('AIChat - isOpen:', isOpen, 'filename:', filename, 'messages:', messages.length);

  return (
    <div 
      className="fixed bottom-4 right-4 w-96 h-96 bg-white rounded-lg shadow-2xl border-2 border-blue-500 flex flex-col z-[9999]"
      style={{ 
        zIndex: 9999,
        position: 'fixed',
        bottom: '16px',
        right: '16px',
        width: '384px',
        height: '384px',
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        border: '2px solid #3b82f6'
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-blue-600 text-white rounded-t-lg">
        <div className="flex items-center space-x-2">
          <ChatBubbleLeftRightIcon className="w-5 h-5" />
          <span className="font-semibold">Assistant IA</span>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-xs">Optimisé</span>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <div className="text-xs bg-blue-700 px-2 py-1 rounded">
            Cache: {messages.length > 0 ? 'Actif' : 'Prêt'}
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-blue-700 rounded-full transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isOpen && (
          <div className="text-center text-gray-500 py-8">
            <ChatBubbleLeftRightIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">Posez vos questions sur le fichier PDF</p>
            <p className="text-xs mt-1">"{filename}"</p>
          </div>
        )}
        
        {messages.map((message) => (
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
              <p className="text-sm">{message.text}</p>
              <p className={`text-xs mt-1 ${
                message.isUser ? 'text-blue-100' : 'text-gray-500'
              }`}>
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        
        {/* Suggestions de questions après le message de bienvenue */}
        {messages.length === 1 && messages[0].id === 'welcome' && (
          <div className="space-y-2">
            <p className="text-xs text-gray-500 font-medium">Suggestions de questions :</p>
            <div className="grid grid-cols-2 gap-2">
              {suggestedQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestedQuestion(question)}
                  className="text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-2 rounded-lg border border-blue-200 transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-800 px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-sm">L'assistant réfléchit...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Posez votre question..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputText.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <PaperAirplaneIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIChat; 
import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { PaperAirplaneIcon, ChatBubbleLeftRightIcon, XMarkIcon, ArrowsPointingOutIcon, ArrowsPointingInIcon } from '@heroicons/react/24/outline';

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
  onToggleExpanded?: (expanded: boolean) => void;
}

const AIChat: React.FC<AIChatProps> = ({ filename, isOpen, onClose, onToggleExpanded }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
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
      const response = await fetch('/api/ai/chat/pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename,
          question: userMessage.text
        })
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la communication avec l\'IA');
      }

      const data = await response.json();
      const backendTime = Math.round((data.search_time || 0) * 1000);
      const totalTime = Date.now() - startTime;
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response || data.answer || 'Réponse indisponible',
        isUser: false,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);
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
      fetch('/api/ai/chat/pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename,
          question
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
          text: data.response || data.answer || 'Réponse indisponible',
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

  const handleToggleExpanded = () => {
    const newExpandedState = !isExpanded;
    setIsExpanded(newExpandedState);
    if (onToggleExpanded) {
      onToggleExpanded(newExpandedState);
    }
  };

  if (!isOpen) return null;

  console.log('AIChat - isOpen:', isOpen, 'filename:', filename, 'messages:', messages.length);

  return (
    <div className="w-full h-full flex flex-col bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-3 sm:p-4 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-blue-700 text-white">
        <div className="flex items-center space-x-2 sm:space-x-3">
          <div className="w-6 h-6 sm:w-8 sm:h-8 bg-white/20 rounded-full flex items-center justify-center">
            <ChatBubbleLeftRightIcon className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div>
            <span className="font-semibold text-sm sm:text-lg">Assistant IA</span>
            <div className="flex items-center space-x-1 sm:space-x-2 mt-1">
              <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-xs opacity-90">Optimisé</span>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2 sm:space-x-3">
          <button
            onClick={handleToggleExpanded}
            className="flex items-center space-x-1 sm:space-x-2 text-xs bg-white/20 px-2 sm:px-3 py-1 rounded-full backdrop-blur-sm hover:bg-white/30 transition-all duration-200"
            title={isExpanded ? "Réduire le popup" : "Agrandir le popup"}
          >
            {isExpanded ? (
              <ArrowsPointingInIcon className="w-3 h-3" />
            ) : (
              <ArrowsPointingOutIcon className="w-3 h-3" />
            )}
            <span className="hidden sm:inline">{isExpanded ? 'Réduire' : 'Agrandir'}</span>
          </button>
          <button
            onClick={onClose}
            className="p-1 sm:p-2 hover:bg-white/20 rounded-full transition-all duration-200 hover:scale-110"
          >
            <XMarkIcon className="w-4 h-4 sm:w-5 sm:h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4 bg-gray-50">
        {messages.length === 0 && !isOpen && (
          <div className="text-center text-gray-500 py-6 sm:py-8">
            <ChatBubbleLeftRightIcon className="w-8 h-8 sm:w-12 sm:h-12 mx-auto mb-2 text-gray-300" />
            <p className="text-xs sm:text-sm">Posez vos questions sur le fichier PDF</p>
            <p className="text-xs mt-1">"{filename}"</p>
          </div>
        )}
        
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] sm:max-w-xs lg:max-w-md px-3 sm:px-4 py-2 sm:py-3 rounded-2xl shadow-sm ${
                message.isUser
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-800 border border-gray-200'
              }`}
            >
              {message.isUser ? (
                <p className="text-xs sm:text-sm leading-relaxed">{message.text}</p>
              ) : (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text}</ReactMarkdown>
                </div>
              )}
              <p className={`text-xs mt-1 sm:mt-2 ${
                message.isUser ? 'text-blue-100' : 'text-gray-500'
              }`}>
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        
        {/* Suggestions de questions après le message de bienvenue */}
        {messages.length === 1 && messages[0].id === 'welcome' && (
          <div className="space-y-2 sm:space-y-3">
            <p className="text-xs sm:text-sm text-gray-600 font-medium">💡 Suggestions de questions :</p>
            <div className="grid grid-cols-1 gap-2">
              {suggestedQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestedQuestion(question)}
                  className="text-xs sm:text-sm bg-white hover:bg-blue-50 text-blue-700 px-3 sm:px-4 py-2 sm:py-3 rounded-xl border border-blue-200 transition-all duration-200 hover:border-blue-300 hover:shadow-sm text-left"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white text-gray-800 px-3 sm:px-4 py-2 sm:py-3 rounded-2xl border border-gray-200 shadow-sm">
              <div className="flex items-center space-x-2 sm:space-x-3">
                <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-2 border-blue-600 border-t-transparent"></div>
                <span className="text-xs sm:text-sm">L'assistant réfléchit...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 sm:p-4 border-t border-gray-200 bg-white">
        <div className="flex space-x-2 sm:space-x-3">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Posez votre question..."
            className="flex-1 px-3 sm:px-4 py-2 sm:py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-xs sm:text-sm"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputText.trim() || isLoading}
            className="px-3 sm:px-4 py-2 sm:py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:scale-105 shadow-sm"
          >
            <PaperAirplaneIcon className="w-4 h-4 sm:w-5 sm:h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIChat; 
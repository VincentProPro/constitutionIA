import React, { useState, useRef, useEffect } from 'react';
import { 
  PaperAirplaneIcon,
  UserIcon, 
  SparklesIcon,
  ArrowPathIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  loading?: boolean;
}

const AICopilotPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Bonjour ! Je suis ConstitutionIA, votre assistant spécialisé dans la constitution de la Guinée. Comment puis-je vous aider aujourd'hui ?",
      isUser: false,
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll vers le bas
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Créer une session au chargement
  useEffect(() => {
    const createSession = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/ai/session/create', {
          method: 'POST'
        });
        if (response.ok) {
          const data = await response.json();
          setSessionId(data.session_id);
        }
      } catch (error) {
        console.error('Erreur lors de la création de la session:', error);
      }
    };

    createSession();
  }, []);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      isUser: true,
      timestamp: new Date()
    };

    const aiMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: '',
      isUser: false,
      timestamp: new Date(),
      loading: true
    };

    setMessages(prev => [...prev, userMessage, aiMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: inputValue,
          session_id: sessionId
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        setMessages(prev => prev.map(msg => 
          msg.id === aiMessage.id 
            ? { ...msg, content: data.answer, loading: false }
            : msg
        ));
      } else {
        setMessages(prev => prev.map(msg => 
          msg.id === aiMessage.id 
            ? { ...msg, content: "Désolé, une erreur s'est produite. Veuillez réessayer.", loading: false }
            : msg
        ));
      }
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message:', error);
      setMessages(prev => prev.map(msg => 
        msg.id === aiMessage.id 
          ? { ...msg, content: "Désolé, une erreur s'est produite. Veuillez réessayer.", loading: false }
          : msg
      ));
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

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-4xl mx-auto p-4">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center space-x-3 bg-white rounded-full px-6 py-3 shadow-lg">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <SparklesIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Copilot IA</h1>
              <p className="text-sm text-gray-600">Assistant Constitution de la Guinée</p>
            </div>
          </div>
        </div>

        {/* Chat Container */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
              {/* Messages */}
          <div className="h-[600px] overflow-y-auto p-6 space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.isUser
                      ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                  <div className="flex items-start space-x-2">
                    {!message.isUser && (
                      <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center flex-shrink-0">
                        <SparklesIcon className="w-4 h-4 text-white" />
                      </div>
                    )}
                    <div className="flex-1">
                      <p className="text-sm">{message.content}</p>
                      {message.loading && (
                        <div className="flex space-x-1 mt-2">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      )}
                    </div>
                    {message.isUser && (
                      <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center flex-shrink-0">
                        <UserIcon className="w-4 h-4 text-blue-600" />
                      </div>
                    )}
                    </div>
                  <div className={`text-xs mt-2 ${message.isUser ? 'text-blue-100' : 'text-gray-500'}`}>
                    {formatTime(message.timestamp)}
                  </div>
                </div>
              </div>
            ))}
                <div ref={messagesEndRef} />
              </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4 bg-gray-50">
            <div className="flex items-center space-x-3">
              <div className="flex-1 relative">
                <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Posez votre question sur la constitution de la Guinée..."
                  className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={1}
                  style={{ minHeight: '48px', maxHeight: '120px' }}
                    disabled={isLoading}
                  />
                  <button
                  onClick={sendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  >
                  {isLoading ? (
                    <ArrowPathIcon className="w-4 h-4 animate-spin" />
                  ) : (
                    <PaperAirplaneIcon className="w-4 h-4" />
                  )}
                  </button>
            </div>
          </div>

            {/* Suggestions */}
            <div className="mt-3 flex flex-wrap gap-2">
              {[
                "Combien de mandats peut faire un président ?",
                "Quels sont les droits fondamentaux ?",
                "Comment fonctionne le parlement ?",
                "Quelle est la procédure d'élection ?"
              ].map((suggestion, index) => (
                  <button
                    key={index}
                  onClick={() => setInputValue(suggestion)}
                  className="px-3 py-1 text-xs bg-white border border-gray-300 rounded-full hover:bg-gray-50 transition-colors duration-200"
                  >
                  {suggestion}
                  </button>
                ))}
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl p-6 shadow-lg">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <ChatBubbleLeftRightIcon className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Dialogue Intelligent</h3>
            <p className="text-gray-600 text-sm">Posez vos questions naturellement et obtenez des réponses précises sur la constitution.</p>
              </div>

          <div className="bg-white rounded-xl p-6 shadow-lg">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <SparklesIcon className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">IA Spécialisée</h3>
            <p className="text-gray-600 text-sm">Assistant entraîné spécifiquement sur la constitution de la Guinée pour des réponses pertinentes.</p>
              </div>
          
          <div className="bg-white rounded-xl p-6 shadow-lg">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <ArrowPathIcon className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Mémoire de Conversation</h3>
            <p className="text-gray-600 text-sm">L'IA se souvient de vos échanges précédents pour des conversations cohérentes.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AICopilotPage; 
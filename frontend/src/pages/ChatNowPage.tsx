import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import axios from 'axios';
import { useNotificationContext } from '../contexts/NotificationContext';
import Header from '../components/Header';
import Footer from '../components/Footer';

// --- Types ---
export type Role = "user" | "assistant" | "system";

interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  createdAt: string; // ISO string for hydration safety
}

// --- Utilities ---
const isoNow = () => new Date().toISOString();

const formatTime = (iso: string) => {
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return "";
  }
};

const uid = () => Math.random().toString(36).slice(2) + Date.now().toString(36);

// Persist chat in localStorage (simple, optional)
const STORAGE_KEY = "chat-ia-session-v1";

function usePersistentState<T>(key: string, initial: T) {
  const [state, setState] = useState<T>(() => {
    if (typeof window === "undefined") return initial;
    try {
      const raw = localStorage.getItem(key);
      return raw ? (JSON.parse(raw) as T) : initial;
    } catch {
      return initial;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(state));
    } catch {}
  }, [key, state]);

  return [state, setState] as const;
}

// --- Real API Integration ---
async function sendToAIBackend(prompt: string, history: ChatMessage[]): Promise<string> {
  try {
    const response = await axios.post('/api/chatnow/chat', {
      question: prompt,
      user_id: null,
      chat_history: history.slice(-6) // Envoyer les 6 derniers messages pour le contexte
    }, {
      timeout: 45000, // 45 secondes de timeout
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.data && response.data.response) {
      return response.data.response;
    } else {
      throw new Error('Réponse invalide du serveur');
    }
  } catch (error: any) {
    console.error('Erreur API ChatNow:', error);
    
    if (error.response) {
      // Erreur de réponse du serveur
      const status = error.response.status;
      const data = error.response.data;
      
      if (status === 400) {
        throw new Error(data.detail || 'Requête invalide');
      } else if (status === 500) {
        throw new Error('Erreur serveur. Veuillez réessayer.');
      } else {
        throw new Error(data.detail || `Erreur ${status}: ${data.message || 'Erreur inconnue'}`);
      }
    } else if (error.request) {
      // Erreur de réseau
      throw new Error('Erreur de connexion. Vérifiez votre connexion internet.');
    } else if (error.code === 'ECONNABORTED') {
      throw new Error('Délai d\'attente dépassé. Veuillez réessayer.');
    } else {
      throw new Error('Une erreur inattendue est survenue.');
    }
  }
}

// --- Components ---
const MessageBubble: React.FC<{ message: ChatMessage } & { isFirstOfGroup: boolean }> = ({ message, isFirstOfGroup }) => {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] sm:max-w-[80%] rounded-2xl px-3 sm:px-4 py-2 shadow-sm ${isUser ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-900"}`}>
        {isFirstOfGroup && (
          <div className={`text-[10px] mb-1 ${isUser ? "text-blue-100" : "text-gray-500"}`}>{isUser ? "Vous" : "Assistant"}</div>
        )}
        <div className="whitespace-pre-wrap text-sm leading-relaxed break-words">{message.content}</div>
        <div className={`text-[10px] mt-1 ${isUser ? "text-blue-100" : "text-gray-500"}`}>{formatTime(message.createdAt)}</div>
      </div>
    </div>
  );
};

const TypingDots: React.FC = () => (
  <div className="flex items-center space-x-1 sm:space-x-2 text-xs sm:text-sm text-gray-600">
    <div className="animate-bounce h-2 w-2 rounded-full bg-gray-400"></div>
    <div className="animate-bounce [animation-delay:120ms] h-2 w-2 rounded-full bg-gray-400"></div>
    <div className="animate-bounce [animation-delay:240ms] h-2 w-2 rounded-full bg-gray-400"></div>
    <span className="ml-1 sm:ml-2">L'assistant réfléchit…</span>
  </div>
);

// --- Main Page Component ---
const ChatNowPage: React.FC = () => {
  console.log('ChatNowPage: Composant en cours de chargement...');
  
  // Déplacer l'appel du hook au début, sans condition
  const notificationContext = useNotificationContext();
  const { showSuccess, showError, showWarning } = notificationContext || {};

  const [messages, setMessages] = usePersistentState<ChatMessage[]>(STORAGE_KEY, [
    {
      id: uid(),
      role: "assistant",
      content: "Bonjour 👋 Je suis votre assistant IA spécialisé dans l'analyse de la constitution de la Guinée.\n\nJe peux vous aider à :\n• Trouver des articles spécifiques\n• Expliquer les droits et libertés\n• Clarifier le fonctionnement des institutions\n• Analyser les principes constitutionnels\n• Répondre à vos questions sur la constitution\n\nPosez-moi votre question et je vous répondrai en me basant sur la constitution de la Guinée.",
      createdAt: isoNow(),
    },
  ]);

  // Questions amorces clickables
  const quickQuestions = [
    "Quelle est la durée du mandat présidentiel ?",
    "Quels sont les droits fondamentaux des citoyens ?",
    "Comment fonctionne le pouvoir exécutif ?",
    "Que dit la constitution sur l'éducation ?",
    "Quels sont les devoirs des citoyens ?",
    "Comment sont organisées les élections ?"
  ];

  const handleQuickQuestion = (question: string) => {
    setInput(question);
  };

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const canSend = useMemo(() => input.trim().length > 0 && !isLoading, [input, isLoading]);

  useEffect(() => {
    console.log('ChatNowPage: Composant monté avec succès');
  }, []);

  // Scroll automatique optimisé - seulement pour les nouveaux messages
  useEffect(() => {
    if (messages.length > 1) {
      // Utiliser requestAnimationFrame pour un scroll plus fluide
      requestAnimationFrame(() => {
        scrollRef.current?.scrollIntoView({ 
          behavior: "smooth",
          block: "end"
        });
      });
    }
  }, [messages.length]); // Dépendance sur la longueur plutôt que sur l'objet messages

  const sendMessage = useCallback(async () => {
    if (!canSend) return;
    setError(null);

    const userMsg: ChatMessage = {
      id: uid(),
      role: "user",
      content: input.trim(),
      createdAt: isoNow(),
    };

    // Mettre à jour l'état en une seule fois pour éviter les re-renders multiples
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      // Utiliser les messages actuels pour le contexte
      const currentMessages = [...messages, userMsg];
      const reply = await sendToAIBackend(userMsg.content, currentMessages);
      
      const aiMsg: ChatMessage = {
        id: uid(),
        role: "assistant",
        content: reply,
        createdAt: isoNow(),
      };
      
      // Mettre à jour avec le nouveau message de l'IA
      setMessages((prev) => [...prev, aiMsg]);
    } catch (e: any) {
      const errorMessage = e.message || "Une erreur est survenue. Veuillez réessayer.";
      setError(errorMessage);
      if (showError) {
        showError('Erreur de communication', errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  }, [canSend, messages, showError]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }, [sendMessage]);

  const clearChat = useCallback(() => {
    const newMessage: ChatMessage = {
      id: uid(),
      role: "assistant",
      content: "Bonjour 👋 Je suis votre assistant IA spécialisé dans l'analyse de la constitution de la Guinée.\n\nJe peux vous aider à :\n• Trouver des articles spécifiques\n• Expliquer les droits et libertés\n• Clarifier le fonctionnement des institutions\n• Analyser les principes constitutionnels\n• Répondre à vos questions sur la constitution\n\nPosez-moi votre question et je vous répondrai en me basant sur la constitution de la Guinée.",
      createdAt: isoNow(),
    };
    
    // Réinitialiser tous les états en une seule fois
    setMessages([newMessage]);
    setError(null);
    setIsLoading(false);
  }, []);

  const groups = useMemo(() => {
    const result: { first: boolean; msg: ChatMessage }[] = [];
    for (let i = 0; i < messages.length; i++) {
      const msg = messages[i];
      const prev = messages[i - 1];
      const first = !prev || prev.role !== msg.role;
      result.push({ first, msg });
    }
    return result;
  }, [messages.length]); // Dépendance sur la longueur plutôt que sur l'objet messages

  console.log('ChatNowPage: Rendu du composant');
  
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="max-w-4xl mx-auto px-2 sm:px-4 py-2 sm:py-4">
        <div className="mb-2 sm:mb-4 text-center">
          <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-gray-900 mb-2">
            Tout Comprendre sur la Nouvelle Constitution
          </h1>
          <p className="text-gray-600 text-xs sm:text-sm mb-4 px-2">
            Posez une question, appuyez sur <kbd className="px-1 py-0.5 rounded border text-xs">Entrée</kbd> pour envoyer. 
            Utilisez <kbd className="px-1 py-0.5 rounded border text-xs">Shift</kbd>+<kbd className="px-1 py-0.5 rounded border text-xs">Entrée</kbd> pour une nouvelle ligne.
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-md overflow-hidden max-w-3xl mx-auto">
          <div className="h-[calc(100vh-280px)] sm:h-[calc(100vh-320px)] md:h-[calc(100vh-350px)] overflow-y-auto p-2 sm:p-4 space-y-3">
            {groups.map(({ first, msg }) => (
              <MessageBubble key={msg.id} message={msg} isFirstOfGroup={first} />
            ))}

            {/* Questions amorces clickables - affichées seulement si c'est le premier message */}
            {messages.length === 1 && (
              <div className="flex flex-wrap gap-2 justify-center mt-4">
                {quickQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuickQuestion(question)}
                    className="px-3 py-2 bg-blue-100 hover:bg-blue-200 text-blue-800 text-xs sm:text-sm rounded-lg transition-colors duration-200 border border-blue-200 hover:border-blue-300"
                  >
                    {question}
                  </button>
                ))}
              </div>
            )}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-2xl px-3 sm:px-4 py-2">
                  <TypingDots />
                </div>
              </div>
            )}

            <div ref={scrollRef} />
          </div>

          <div className="border-t border-gray-200 p-2 sm:p-3">
            {error && (
              <div className="mb-2 text-xs sm:text-sm text-red-600 bg-red-50 p-2 rounded">{error}</div>
            )}
            <div className="flex items-end gap-2 sm:gap-3">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Écrivez votre message…"
                rows={2}
                className="flex-1 resize-none rounded-xl border border-gray-300 p-2 sm:p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                style={{ resize: 'none' }}
              />
              <button
                onClick={sendMessage}
                disabled={!canSend}
                className="h-10 px-3 sm:px-4 rounded-xl bg-blue-600 text-white text-xs sm:text-sm font-medium disabled:bg-gray-400 hover:bg-blue-700 transition-colors whitespace-nowrap"
              >
                Envoyer
              </button>
            </div>
            <div className="mt-1 text-[10px] sm:text-[11px] text-gray-500">
              Conseil : soyez précis pour obtenir des réponses plus pertinentes.
            </div>
          </div>
        </div>

        <div className="mt-2 sm:mt-4 flex justify-center max-w-3xl mx-auto">
          <button 
            onClick={clearChat}
            className="text-xs sm:text-sm px-3 sm:px-4 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors"
          >
            🗑️ Effacer le chat
          </button>
        </div>

        <div className="mt-2 sm:mt-4 bg-blue-50 text-blue-800 rounded-xl p-3 sm:p-4 max-w-3xl mx-auto">
          <div className="font-semibold mb-1 text-sm sm:text-base">💡 Astuces pour les questions constitutionnelles</div>
          <ul className="list-disc list-inside text-xs sm:text-sm space-y-1">
            <li>Demandez des informations sur des articles spécifiques : <em>"Que dit l'article 15 de la constitution ?"</em></li>
            <li>Posez des questions sur les droits et libertés : <em>"Quels sont les droits fondamentaux garantis ?"</em></li>
            <li>Interrogez sur les institutions : <em>"Comment fonctionne le pouvoir exécutif ?"</em></li>
            <li>Demandez des explications sur les principes constitutionnels</li>
            <li>Relancez l'IA pour préciser un point : <em>"peux‑tu détailler le point 2 ?"</em></li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ChatNowPage;

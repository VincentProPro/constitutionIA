import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { NotificationProvider } from './contexts/NotificationContext';
import NotificationContainer from './components/NotificationContainer';
import HomePage from './pages/HomePage';
import ConstitutionsPage from './pages/ConstitutionsPage';
import AICopilotPage from './pages/AICopilotPage';

const App: React.FC = () => {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // S'assurer que l'application est prête
    setIsReady(true);
  }, []);

  if (!isReady) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <NotificationProvider>
    <Router>
      <div className="min-h-screen bg-gray-50">
          <NotificationContainer />
        <Routes>
          <Route path="/" element={<HomePage />} />
            <Route path="/constitutions" element={<ConstitutionsPage />} />
            <Route path="/ai-copilot" element={<AICopilotPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
    </NotificationProvider>
  );
};

export default App; 
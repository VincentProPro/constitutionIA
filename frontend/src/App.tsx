import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { NotificationProvider } from './contexts/NotificationContext';
import NotificationContainer from './components/NotificationContainer';
import HomePage from './pages/HomePage';
import ConstitutionsPage from './pages/ConstitutionsPage';
import ChatNowPage from './pages/ChatNowPage';

const App: React.FC = () => {
  return (
    <NotificationProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/constitutions" element={<ConstitutionsPage />} />
            <Route path="/chatnow" element={<ChatNowPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <NotificationContainer />
        </div>
      </Router>
    </NotificationProvider>
  );
};

export default App; 
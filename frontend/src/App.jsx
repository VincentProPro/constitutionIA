import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { NotificationProvider } from './contexts/NotificationContext';
import NotificationContainer from './components/NotificationContainer';
import HomePage from './pages/HomePage.tsx';
import ConstitutionsPage from './pages/ConstitutionsPage.tsx';
import PDFViewerPage from './pages/PDFViewerPage.tsx';
import ChatNowPage from './pages/ChatNowPage';

const App = () => {
  return (
    <NotificationProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <NotificationContainer />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/constitutions" element={<ConstitutionsPage />} />
            <Route path="/chatnow" element={<ChatNowPage />} />

            <Route path="/pdf/:filename" element={<PDFViewerPage />} />
          </Routes>
        </div>
      </Router>
    </NotificationProvider>
  );
};

export default App; 
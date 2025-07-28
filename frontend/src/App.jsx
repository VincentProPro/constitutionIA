import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage.js';
import ConstitutionsPage from './pages/ConstitutionsPage.js';
import PDFViewerPage from './pages/PDFViewerPage.js';

const App = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/constitutions" element={<ConstitutionsPage />} />
          <Route path="/pdf/:filename" element={<PDFViewerPage />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App; 
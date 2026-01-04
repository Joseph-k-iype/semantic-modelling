/**
 * Main App Component with Routing
 * Path: frontend/src/App.tsx
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { HomePage } from './pages/HomePage/HomePage';
import { LoginPage } from './pages/LoginPage/LoginPage';
import { OntologyBuilderPage } from './pages/OntologyBuilderPage/OntologyBuilderPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected Routes - Ontology Builder */}
        <Route path="/builder/new" element={<OntologyBuilderPage />} />
        <Route path="/builder/:id" element={<OntologyBuilderPage />} />
        
        {/* Legacy route redirects */}
        <Route path="/diagram/*" element={<Navigate to="/builder/new" replace />} />
        
        {/* Fallback - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
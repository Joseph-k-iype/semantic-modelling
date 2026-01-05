// frontend/src/App.tsx
/**
 * Main App Component with Routing - FIXED with Authentication
 * Path: frontend/src/App.tsx
 * 
 * CRITICAL FIX: Added ProtectedRoute wrapper for authenticated routes
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { HomePage } from './pages/HomePage/HomePage';
import { LoginPage } from './pages/LoginPage/LoginPage';
import { OntologyBuilderPage } from './pages/OntologyBuilderPage/OntologyBuilderPage';
import { ProtectedRoute } from './components/auth/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes - No authentication required */}
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected Routes - Authentication required */}
        <Route 
          path="/builder/new" 
          element={
            <ProtectedRoute>
              <OntologyBuilderPage />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/builder/:id" 
          element={
            <ProtectedRoute>
              <OntologyBuilderPage />
            </ProtectedRoute>
          } 
        />
        
        {/* Legacy route redirects */}
        <Route path="/diagram/*" element={<Navigate to="/builder/new" replace />} />
        
        {/* Fallback - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
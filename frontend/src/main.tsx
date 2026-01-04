/**
 * Main Application Entry Point
 * Path: frontend/src/main.tsx
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/globals.css';

// Error boundary for production
const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Failed to find the root element');
}

// Render app
ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Log application version in development
if (import.meta.env.DEV) {
  console.log('🚀 Semantic Architect v2.0.0');
  console.log('📡 API URL:', import.meta.env.VITE_API_URL);
}
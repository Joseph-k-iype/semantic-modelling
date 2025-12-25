// frontend/src/components/auth/AuthGuard/AuthGuard.tsx

import React, { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';

interface AuthGuardProps {
  children: ReactNode;
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  // TODO: Replace with actual authentication check
  // For now, we'll use a simple check from localStorage
  const isAuthenticated = checkAuth();

  if (!isAuthenticated) {
    // Redirect to login page if not authenticated
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Helper function to check authentication
// TODO: Replace with actual auth logic from your auth store/service
function checkAuth(): boolean {
  // For development, let's assume user is always authenticated
  // In production, check JWT token, auth state, etc.
  const token = localStorage.getItem('access_token');
  
  // If no token, not authenticated
  if (!token) {
    return false;
  }

  // TODO: Add token validation logic here
  // - Check if token is expired
  // - Verify token signature
  // - Check user permissions
  
  return true;
}

export default AuthGuard;
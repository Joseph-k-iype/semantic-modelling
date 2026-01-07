// frontend/src/components/auth/AuthGuard/AuthGuard.tsx
/**
 * Authentication Guard Component - Simplified
 * Protects routes from unauthenticated access
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore, type AuthState } from '../../../store/authStore';

interface AuthGuardProps {
  children: React.ReactNode;
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const location = useLocation();
  
  // Get auth state - this will be true if user logged in
  const isAuthenticated = useAuthStore((state: AuthState) => state.isAuthenticated);
  const token = useAuthStore((state: AuthState) => state.token);

  // If not authenticated and no token, redirect to login
  if (!isAuthenticated || !token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Render protected content
  return <>{children}</>;
};

export default AuthGuard;
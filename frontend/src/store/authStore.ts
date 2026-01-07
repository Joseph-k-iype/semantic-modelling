// frontend/src/store/authStore.ts
/**
 * Authentication Store using Zustand
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: string;
  username: string;
  email: string;
  created_at?: string;
  updated_at?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  
  // Actions
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      loading: false,
      error: null,

      // Set user
      setUser: (user: User) => {
        set({ user, isAuthenticated: true });
      },

      // Set token
      setToken: (token: string) => {
        set({ token });
      },

      // Login
      login: async (email: string, password: string) => {
        set({ loading: true, error: null });
        
        try {
          const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
            credentials: 'include',
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Login failed');
          }

          const data = await response.json();
          
          set({
            user: data.user,
            token: data.access_token,
            isAuthenticated: true,
            loading: false,
            error: null,
          });
        } catch (error) {
          set({
            loading: false,
            error: error instanceof Error ? error.message : 'Login failed',
          });
          throw error;
        }
      },

      // Logout
      logout: async () => {
        set({ loading: true });
        
        try {
          await fetch('/api/v1/auth/logout', {
            method: 'POST',
            credentials: 'include',
          });
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            loading: false,
            error: null,
          });
        }
      },

      // Check authentication status
      checkAuth: async () => {
        const token = get().token;
        
        if (!token) {
          set({ isAuthenticated: false });
          return;
        }

        set({ loading: true });
        
        try {
          const response = await fetch('/api/v1/auth/me', {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
            credentials: 'include',
          });

          if (!response.ok) {
            throw new Error('Authentication check failed');
          }

          const user = await response.json();
          
          set({
            user,
            isAuthenticated: true,
            loading: false,
          });
        } catch (error) {
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            loading: false,
          });
        }
      },

      // Clear error
      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    }
  )
);
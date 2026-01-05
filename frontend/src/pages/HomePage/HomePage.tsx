// frontend/src/pages/HomePage/HomePage.tsx
/**
 * Home Page Component - FIXED with Authentication Check
 * Path: frontend/src/pages/HomePage/HomePage.tsx
 * 
 * CRITICAL FIX:
 * - Checks authentication before creating diagram
 * - Redirects to login if not authenticated
 * - Preserves intended action after login
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, AlertCircle, LogIn } from 'lucide-react';
import { apiClient } from '../../services/api/client';
import { CreateDiagramModal } from '../../components/modals/CreateDiagramModal/CreateDiagramModal'
import { ModelCard } from '../../components/cards/ModelCard/ModelCard';
import { COLORS } from '../../constants/colors';
import type { PublishedModel } from '../../types/diagram.types';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  
  // State
  const [publishedModels, setPublishedModels] = useState<PublishedModel[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check authentication status
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    setIsAuthenticated(!!token);
  }, []);

  // Fetch published models on mount
  useEffect(() => {
    fetchPublishedModels();
  }, []);

  const fetchPublishedModels = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiClient.get<PublishedModel[]>('/diagrams/published');
      setPublishedModels(response.data || []);
    } catch (error: any) {
      console.error('Failed to fetch published models:', error);
      setError(error?.response?.data?.detail || 'Failed to load published models. Please try again.');
      setPublishedModels([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateClick = () => {
    // Check if user is authenticated
    if (!isAuthenticated) {
      // Redirect to login with return path
      navigate('/login', { state: { from: { pathname: '/builder/new' } } });
      return;
    }

    // User is authenticated, show create modal
    setIsCreateModalOpen(true);
  };

  const handleCreateDiagram = async (workspaceName: string, diagramName: string) => {
    // Double-check authentication before API call
    if (!isAuthenticated) {
      navigate('/login', { state: { from: { pathname: '/builder/new' } } });
      return;
    }

    try {
      setIsCreating(true);
      
      const response = await apiClient.post<{ id: string }>('/diagrams', {
        workspace_name: workspaceName,
        name: diagramName,
        nodes: [],  // Empty diagram to start
        edges: [],
        viewport: { x: 0, y: 0, zoom: 1 }
      });

      setIsCreateModalOpen(false);
      
      // Navigate to builder with new diagram ID
      navigate(`/builder/${response.data.id}`);
    } catch (error: any) {
      console.error('Failed to create diagram:', error);
      
      // Check if it's an auth error
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        // Token expired or invalid, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setIsAuthenticated(false);
        navigate('/login', { state: { from: { pathname: '/builder/new' } } });
        return;
      }
      
      const errorMessage = error?.response?.data?.detail || 'Failed to create diagram. Please try again.';
      setError(errorMessage);
    } finally {
      setIsCreating(false);
    }
  };

  const handleLogin = () => {
    navigate('/login');
  };

  // Filter models based on search query
  const filteredModels = publishedModels.filter(model =>
    model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    model.workspace_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Left Sidebar - RED */}
      <div 
        className="w-64 flex-shrink-0"
        style={{ backgroundColor: COLORS.ERROR }}
      >
        <div className="p-6">
          <h2 className="text-xl font-bold text-white mb-6">
            Published Models
          </h2>
          <div className="space-y-2">
            <button 
              onClick={handleCreateClick}
              className="w-full flex items-center gap-2 px-4 py-3 text-white bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg transition-all"
            >
              <Plus className="w-5 h-5" />
              <span className="font-medium">New Diagram</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto">
        {/* Top Bar */}
        <div className="bg-white border-b border-gray-200 px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex-1 max-w-2xl">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search models..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            
            {/* Auth Status */}
            <div className="ml-4">
              {isAuthenticated ? (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Logged in</span>
                </div>
              ) : (
                <button
                  onClick={handleLogin}
                  className="flex items-center gap-2 px-4 py-2 text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                >
                  <LogIn className="w-4 h-4" />
                  <span className="font-medium">Sign In</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-8">
          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-red-800 font-medium">Error</p>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading published models...</p>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && filteredModels.length === 0 && (
            <div className="text-center py-12">
              <div className="mx-auto w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                <Search className="w-12 h-12 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {searchQuery ? 'No models found' : 'No published models yet'}
              </h3>
              <p className="text-gray-600 mb-6">
                {searchQuery 
                  ? 'Try adjusting your search terms' 
                  : 'Create your first diagram to get started'}
              </p>
              <button
                onClick={handleCreateClick}
                className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-5 h-5" />
                Create New Diagram
              </button>
            </div>
          )}

          {/* Models Grid */}
          {!isLoading && filteredModels.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredModels.map((model) => (
                <ModelCard 
                  key={model.id}
                  name={model.name}
                  workspace={model.workspace_name}
                  author={model.author_name}
                  totalClasses={model.total_classes}
                  totalRelationships={model.total_relationships}
                  onClick={() => navigate(`/builder/${model.id}`)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Diagram Modal */}
      {isCreateModalOpen && (
        <CreateDiagramModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onSubmit={handleCreateDiagram}
          isLoading={isCreating}
        />
      )}
    </div>
  );
};
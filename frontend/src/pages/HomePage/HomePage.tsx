/**
 * Home Page Component
 * Path: frontend/src/pages/HomePage/HomePage.tsx
 * 
 * Displays published models library with red sidebar
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, AlertCircle } from 'lucide-react';
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

  const handleCreateDiagram = async (workspaceName: string, diagramName: string) => {
    try {
      setIsCreating(true);
      
      const response = await apiClient.post<{ id: string }>('/diagrams', {
        workspace_name: workspaceName,
        name: diagramName,
      });

      setIsCreateModalOpen(false);
      
      // Navigate to builder with new diagram ID
      navigate(`/builder/${response.data.id}`);
    } catch (error: any) {
      console.error('Failed to create diagram:', error);
      const errorMessage = error?.response?.data?.detail || 'Failed to create diagram. Please try again.';
      alert(errorMessage);
    } finally {
      setIsCreating(false);
    }
  };

  const handleModelClick = (modelId: string) => {
    navigate(`/builder/${modelId}`);
  };

  // Filter models based on search query
  const filteredModels = publishedModels.filter(model =>
    model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    model.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (model.workspace_name && model.workspace_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (model.author_name && model.author_name.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div 
      className="min-h-screen"
      style={{ backgroundColor: COLORS.OFF_WHITE }}
    >
      {/* Left Sidebar - Red */}
      <aside
        className="fixed left-0 top-0 h-full w-80 shadow-lg z-10"
        style={{ backgroundColor: COLORS.ERROR }}
      >
        <div className="p-6">
          {/* Title */}
          <h1 
            className="text-2xl font-bold mb-6" 
            style={{ color: COLORS.WHITE }}
          >
            Public Models
          </h1>
          
          {/* Search Bar */}
          <div className="relative">
            <Search 
              className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4" 
              style={{ color: COLORS.DARK_GREY }}
            />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name or id"
              className="w-full pl-10 pr-4 py-2 rounded focus:outline-none focus:ring-2"
              style={{ 
                backgroundColor: COLORS.WHITE,
                color: COLORS.BLACK,
                borderColor: COLORS.LIGHT_GREY
              }}
            />
          </div>

          {/* Search Results Count */}
          {searchQuery && (
            <p 
              className="mt-3 text-sm"
              style={{ color: COLORS.WHITE }}
            >
              {filteredModels.length} result{filteredModels.length !== 1 ? 's' : ''} found
            </p>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="ml-80 p-8">
        {/* Header */}
        <header className="flex justify-between items-center mb-8">
          <h2 
            className="text-4xl font-bold" 
            style={{ color: COLORS.BLACK }}
          >
            SEMANTIC ARCHITECT
          </h2>
          
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center gap-2 px-6 py-3 rounded text-white font-semibold transition hover:opacity-90 shadow-md"
            style={{ backgroundColor: COLORS.ERROR }}
          >
            Create
            <Plus className="w-5 h-5" />
          </button>
        </header>

        {/* Error Message */}
        {error && (
          <div 
            className="mb-6 p-4 rounded border flex items-start gap-3"
            style={{ 
              backgroundColor: `${COLORS.ERROR}10`,
              borderColor: COLORS.ERROR,
              color: COLORS.ERROR
            }}
          >
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold">Error loading models</p>
              <p className="text-sm mt-1">{error}</p>
              <button
                onClick={fetchPublishedModels}
                className="mt-2 text-sm underline hover:no-underline"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading ? (
          <div className="text-center py-16">
            <div 
              className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-solid"
              style={{ 
                borderColor: COLORS.LIGHT_GREY,
                borderTopColor: COLORS.PRIMARY
              }}
            />
            <p 
              className="mt-4 text-lg"
              style={{ color: COLORS.DARK_GREY }}
            >
              Loading published models...
            </p>
          </div>
        ) : filteredModels.length === 0 ? (
          /* Empty State */
          <div className="text-center py-16">
            <div
              className="w-24 h-24 mx-auto mb-4 rounded-full flex items-center justify-center"
              style={{ backgroundColor: COLORS.LIGHT_GREY }}
            >
              <Search className="w-12 h-12" style={{ color: COLORS.DARK_GREY }} />
            </div>
            <p 
              className="text-xl mb-2"
              style={{ color: COLORS.BLACK }}
            >
              {searchQuery ? 'No models match your search' : 'Models not yet published'}
            </p>
            <p 
              className="text-sm"
              style={{ color: COLORS.DARK_GREY }}
            >
              {searchQuery 
                ? 'Try adjusting your search terms' 
                : 'Create your first diagram to get started'}
            </p>
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="mt-4 px-4 py-2 rounded transition hover:opacity-90"
                style={{ 
                  backgroundColor: COLORS.PRIMARY,
                  color: COLORS.WHITE
                }}
              >
                Clear search
              </button>
            )}
          </div>
        ) : (
          /* Published Models Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredModels.map((model) => (
              <ModelCard
                key={model.id}
                name={model.name}
                workspace={model.workspace_name}
                author={model.author_name}
                totalClasses={model.total_classes}
                totalRelationships={model.total_relationships}
                onClick={() => handleModelClick(model.id)}
              />
            ))}
          </div>
        )}
      </main>

      {/* Create Modal */}
      <CreateDiagramModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreateDiagram}
        isLoading={isCreating}
      />
    </div>
  );
};

export default HomePage;
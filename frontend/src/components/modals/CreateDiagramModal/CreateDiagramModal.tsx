/**
 * Create Diagram Modal Component
 * Path: frontend/src/components/modals/CreateDiagramModal/CreateDiagramModal.tsx
 * 
 * Modal for creating new diagrams with workspace and diagram name
 */

import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { COLORS } from '../../../constants/colors';

interface CreateDiagramModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (workspaceName: string, diagramName: string) => void;
  isLoading?: boolean;
}

export const CreateDiagramModal: React.FC<CreateDiagramModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
}) => {
  const [workspaceName, setWorkspaceName] = useState('');
  const [diagramName, setDiagramName] = useState('');
  const [error, setError] = useState('');

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setWorkspaceName('');
      setDiagramName('');
      setError('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const validateForm = (): boolean => {
    setError('');

    // Validate workspace name
    if (!workspaceName.trim()) {
      setError('Workspace name is required');
      return false;
    }

    if (workspaceName.trim().length < 3) {
      setError('Workspace name must be at least 3 characters');
      return false;
    }

    if (workspaceName.length > 255) {
      setError('Workspace name must be less than 255 characters');
      return false;
    }

    // Validate diagram name
    if (!diagramName.trim()) {
      setError('Diagram name is required');
      return false;
    }

    if (diagramName.trim().length < 3) {
      setError('Diagram name must be at least 3 characters');
      return false;
    }

    if (diagramName.length > 255) {
      setError('Diagram name must be less than 255 characters');
      return false;
    }

    // Validate characters (alphanumeric, spaces, hyphens, underscores)
    const validNameRegex = /^[a-zA-Z0-9\s\-_]+$/;
    
    if (!validNameRegex.test(workspaceName)) {
      setError('Workspace name can only contain letters, numbers, spaces, hyphens, and underscores');
      return false;
    }

    if (!validNameRegex.test(diagramName)) {
      setError('Diagram name can only contain letters, numbers, spaces, hyphens, and underscores');
      return false;
    }

    return true;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    onSubmit(workspaceName.trim(), diagramName.trim());
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isLoading) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={handleBackdropClick}
    >
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50"
        style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
      />
      
      {/* Modal */}
      <div 
        className="relative rounded-lg shadow-2xl w-full max-w-md"
        style={{ backgroundColor: COLORS.WHITE }}
      >
        {/* Header */}
        <div 
          className="flex items-center justify-between p-6 border-b"
          style={{ borderColor: COLORS.LIGHT_GREY }}
        >
          <h2 
            className="text-2xl font-bold"
            style={{ color: COLORS.BLACK }}
          >
            Create New Diagram
          </h2>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="p-1 rounded transition hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Close modal"
          >
            <X className="w-6 h-6" style={{ color: COLORS.DARK_GREY }} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            {/* Error Message */}
            {error && (
              <div 
                className="p-3 rounded border text-sm"
                style={{ 
                  backgroundColor: `${COLORS.ERROR}10`,
                  borderColor: COLORS.ERROR,
                  color: COLORS.ERROR
                }}
                role="alert"
              >
                {error}
              </div>
            )}

            {/* Workspace Name */}
            <div>
              <label 
                htmlFor="workspace-name" 
                className="block text-sm font-medium mb-1"
                style={{ color: COLORS.BLACK }}
              >
                Workspace Name <span style={{ color: COLORS.ERROR }}>*</span>
              </label>
              <input
                id="workspace-name"
                type="text"
                value={workspaceName}
                onChange={(e) => setWorkspaceName(e.target.value)}
                disabled={isLoading}
                className="w-full px-4 py-2 border rounded focus:outline-none focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ 
                  borderColor: COLORS.LIGHT_GREY,
                  color: COLORS.BLACK,
                }}
                placeholder="My Workspace"
                autoFocus
                required
                minLength={3}
                maxLength={255}
              />
              <p 
                className="mt-1 text-xs"
                style={{ color: COLORS.DARK_GREY }}
              >
                The workspace organizes related diagrams together
              </p>
            </div>

            {/* Diagram Name */}
            <div>
              <label 
                htmlFor="diagram-name" 
                className="block text-sm font-medium mb-1"
                style={{ color: COLORS.BLACK }}
              >
                Diagram Name <span style={{ color: COLORS.ERROR }}>*</span>
              </label>
              <input
                id="diagram-name"
                type="text"
                value={diagramName}
                onChange={(e) => setDiagramName(e.target.value)}
                disabled={isLoading}
                className="w-full px-4 py-2 border rounded focus:outline-none focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ 
                  borderColor: COLORS.LIGHT_GREY,
                  color: COLORS.BLACK,
                }}
                placeholder="Enterprise Logical Diagram"
                required
                minLength={3}
                maxLength={255}
              />
              <p 
                className="mt-1 text-xs"
                style={{ color: COLORS.DARK_GREY }}
              >
                A descriptive name for your ontology model
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 border rounded transition hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ 
                borderColor: COLORS.LIGHT_GREY,
                color: COLORS.BLACK
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2 rounded text-white transition hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ backgroundColor: COLORS.PRIMARY }}
            >
              {isLoading ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
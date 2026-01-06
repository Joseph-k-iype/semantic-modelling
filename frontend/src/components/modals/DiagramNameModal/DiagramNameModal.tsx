// frontend/src/components/modals/DiagramNameModal/DiagramNameModal.tsx
/**
 * Diagram Name Modal - Prompt for workspace and diagram name
 * Shows when saving a new diagram for the first time
 */

import React, { useState } from 'react';
import { X } from 'lucide-react';
import { COLORS } from '../../../constants/colors';

interface DiagramNameModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (workspaceName: string, diagramName: string) => void;
  defaultWorkspace?: string;
  defaultDiagram?: string;
}

export const DiagramNameModal: React.FC<DiagramNameModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  defaultWorkspace = 'default',
  defaultDiagram = 'Untitled Diagram'
}) => {
  const [workspaceName, setWorkspaceName] = useState(defaultWorkspace);
  const [diagramName, setDiagramName] = useState(defaultDiagram);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!workspaceName.trim()) {
      setError('Workspace name is required');
      return;
    }
    
    if (!diagramName.trim()) {
      setError('Diagram name is required');
      return;
    }
    
    // Check for invalid characters
    const invalidChars = /[<>:"/\\|?*]/;
    if (invalidChars.test(workspaceName)) {
      setError('Workspace name contains invalid characters');
      return;
    }
    
    if (invalidChars.test(diagramName)) {
      setError('Diagram name contains invalid characters');
      return;
    }
    
    onSubmit(workspaceName.trim(), diagramName.trim());
    setError('');
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="bg-white rounded-lg shadow-2xl w-full max-w-md"
        style={{ borderColor: COLORS.PRIMARY, borderWidth: 2 }}
      >
        {/* Header */}
        <div
          className="flex justify-between items-center p-4 border-b"
          style={{ borderColor: COLORS.LIGHT_GREY }}
        >
          <h2 className="text-xl font-bold" style={{ color: COLORS.BLACK }}>
            Save Diagram
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
            style={{ color: COLORS.DARK_GREY }}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Error message */}
          {error && (
            <div
              className="p-3 rounded text-sm"
              style={{
                backgroundColor: COLORS.ERROR + '20',
                color: COLORS.ERROR,
                borderLeft: `4px solid ${COLORS.ERROR}`
              }}
            >
              {error}
            </div>
          )}

          {/* Workspace Name */}
          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: COLORS.BLACK }}
            >
              Workspace Name
            </label>
            <input
              type="text"
              value={workspaceName}
              onChange={(e) => setWorkspaceName(e.target.value)}
              placeholder="e.g., E-Commerce, HR System"
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{
                borderColor: COLORS.LIGHT_GREY
              }}
              autoFocus
            />
            <p className="text-xs mt-1" style={{ color: COLORS.DARK_GREY }}>
              Group related diagrams together
            </p>
          </div>

          {/* Diagram Name */}
          <div>
            <label
              className="block text-sm font-medium mb-2"
              style={{ color: COLORS.BLACK }}
            >
              Diagram Name
            </label>
            <input
              type="text"
              value={diagramName}
              onChange={(e) => setDiagramName(e.target.value)}
              placeholder="e.g., Customer Order System"
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{
                borderColor: COLORS.LIGHT_GREY
              }}
            />
            <p className="text-xs mt-1" style={{ color: COLORS.DARK_GREY }}>
              Descriptive name for this diagram
            </p>
          </div>

          {/* Preview */}
          <div
            className="p-3 rounded"
            style={{ backgroundColor: COLORS.OFF_WHITE }}
          >
            <p className="text-xs font-medium mb-1" style={{ color: COLORS.DARK_GREY }}>
              Graph will be created as:
            </p>
            <code
              className="text-sm font-mono"
              style={{ color: COLORS.PRIMARY }}
            >
              {workspaceName.trim() || 'workspace'}/{diagramName.trim() || 'diagram'}
            </code>
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 rounded transition"
              style={{
                backgroundColor: COLORS.OFF_WHITE,
                color: COLORS.BLACK,
                border: `1px solid ${COLORS.LIGHT_GREY}`
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 rounded transition"
              style={{
                backgroundColor: COLORS.PRIMARY,
                color: COLORS.WHITE
              }}
            >
              Save Diagram
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DiagramNameModal;
// frontend/src/components/builder/EdgeEditor/EdgeEditor.tsx
/**
 * Edge Editor Component - Edit edge properties after creation
 * Path: frontend/src/components/builder/EdgeEditor/EdgeEditor.tsx
 * 
 * Allows editing: label, relationship type, cardinality, color
 */

import React, { useState, useEffect } from 'react';
import { Save, X, Trash2 } from 'lucide-react';
import { COLORS } from '../../../constants/colors';
import type { Edge } from 'reactflow';
import type { EdgeData } from '../../../types/diagram.types';

interface EdgeEditorProps {
  selectedEdge: Edge<EdgeData> | null;
  onUpdate: (edgeId: string, updates: Partial<EdgeData>) => void;
  onDelete: (edgeId: string) => void;
  onClose: () => void;
}

export const EdgeEditor: React.FC<EdgeEditorProps> = ({
  selectedEdge,
  onUpdate,
  onDelete,
  onClose,
}) => {
  const [label, setLabel] = useState('');
  const [type, setType] = useState<string>('Association');
  const [sourceCardinality, setSourceCardinality] = useState('1');
  const [targetCardinality, setTargetCardinality] = useState('1');
  const [color, setColor] = useState<string>(COLORS.BLACK);

  // Relationship types
  const relationshipTypes = [
    'Association',
    'Aggregation',
    'Composition',
    'Generalization',
    'Dependency',
    'Realization',
  ];

  // Cardinality options
  const cardinalityOptions = [
    '0..1',
    '1',
    '0..*',
    '1..*',
    '*',
    'n',
  ];

  // Update local state when selected edge changes
  useEffect(() => {
    if (selectedEdge && selectedEdge.data) {
      setLabel(selectedEdge.data.label || '');
      setType(selectedEdge.data.type || 'Association');
      setSourceCardinality(selectedEdge.data.sourceCardinality || '1');
      setTargetCardinality(selectedEdge.data.targetCardinality || '1');
      setColor(selectedEdge.data.color || COLORS.BLACK);
    }
  }, [selectedEdge]);

  if (!selectedEdge) {
    return (
      <div 
        className="w-80 border-l-2 p-6 flex items-center justify-center"
        style={{ 
          backgroundColor: COLORS.OFF_WHITE,
          borderColor: COLORS.LIGHT_GREY
        }}
      >
        <p style={{ color: COLORS.DARK_GREY }}>
          Select an edge to edit
        </p>
      </div>
    );
  }

  const handleSave = () => {
    onUpdate(selectedEdge.id, {
      label,
      type: type as any,
      sourceCardinality,
      targetCardinality,
      color,
    });
  };

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this relationship?')) {
      onDelete(selectedEdge.id);
      onClose();
    }
  };

  return (
    <div
      className="w-80 border-l-2 flex flex-col h-full"
      style={{
        backgroundColor: COLORS.OFF_WHITE,
        borderColor: COLORS.LIGHT_GREY,
      }}
    >
      {/* Header */}
      <div
        className="p-4 flex items-center justify-between border-b-2"
        style={{ borderColor: COLORS.LIGHT_GREY }}
      >
        <h3 className="font-bold text-lg" style={{ color: COLORS.BLACK }}>
          Edit Relationship
        </h3>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-200 rounded"
          title="Close"
        >
          <X className="w-5 h-5" style={{ color: COLORS.DARK_GREY }} />
        </button>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-auto p-4 space-y-6">
        {/* Label */}
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: COLORS.BLACK }}>
            Label
          </label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="e.g., 'manages', 'belongs to'"
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2"
            style={{
              borderColor: COLORS.LIGHT_GREY,
              backgroundColor: COLORS.WHITE,
            }}
          />
          <p className="text-xs mt-1" style={{ color: COLORS.DARK_GREY }}>
            This label will appear on the edge and in FalkorDB
          </p>
        </div>

        {/* Relationship Type */}
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: COLORS.BLACK }}>
            Relationship Type
          </label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2"
            style={{
              borderColor: COLORS.LIGHT_GREY,
              backgroundColor: COLORS.WHITE,
            }}
          >
            {relationshipTypes.map((relType) => (
              <option key={relType} value={relType}>
                {relType}
              </option>
            ))}
          </select>
        </div>

        {/* Source Cardinality */}
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: COLORS.BLACK }}>
            Source Cardinality
          </label>
          <select
            value={sourceCardinality}
            onChange={(e) => setSourceCardinality(e.target.value)}
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2"
            style={{
              borderColor: COLORS.LIGHT_GREY,
              backgroundColor: COLORS.WHITE,
            }}
          >
            {cardinalityOptions.map((card) => (
              <option key={card} value={card}>
                {card}
              </option>
            ))}
          </select>
        </div>

        {/* Target Cardinality */}
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: COLORS.BLACK }}>
            Target Cardinality
          </label>
          <select
            value={targetCardinality}
            onChange={(e) => setTargetCardinality(e.target.value)}
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2"
            style={{
              borderColor: COLORS.LIGHT_GREY,
              backgroundColor: COLORS.WHITE,
            }}
          >
            {cardinalityOptions.map((card) => (
              <option key={card} value={card}>
                {card}
              </option>
            ))}
          </select>
        </div>

        {/* Color */}
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: COLORS.BLACK }}>
            Color
          </label>
          <div className="flex items-center gap-3">
            <input
              type="color"
              value={color}
              onChange={(e) => setColor(e.target.value)}
              className="w-12 h-10 rounded cursor-pointer border"
              style={{ borderColor: COLORS.LIGHT_GREY }}
            />
            <input
              type="text"
              value={color}
              onChange={(e) => setColor(e.target.value)}
              placeholder="#000000"
              className="flex-1 px-3 py-2 border rounded focus:outline-none focus:ring-2"
              style={{
                borderColor: COLORS.LIGHT_GREY,
                backgroundColor: COLORS.WHITE,
              }}
            />
          </div>
        </div>

        {/* Edge Info */}
        <div
          className="p-3 rounded"
          style={{ backgroundColor: COLORS.WHITE }}
        >
          <p className="text-xs font-medium mb-1" style={{ color: COLORS.DARK_GREY }}>
            Edge ID
          </p>
          <p className="text-xs font-mono" style={{ color: COLORS.BLACK }}>
            {selectedEdge.id}
          </p>
          <p className="text-xs font-medium mb-1 mt-2" style={{ color: COLORS.DARK_GREY }}>
            Connection
          </p>
          <p className="text-xs" style={{ color: COLORS.BLACK }}>
            {selectedEdge.source} → {selectedEdge.target}
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div
        className="p-4 border-t-2 flex gap-2"
        style={{ borderColor: COLORS.LIGHT_GREY }}
      >
        <button
          onClick={handleSave}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded transition"
          style={{
            backgroundColor: COLORS.SUCCESS,
            color: COLORS.WHITE,
          }}
        >
          <Save className="w-4 h-4" />
          Save Changes
        </button>
        <button
          onClick={handleDelete}
          className="px-4 py-2 rounded transition"
          style={{
            backgroundColor: COLORS.ERROR,
            color: COLORS.WHITE,
          }}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default EdgeEditor;
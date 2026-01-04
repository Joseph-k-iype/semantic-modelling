/**
 * Cardinality Modal Component
 * Path: frontend/src/components/modals/CardinalityModal/CardinalityModal.tsx
 * 
 * Modal for configuring relationship cardinality and type
 */

import React, { useState } from 'react';
import { X } from 'lucide-react';
import type { Node } from 'reactflow';
import { COLORS } from '../../../constants/colors';
import type { NodeData, RelationshipType } from '../../../types/diagram.types';
import { CARDINALITY_OPTIONS, RELATIONSHIP_TYPE_OPTIONS } from '../../../types/diagram.types';

interface CardinalityModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (config: {
    sourceCardinality: string;
    targetCardinality: string;
    type: string;
    label?: string;
  }) => void;
  sourceNode?: Node<NodeData>;
  targetNode?: Node<NodeData>;
}

export const CardinalityModal: React.FC<CardinalityModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  sourceNode,
  targetNode,
}) => {
  const [relationshipType, setRelationshipType] = useState<RelationshipType>('Association' as RelationshipType);
  const [sourceCardinality, setSourceCardinality] = useState('1');
  const [targetCardinality, setTargetCardinality] = useState('*');
  const [label, setLabel] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      type: relationshipType,
      sourceCardinality,
      targetCardinality,
      label: label.trim() || undefined,
    });
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={handleBackdropClick}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-50" />

      {/* Modal */}
      <div
        className="relative rounded-lg shadow-2xl w-full max-w-lg"
        style={{ backgroundColor: COLORS.WHITE }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between p-6 border-b"
          style={{ borderColor: COLORS.LIGHT_GREY }}
        >
          <h3 className="text-xl font-bold" style={{ color: COLORS.BLACK }}>
            Configure Relationship
          </h3>
          <button
            onClick={onClose}
            className="p-1 rounded transition hover:bg-gray-100"
            aria-label="Close modal"
          >
            <X className="w-6 h-6" style={{ color: COLORS.DARK_GREY }} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-5">
            {/* Connection Info */}
            <div
              className="p-4 rounded"
              style={{ backgroundColor: COLORS.OFF_WHITE }}
            >
              <div className="flex items-center justify-between text-sm">
                <span style={{ color: COLORS.BLACK }} className="font-medium">
                  {sourceNode?.data.label || 'Source'}
                </span>
                <span style={{ color: COLORS.DARK_GREY }}>→</span>
                <span style={{ color: COLORS.BLACK }} className="font-medium">
                  {targetNode?.data.label || 'Target'}
                </span>
              </div>
            </div>

            {/* Relationship Type */}
            <div>
              <label htmlFor="relationship-type" className="block text-sm font-medium mb-2" style={{ color: COLORS.BLACK }}>
                Relationship Type
              </label>
              <select
                id="relationship-type"
                value={relationshipType}
                onChange={(e) => setRelationshipType(e.target.value as RelationshipType)}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2"
                style={{
                  borderColor: COLORS.LIGHT_GREY,
                  color: COLORS.BLACK,
                }}
              >
                {RELATIONSHIP_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs" style={{ color: COLORS.DARK_GREY }}>
                {RELATIONSHIP_TYPE_OPTIONS.find((o) => o.value === relationshipType)?.description}
              </p>
            </div>

            {/* Source Cardinality */}
            <div>
              <label htmlFor="source-cardinality" className="block text-sm font-medium mb-2" style={{ color: COLORS.BLACK }}>
                {sourceNode?.data.label || 'Source'} Cardinality
              </label>
              <select
                id="source-cardinality"
                value={sourceCardinality}
                onChange={(e) => setSourceCardinality(e.target.value)}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2"
                style={{
                  borderColor: COLORS.LIGHT_GREY,
                  color: COLORS.BLACK,
                }}
              >
                {CARDINALITY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Target Cardinality */}
            <div>
              <label htmlFor="target-cardinality" className="block text-sm font-medium mb-2" style={{ color: COLORS.BLACK }}>
                {targetNode?.data.label || 'Target'} Cardinality
              </label>
              <select
                id="target-cardinality"
                value={targetCardinality}
                onChange={(e) => setTargetCardinality(e.target.value)}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2"
                style={{
                  borderColor: COLORS.LIGHT_GREY,
                  color: COLORS.BLACK,
                }}
              >
                {CARDINALITY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Optional Label */}
            <div>
              <label htmlFor="relationship-label" className="block text-sm font-medium mb-2" style={{ color: COLORS.BLACK }}>
                Label (Optional)
              </label>
              <input
                id="relationship-label"
                type="text"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2"
                style={{
                  borderColor: COLORS.LIGHT_GREY,
                  color: COLORS.BLACK,
                }}
                placeholder="Relates To"
              />
              <p className="mt-1 text-xs" style={{ color: COLORS.DARK_GREY }}>
                Custom label for this relationship
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded transition hover:bg-gray-50"
              style={{
                borderColor: COLORS.LIGHT_GREY,
                color: COLORS.BLACK,
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2 rounded text-white transition hover:opacity-90"
              style={{ backgroundColor: COLORS.PRIMARY }}
            >
              Create Relationship
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CardinalityModal;
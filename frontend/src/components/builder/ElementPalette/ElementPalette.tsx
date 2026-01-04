/**
 * Element Palette Component
 * Path: frontend/src/components/builder/ElementPalette/ElementPalette.tsx
 * 
 * Draggable element library for the ontology builder
 */

import React from 'react';
import { COLORS, ELEMENT_COLORS } from '../../../constants/colors';
import type { NodeType } from '../../../types/diagram.types';

interface ElementType {
  id: NodeType;
  label: string;
  color: string;
  borderColor: string;
}

const ELEMENT_TYPES: ElementType[] = [
  {
    id: 'package' as NodeType,
    label: 'Package',
    color: ELEMENT_COLORS.package,
    borderColor: COLORS.BLACK,
  },
  {
    id: 'class' as NodeType,
    label: 'Class',
    color: ELEMENT_COLORS.class,
    borderColor: COLORS.BLACK,
  },
  {
    id: 'object' as NodeType,
    label: 'Object',
    color: ELEMENT_COLORS.object,
    borderColor: COLORS.BLACK,
  },
  {
    id: 'interface' as NodeType,
    label: 'Interface',
    color: ELEMENT_COLORS.interface,
    borderColor: COLORS.BLACK,
  },
  {
    id: 'enumeration' as NodeType,
    label: 'Enumeration',
    color: ELEMENT_COLORS.enumeration,
    borderColor: COLORS.BLACK,
  },
];

interface DraggableElementProps {
  type: ElementType;
}

const DraggableElement: React.FC<DraggableElementProps> = ({ type }) => {
  const onDragStart = (event: React.DragEvent) => {
    event.dataTransfer.setData('application/reactflow', type.id);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      draggable
      onDragStart={onDragStart}
      className="border-2 rounded p-3 cursor-move transition hover:shadow-md"
      style={{
        borderColor: type.borderColor,
        backgroundColor: COLORS.OFF_WHITE,
      }}
    >
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded flex-shrink-0"
          style={{ backgroundColor: type.color }}
        />
        <span className="text-sm font-medium" style={{ color: COLORS.BLACK }}>
          {type.label}
        </span>
      </div>
    </div>
  );
};

const RelationshipTypes: React.FC = () => {
  const relationships = [
    { name: 'Association', symbol: '———' },
    { name: 'Inheritance', symbol: '◁───' },
    { name: 'Composition', symbol: '◆───' },
    { name: 'Aggregation', symbol: '◇───' },
    { name: 'Dependency', symbol: '- - -' },
    { name: 'Realization', symbol: '◁- -' },
  ];

  return (
    <div className="space-y-2">
      {relationships.map((rel) => (
        <div
          key={rel.name}
          className="p-2 rounded"
          style={{ backgroundColor: COLORS.OFF_WHITE }}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium" style={{ color: COLORS.BLACK }}>
              {rel.name}
            </span>
            <span className="text-xs font-mono" style={{ color: COLORS.DARK_GREY }}>
              {rel.symbol}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

export const ElementPalette: React.FC = () => {
  return (
    <div className="space-y-4">
      {/* Element Types */}
      <div>
        <h3 className="text-sm font-semibold mb-3" style={{ color: COLORS.BLACK }}>
          Elements
        </h3>
        <div className="space-y-2">
          {ELEMENT_TYPES.map((type) => (
            <DraggableElement key={type.id} type={type} />
          ))}
        </div>
      </div>

      {/* Relationship Types */}
      <div className="pt-4 border-t" style={{ borderColor: COLORS.LIGHT_GREY }}>
        <h3 className="text-sm font-semibold mb-3" style={{ color: COLORS.BLACK }}>
          Relationships
        </h3>
        <p className="text-xs mb-3" style={{ color: COLORS.DARK_GREY }}>
          Connect elements to create relationships
        </p>
        <RelationshipTypes />
      </div>
    </div>
  );
};

export default ElementPalette;
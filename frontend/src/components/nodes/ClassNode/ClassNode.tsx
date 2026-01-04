/**
 * Class Node Component
 * Path: frontend/src/components/nodes/ClassNode/ClassNode.tsx
 * 
 * Universal node component for all UML element types
 * Handles: Package, Class, Object, Interface, Enumeration
 */

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { COLORS, getTextColor } from '../../../constants/colors';
import type { NodeData, Attribute, Method } from '../../../types/diagram.types';

export const ClassNode: React.FC<NodeProps<NodeData>> = memo(({ data, selected }) => {
  const isPackage = data.type === 'package';
  const isEnumeration = data.type === 'enumeration';
  const hasAttributes = 'attributes' in data && Array.isArray(data.attributes);
  const hasMethods = 'methods' in data && Array.isArray(data.methods);
  const hasLiterals = 'literals' in data && Array.isArray(data.literals);

  const textColor = getTextColor(data.color);
  const borderColor = selected ? COLORS.BLACK : COLORS.DARK_GREY;

  return (
    <div
      className="rounded border-2 shadow-md min-w-[200px]"
      style={{
        backgroundColor: data.color,
        borderColor: borderColor,
        borderWidth: selected ? '3px' : '2px',
      }}
    >
      {/* Connection handles */}
      <Handle type="target" position={Position.Top} style={{ background: COLORS.BLACK }} />
      <Handle type="source" position={Position.Bottom} style={{ background: COLORS.BLACK }} />
      <Handle type="target" position={Position.Left} style={{ background: COLORS.BLACK }} />
      <Handle type="source" position={Position.Right} style={{ background: COLORS.BLACK }} />

      {/* Header with stereotype and name */}
      <div
        className="px-4 py-2 border-b-2"
        style={{
          borderColor: COLORS.BLACK,
          color: textColor,
        }}
      >
        {data.stereotype && (
          <div className="text-xs text-center mb-1">
            &lt;&lt;{data.stereotype}&gt;&gt;
          </div>
        )}
        <div className="font-bold text-center">{data.label}</div>
      </div>

      {/* Attributes Section (for Class, Object) */}
      {hasAttributes && data.attributes && data.attributes.length > 0 && (
        <div
          className="p-2 space-y-1 border-b"
          style={{
            backgroundColor: `${COLORS.WHITE}CC`,
            borderColor: COLORS.LIGHT_GREY,
          }}
        >
          {data.attributes.map((attr: Attribute, idx: number) => (
            <div
              key={attr.id || idx}
              className="flex justify-between text-xs font-mono gap-4 px-2"
              style={{ color: COLORS.BLACK }}
            >
              <span className="truncate">{attr.name}</span>
              <span className="text-gray-600 flex-shrink-0">{attr.dataType}</span>
              <span className="text-gray-500 text-[10px] flex-shrink-0">
                {attr.key === 'PRIMARY KEY' && 'PK'}
                {attr.key === 'FOREIGN KEY' && 'FK'}
                {attr.key === 'Default' && 'ID'}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Methods Section (for Interface, Class) */}
      {hasMethods && data.methods && data.methods.length > 0 && (
        <div
          className="p-2 space-y-1"
          style={{
            backgroundColor: `${COLORS.WHITE}CC`,
            color: COLORS.BLACK,
          }}
        >
          {data.methods.map((method: Method, idx: number) => (
            <div
              key={method.id || idx}
              className="text-xs font-mono px-2"
            >
              <span className="truncate">
                {method.name}({method.parameters?.map(p => `${p.name}: ${p.type}`).join(', ')})
              </span>
              {method.returnType && (
                <span className="text-gray-600"> : {method.returnType}</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Enumeration Literals */}
      {hasLiterals && data.literals && data.literals.length > 0 && (
        <div
          className="p-2 space-y-1"
          style={{
            backgroundColor: `${COLORS.WHITE}CC`,
            color: COLORS.BLACK,
          }}
        >
          {data.literals.map((literal: string, idx: number) => (
            <div
              key={idx}
              className="text-xs font-mono px-2 text-center"
            >
              {literal}
            </div>
          ))}
        </div>
      )}

      {/* Empty package indicator */}
      {isPackage && (
        <div
          className="p-4 text-xs italic text-center"
          style={{
            backgroundColor: `${COLORS.WHITE}CC`,
            color: COLORS.DARK_GREY,
          }}
        >
          Package
        </div>
      )}
    </div>
  );
});

ClassNode.displayName = 'ClassNode';

export default ClassNode;
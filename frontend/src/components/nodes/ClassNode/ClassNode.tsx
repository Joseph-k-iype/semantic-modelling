/**
 * Class Node Component - Universal node for all UML element types
 * Path: frontend/src/components/nodes/ClassNode/ClassNode.tsx
 * 
 * IMPROVEMENTS:
 * - Inline name editing (double-click on name)
 * - Better visual hierarchy
 * - Shows attributes, methods, literals
 * - Handles all 5 node types (excluding Package)
 */

import React, { memo, useState, useCallback, useRef, useEffect } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { COLORS, getTextColor } from '../../../constants/colors';
import type { NodeData, Attribute, Method } from '../../../types/diagram.types';

export const ClassNode: React.FC<NodeProps<NodeData>> = memo(({ id, data, selected }) => {
  const [isEditingName, setIsEditingName] = useState(false);
  const [tempName, setTempName] = useState(data.label);
  const inputRef = useRef<HTMLInputElement>(null);

  const isPackage = data.type === 'package';
  const isEnumeration = data.type === 'enumeration';
  const hasAttributes = 'attributes' in data && Array.isArray(data.attributes);
  const hasMethods = 'methods' in data && Array.isArray(data.methods);
  const hasLiterals = 'literals' in data && Array.isArray(data.literals);

  const textColor = getTextColor(data.color);
  const borderColor = selected ? COLORS.PRIMARY : COLORS.DARK_GREY;

  useEffect(() => {
    if (isEditingName && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditingName]);

  const handleNameDoubleClick = useCallback(() => {
    setIsEditingName(true);
    setTempName(data.label);
  }, [data.label]);

  const handleNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setTempName(e.target.value);
  }, []);

  const handleNameBlur = useCallback(() => {
    setIsEditingName(false);
    if (tempName.trim() && tempName !== data.label) {
      // Update through global function if available
      if (window.updateNodeData) {
        window.updateNodeData(id, { label: tempName.trim() });
      }
    }
  }, [id, tempName, data.label]);

  const handleNameKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleNameBlur();
    } else if (e.key === 'Escape') {
      setTempName(data.label);
      setIsEditingName(false);
    }
  }, [handleNameBlur, data.label]);

  return (
    <div
      className="rounded border-2 shadow-lg min-w-[200px] max-w-[400px]"
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
        onDoubleClick={handleNameDoubleClick}
      >
        {data.stereotype && (
          <div className="text-xs text-center mb-1">
            &lt;&lt;{data.stereotype}&gt;&gt;
          </div>
        )}
        <div className="font-bold text-center">
          {isEditingName ? (
            <input
              ref={inputRef}
              type="text"
              value={tempName}
              onChange={handleNameChange}
              onBlur={handleNameBlur}
              onKeyDown={handleNameKeyDown}
              className="w-full text-center px-2 py-1 rounded border"
              style={{
                backgroundColor: COLORS.WHITE,
                color: COLORS.BLACK,
                borderColor: COLORS.PRIMARY,
              }}
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <span className="cursor-pointer hover:opacity-80" title="Double-click to edit">
              {data.label}
            </span>
          )}
        </div>
      </div>

      {/* Attributes Section (for Class, Object) */}
      {hasAttributes && data.attributes && data.attributes.length > 0 && (
        <div
          className="p-2 space-y-1 border-b"
          style={{
            backgroundColor: `${COLORS.WHITE}DD`,
            borderColor: COLORS.LIGHT_GREY,
          }}
        >
          {data.attributes.map((attr: Attribute, idx: number) => (
            <div
              key={attr.id || idx}
              className="flex justify-between text-xs font-mono gap-4 px-2 py-1"
              style={{ color: COLORS.BLACK }}
            >
              <span className="flex items-center gap-1">
                {attr.visibility === 'public' && '+'}
                {attr.visibility === 'private' && '-'}
                {attr.visibility === 'protected' && '#'}
                {attr.visibility === 'package' && '~'}
                <span className="font-medium">{attr.name}</span>
              </span>
              <span className="text-gray-600 flex-shrink-0">
                : {attr.dataType}
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
            backgroundColor: `${COLORS.WHITE}DD`,
            color: COLORS.BLACK,
          }}
        >
          {data.methods.map((method: Method, idx: number) => (
            <div
              key={method.id || idx}
              className="text-xs font-mono px-2 py-1"
            >
              <span className="flex items-center gap-1">
                {method.visibility === 'public' && '+'}
                {method.visibility === 'private' && '-'}
                {method.visibility === 'protected' && '#'}
                {method.visibility === 'package' && '~'}
                <span className="font-medium">
                  {method.name}
                  ({method.parameters?.map(p => `${p.name}: ${p.type}`).join(', ')})
                </span>
                {method.returnType && method.returnType !== 'void' && (
                  <span className="text-gray-600"> : {method.returnType}</span>
                )}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Enumeration Literals */}
      {hasLiterals && data.literals && data.literals.length > 0 && (
        <div
          className="p-2 space-y-1"
          style={{
            backgroundColor: `${COLORS.WHITE}DD`,
            color: COLORS.BLACK,
          }}
        >
          {data.literals.map((literal: string, idx: number) => (
            <div
              key={idx}
              className="text-xs font-mono px-2 py-1 text-center font-bold"
            >
              {literal}
            </div>
          ))}
        </div>
      )}

      {/* Empty state indicators */}
      {hasAttributes && (!data.attributes || data.attributes.length === 0) && (
        <div
          className="p-3 text-xs text-center italic border-b"
          style={{
            backgroundColor: `${COLORS.WHITE}DD`,
            borderColor: COLORS.LIGHT_GREY,
            color: COLORS.DARK_GREY,
          }}
        >
          No attributes yet
        </div>
      )}

      {hasMethods && (!data.methods || data.methods.length === 0) && (
        <div
          className="p-3 text-xs text-center italic"
          style={{
            backgroundColor: `${COLORS.WHITE}DD`,
            color: COLORS.DARK_GREY,
          }}
        >
          No methods yet
        </div>
      )}

      {hasLiterals && (!data.literals || data.literals.length === 0) && (
        <div
          className="p-3 text-xs text-center italic"
          style={{
            backgroundColor: `${COLORS.WHITE}DD`,
            color: COLORS.DARK_GREY,
          }}
        >
          No literals yet
        </div>
      )}

      {/* Help text for empty nodes */}
      {((hasAttributes && (!data.attributes || data.attributes.length === 0)) ||
        (hasMethods && (!data.methods || data.methods.length === 0)) ||
        (hasLiterals && (!data.literals || data.literals.length === 0))) && (
        <div
          className="px-3 pb-2 text-xs text-center"
          style={{ color: COLORS.DARK_GREY }}
        >
          Select and use the editor panel to add content →
        </div>
      )}
    </div>
  );
});

ClassNode.displayName = 'ClassNode';

export default ClassNode;

// Global function for updating node data
declare global {
  interface Window {
    updateNodeData?: (nodeId: string, updates: Partial<NodeData>) => void;
  }
}
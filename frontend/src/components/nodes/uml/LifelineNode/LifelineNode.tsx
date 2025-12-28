// frontend/src/components/nodes/uml/LifelineNode/LifelineNode.tsx

import React, { memo, useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export interface LifelineNodeData {
  label: string;
  stereotype?: string;
  color?: string;
  textColor?: string;
  lifelineHeight?: number;
  zIndex?: number;
}

const LifelineNode: React.FC<NodeProps<LifelineNodeData>> = memo(({ id, data, selected }) => {
  const [isEditingLabel, setIsEditingLabel] = useState(false);
  const [label, setLabel] = useState(data.label || 'Object');
  const [isEditingStereotype, setIsEditingStereotype] = useState(false);
  const [stereotype, setStereotype] = useState(data.stereotype || '');

  const lifelineHeight = data.lifelineHeight || 400;

  const handleLabelChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setLabel(e.target.value);
  }, []);

  const handleLabelBlur = useCallback(() => {
    setIsEditingLabel(false);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label, stereotype });
    }
  }, [id, label, stereotype]);

  const handleStereotypeChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setStereotype(e.target.value);
  }, []);

  const handleStereotypeBlur = useCallback(() => {
    setIsEditingStereotype(false);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label, stereotype });
    }
  }, [id, label, stereotype]);

  const handleLabelKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleLabelBlur();
    } else if (e.key === 'Escape') {
      setIsEditingLabel(false);
      setLabel(data.label || 'Object');
    }
  }, [handleLabelBlur, data.label]);

  const handleStereotypeKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleStereotypeBlur();
    } else if (e.key === 'Escape') {
      setIsEditingStereotype(false);
      setStereotype(data.stereotype || '');
    }
  }, [handleStereotypeBlur, data.stereotype]);

  return (
    <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      {/* Object Box */}
      <div
        style={{
          background: data.color || 'white',
          border: `2px solid ${selected ? '#3b82f6' : '#374151'}`,
          borderRadius: '4px',
          padding: '8px 16px',
          minWidth: '100px',
          boxShadow: selected ? '0 0 0 3px rgba(59, 130, 246, 0.3)' : '0 1px 3px rgba(0,0,0,0.1)',
          position: 'relative',
          zIndex: data.zIndex || 1
        }}
      >
        {/* Stereotype */}
        {(stereotype || isEditingStereotype) && (
          <div
            style={{
              textAlign: 'center',
              marginBottom: '4px'
            }}
            onDoubleClick={() => setIsEditingStereotype(true)}
          >
            {isEditingStereotype ? (
              <input
                type="text"
                value={stereotype}
                onChange={handleStereotypeChange}
                onBlur={handleStereotypeBlur}
                onKeyDown={handleStereotypeKeyDown}
                placeholder="«stereotype»"
                autoFocus
                style={{
                  width: '100%',
                  padding: '2px',
                  fontSize: '10px',
                  border: '1px solid #3b82f6',
                  borderRadius: '2px',
                  outline: 'none',
                  textAlign: 'center',
                  fontStyle: 'italic'
                }}
              />
            ) : (
              <div
                style={{
                  fontSize: '10px',
                  fontStyle: 'italic',
                  color: data.textColor || '#6b7280',
                  cursor: 'text'
                }}
              >
                «{stereotype}»
              </div>
            )}
          </div>
        )}

        {/* Object Name */}
        <div
          style={{
            textAlign: 'center'
          }}
          onDoubleClick={() => setIsEditingLabel(true)}
        >
          {isEditingLabel ? (
            <input
              type="text"
              value={label}
              onChange={handleLabelChange}
              onBlur={handleLabelBlur}
              onKeyDown={handleLabelKeyDown}
              autoFocus
              style={{
                width: '100%',
                padding: '2px',
                fontSize: '12px',
                border: '2px solid #3b82f6',
                borderRadius: '3px',
                outline: 'none',
                textAlign: 'center',
                fontWeight: 'bold'
              }}
            />
          ) : (
            <div
              style={{
                fontSize: '12px',
                fontWeight: 'bold',
                cursor: 'text',
                color: data.textColor || '#374151'
              }}
            >
              {label}
            </div>
          )}
        </div>
      </div>

      {/* Lifeline (dashed vertical line) */}
      <svg
        width="2"
        height={lifelineHeight}
        style={{
          overflow: 'visible'
        }}
      >
        <line
          x1="1"
          y1="0"
          x2="1"
          y2={lifelineHeight}
          stroke={selected ? '#3b82f6' : '#6b7280'}
          strokeWidth="2"
          strokeDasharray="5,5"
        />
      </svg>

      {/* Handles for messages */}
      <Handle
        type="target"
        position={Position.Left}
        style={{
          background: '#6b7280',
          width: '8px',
          height: '8px',
          border: '2px solid white',
          left: '-50px',
          top: '50px'
        }}
      />
      <Handle
        type="source"
        position={Position.Right}
        style={{
          background: '#6b7280',
          width: '8px',
          height: '8px',
          border: '2px solid white',
          right: '-50px',
          top: '50px'
        }}
      />
    </div>
  );
});

LifelineNode.displayName = 'LifelineNode';

export default LifelineNode;
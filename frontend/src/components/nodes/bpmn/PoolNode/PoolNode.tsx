// frontend/src/components/nodes/bpmn/PoolNode/PoolNode.tsx

import React, { memo, useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export type PoolType = 'pool' | 'lane';

export interface PoolNodeData {
  label: string;
  poolType: PoolType;
  color?: string;
  textColor?: string;
  width?: number;
  height?: number;
  zIndex?: number;
}

const PoolNode: React.FC<NodeProps<PoolNodeData>> = memo(({ id, data, selected }) => {
  const [isEditingLabel, setIsEditingLabel] = useState(false);
  const [label, setLabel] = useState(data.label || 'Pool');

  const width = data.width || 400;
  const height = data.height || 200;

  const handleLabelChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setLabel(e.target.value);
  }, []);

  const handleLabelBlur = useCallback(() => {
    setIsEditingLabel(false);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label });
    }
  }, [id, label]);

  const handleLabelKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleLabelBlur();
    } else if (e.key === 'Escape') {
      setIsEditingLabel(false);
      setLabel(data.label || 'Pool');
    }
  }, [handleLabelBlur, data.label]);

  const isPool = data.poolType === 'pool';

  return (
    <div style={{ position: 'relative' }}>
      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        style={{
          background: '#6b7280',
          width: '8px',
          height: '8px',
          border: '2px solid white',
          top: '50%'
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
          top: '50%'
        }}
      />

      {/* Pool/Lane Container */}
      <div
        style={{
          width: `${width}px`,
          height: `${height}px`,
          background: data.color || '#f0f9ff',
          border: `${isPool ? 3 : 2}px solid ${selected ? '#3b82f6' : '#64748b'}`,
          borderRadius: '4px',
          display: 'flex',
          position: 'relative',
          boxShadow: selected ? '0 0 0 3px rgba(59, 130, 246, 0.3)' : 'none',
          zIndex: data.zIndex || 0
        }}
      >
        {/* Label Bar (vertical) */}
        <div
          style={{
            width: '30px',
            height: '100%',
            background: isPool ? '#0284c7' : '#64748b',
            borderTopLeftRadius: '2px',
            borderBottomLeftRadius: '2px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
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
                width: '20px',
                padding: '2px',
                fontSize: '11px',
                border: '2px solid #3b82f6',
                borderRadius: '3px',
                outline: 'none',
                textAlign: 'center',
                transform: 'rotate(-90deg)',
                transformOrigin: 'center'
              }}
            />
          ) : (
            <div
              style={{
                color: 'white',
                fontSize: '12px',
                fontWeight: 'bold',
                writingMode: 'vertical-rl',
                transform: 'rotate(180deg)',
                cursor: 'text',
                userSelect: 'none'
              }}
            >
              {label}
            </div>
          )}
        </div>

        {/* Content Area */}
        <div
          style={{
            flex: 1,
            padding: '8px',
            position: 'relative'
          }}
        >
          {/* Placeholder text */}
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              color: '#94a3b8',
              fontSize: '11px',
              fontStyle: 'italic',
              pointerEvents: 'none'
            }}
          >
            Drop tasks here
          </div>
        </div>
      </div>
    </div>
  );
});

PoolNode.displayName = 'PoolNode';

export default PoolNode;
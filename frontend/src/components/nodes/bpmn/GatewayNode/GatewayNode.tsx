// frontend/src/components/nodes/bpmn/GatewayNode/GatewayNode.tsx

import React, { memo, useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Plus, Circle } from 'lucide-react';

export type GatewayType = 'exclusive' | 'parallel' | 'inclusive' | 'event-based';

export interface GatewayNodeData {
  label: string;
  gatewayType: GatewayType;
  color?: string;
  textColor?: string;
  zIndex?: number;
}

const GatewayNode: React.FC<NodeProps<GatewayNodeData>> = memo(({ id, data, selected }) => {
  const [isEditingLabel, setIsEditingLabel] = useState(false);
  const [label, setLabel] = useState(data.label || 'Gateway');

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
      setLabel(data.label || 'Gateway');
    }
  }, [handleLabelBlur, data.label]);

  const getGatewayIcon = () => {
    switch (data.gatewayType) {
      case 'exclusive':
        return <span style={{ fontSize: '24px', fontWeight: 'bold' }}>×</span>;
      case 'parallel':
        return <Plus size={24} strokeWidth={3} />;
      case 'inclusive':
        return <Circle size={20} strokeWidth={3} />;
      case 'event-based':
        return <Circle size={16} strokeWidth={2} />;
      default:
        return null;
    }
  };

  const diamondSize = 60;
  const borderColor = selected ? '#3b82f6' : '#f59e0b';

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
          left: '0',
          top: '50%',
          transform: 'translate(-50%, -50%)'
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
          right: '0',
          top: '50%',
          transform: 'translate(50%, -50%)'
        }}
      />
      <Handle
        type="source"
        position={Position.Top}
        style={{
          background: '#6b7280',
          width: '8px',
          height: '8px',
          border: '2px solid white',
          top: '0',
          left: '50%',
          transform: 'translate(-50%, -50%)'
        }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        style={{
          background: '#6b7280',
          width: '8px',
          height: '8px',
          border: '2px solid white',
          bottom: '0',
          left: '50%',
          transform: 'translate(-50%, 50%)'
        }}
      />

      {/* Diamond Gateway */}
      <div
        style={{
          width: `${diamondSize}px`,
          height: `${diamondSize}px`,
          transform: 'rotate(45deg)',
          background: data.color || 'white',
          border: `3px solid ${borderColor}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: selected ? `0 0 0 3px ${borderColor}40` : 'none',
          position: 'relative',
          zIndex: data.zIndex || 1
        }}
      >
        <div
          style={{
            transform: 'rotate(-45deg)',
            color: data.textColor || '#f59e0b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {getGatewayIcon()}
        </div>
      </div>

      {/* Label */}
      <div
        style={{
          position: 'absolute',
          top: '75px',
          left: '50%',
          transform: 'translateX(-50%)',
          whiteSpace: 'nowrap',
          textAlign: 'center',
          minWidth: '100px'
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
              padding: '2px 6px',
              fontSize: '11px',
              border: '2px solid #3b82f6',
              borderRadius: '3px',
              outline: 'none',
              textAlign: 'center',
              minWidth: '100px'
            }}
          />
        ) : (
          <div
            style={{
              padding: '2px 6px',
              fontSize: '11px',
              cursor: 'text',
              color: data.textColor || '#374151',
              fontWeight: '500'
            }}
          >
            {label}
          </div>
        )}
      </div>
    </div>
  );
});

GatewayNode.displayName = 'GatewayNode';

export default GatewayNode;
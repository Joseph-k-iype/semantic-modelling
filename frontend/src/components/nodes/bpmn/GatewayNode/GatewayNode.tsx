// frontend/src/components/nodes/bpmn/GatewayNode/GatewayNode.tsx

import React, { memo, useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { X, Plus, Circle } from 'lucide-react';

export type GatewayType = 'exclusive' | 'parallel' | 'inclusive' | 'event' | 'complex';

export interface GatewayNodeData {
  label: string;
  gatewayType: GatewayType;
  color?: string;
  textColor?: string;
  zIndex?: number;
}

const GatewayNode: React.FC<NodeProps<GatewayNodeData>> = ({ data, selected, id }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [gatewayName, setGatewayName] = useState(data.label);

  const handleNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setGatewayName(e.target.value);
  }, []);

  const handleNameBlur = useCallback(() => {
    setIsEditing(false);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label: gatewayName });
    }
  }, [id, gatewayName]);

  const backgroundColor = data.color || '#ffffcc';
  const textColor = data.textColor || '#000000';
  const gatewayType = data.gatewayType || 'exclusive';

  const getGatewayIcon = () => {
    switch (gatewayType) {
      case 'exclusive':
        return <X size={24} color={textColor} strokeWidth={3} />;
      case 'parallel':
        return <Plus size={24} color={textColor} strokeWidth={3} />;
      case 'inclusive':
        return <Circle size={24} color={textColor} strokeWidth={3} />;
      case 'event':
        return (
          <div style={{ position: 'relative' }}>
            <Circle size={20} color={textColor} strokeWidth={2} />
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '12px',
              height: '12px',
              border: `2px solid ${textColor}`,
              borderRadius: '50%'
            }} />
          </div>
        );
      case 'complex':
        return <div style={{ fontSize: '20px', fontWeight: 'bold' }}>*</div>;
      default:
        return <X size={24} color={textColor} />;
    }
  };

  return (
    <div style={{ position: 'relative', zIndex: data.zIndex || 1 }}>
      <div 
        className="gateway-node"
        style={{
          width: '60px',
          height: '60px',
          backgroundColor,
          border: `2px solid ${textColor}`,
          transform: 'rotate(45deg)',
          boxShadow: selected ? '0 0 0 2px #3b82f6' : '0 2px 4px rgba(0,0,0,0.1)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          position: 'relative'
        }}
      >
        <Handle type="target" position={Position.Top} id="top" style={{ transform: 'rotate(-45deg)' }} />
        <Handle type="target" position={Position.Left} id="left" style={{ transform: 'rotate(-45deg)' }} />
        <Handle type="target" position={Position.Right} id="right" style={{ transform: 'rotate(-45deg)' }} />
        <Handle type="target" position={Position.Bottom} id="bottom" style={{ transform: 'rotate(-45deg)' }} />
        
        <Handle type="source" position={Position.Top} id="top-source" style={{ transform: 'rotate(-45deg)' }} />
        <Handle type="source" position={Position.Left} id="left-source" style={{ transform: 'rotate(-45deg)' }} />
        <Handle type="source" position={Position.Right} id="right-source" style={{ transform: 'rotate(-45deg)' }} />
        <Handle type="source" position={Position.Bottom} id="bottom-source" style={{ transform: 'rotate(-45deg)' }} />

        <div style={{ transform: 'rotate(-45deg)' }}>
          {getGatewayIcon()}
        </div>
      </div>

      {/* Gateway Label */}
      <div 
        style={{
          position: 'absolute',
          top: '70px',
          left: '50%',
          transform: 'translateX(-50%)',
          minWidth: '100px',
          textAlign: 'center',
          fontSize: '11px',
          color: textColor,
          whiteSpace: 'nowrap'
        }}
      >
        {isEditing ? (
          <input
            type="text"
            value={gatewayName}
            onChange={handleNameChange}
            onBlur={handleNameBlur}
            autoFocus
            style={{
              width: '100%',
              border: 'none',
              background: 'white',
              color: textColor,
              fontSize: '11px',
              textAlign: 'center',
              outline: 'none',
              padding: '2px'
            }}
          />
        ) : (
          <div 
            onDoubleClick={() => setIsEditing(true)}
            style={{ cursor: 'text' }}
          >
            {gatewayName || gatewayType}
          </div>
        )}
      </div>
    </div>
  );
};

export default memo(GatewayNode);
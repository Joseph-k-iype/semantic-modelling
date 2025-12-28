// frontend/src/components/nodes/uml/LifelineNode/LifelineNode.tsx

import React, { memo, useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { User, Database, Server, Globe } from 'lucide-react';

export type LifelineType = 'actor' | 'object' | 'boundary' | 'control' | 'entity';

export interface Activation {
  id: string;
  startY: number;
  endY: number;
}

export interface LifelineNodeData {
  label: string;
  type: LifelineType;
  stereotype?: string;
  activations: Activation[];
  color?: string;
  textColor?: string;
  lineHeight?: number;
  zIndex?: number;
}

const LifelineNode: React.FC<NodeProps<LifelineNodeData>> = ({ data, selected, id }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(data.label);
  const [stereotype, setStereotype] = useState(data.stereotype || '');

  const handleNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setName(e.target.value);
  }, []);

  const handleNameBlur = useCallback(() => {
    setIsEditing(false);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label: name, stereotype });
    }
  }, [id, name, stereotype]);

  const backgroundColor = data.color || '#ffffff';
  const textColor = data.textColor || '#000000';
  const lineHeight = data.lineHeight || 400;
  const lifelineType = data.type || 'object';

  const getIcon = () => {
    switch (lifelineType) {
      case 'actor':
        return <User size={24} color={textColor} />;
      case 'entity':
        return <Database size={24} color={textColor} />;
      case 'control':
        return <Server size={24} color={textColor} />;
      case 'boundary':
        return <Globe size={24} color={textColor} />;
      default:
        return null;
    }
  };

  return (
    <div 
      className="lifeline-node"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        zIndex: data.zIndex || 1
      }}
    >
      <Handle type="target" position={Position.Top} id="top" />
      <Handle type="source" position={Position.Top} id="top-source" />

      {/* Lifeline Header */}
      <div 
        style={{
          minWidth: '100px',
          padding: '12px 16px',
          backgroundColor,
          border: `2px solid ${textColor}`,
          borderRadius: lifelineType === 'actor' ? '50%' : '4px',
          boxShadow: selected ? '0 0 0 2px #3b82f6' : '0 2px 4px rgba(0,0,0,0.1)',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '4px'
        }}
      >
        {getIcon()}
        
        {stereotype && (
          <div style={{ fontSize: '10px', color: `${textColor}99` }}>
            «{stereotype}»
          </div>
        )}
        
        {isEditing ? (
          <input
            type="text"
            value={name}
            onChange={handleNameChange}
            onBlur={handleNameBlur}
            autoFocus
            style={{
              width: '100%',
              border: 'none',
              background: 'transparent',
              color: textColor,
              fontWeight: 'bold',
              textAlign: 'center',
              outline: 'none',
              fontSize: '12px'
            }}
          />
        ) : (
          <div 
            onDoubleClick={() => setIsEditing(true)}
            style={{ 
              cursor: 'text',
              fontWeight: 'bold',
              fontSize: '12px',
              color: textColor
            }}
          >
            {name}
          </div>
        )}
      </div>

      {/* Lifeline */}
      <div 
        style={{
          width: '2px',
          height: `${lineHeight}px`,
          backgroundColor: textColor,
          borderLeft: '1px dashed',
          borderRight: '1px dashed',
          position: 'relative',
          marginTop: '8px'
        }}
      >
        {/* Activation Boxes */}
        {(data.activations || []).map((activation) => (
          <div
            key={activation.id}
            style={{
              position: 'absolute',
              left: '-6px',
              top: `${activation.startY}px`,
              width: '14px',
              height: `${activation.endY - activation.startY}px`,
              backgroundColor,
              border: `1px solid ${textColor}`,
              boxShadow: '2px 2px 4px rgba(0,0,0,0.2)'
            }}
          />
        ))}
      </div>

      <Handle type="source" position={Position.Bottom} id="bottom-source" />
      <Handle type="target" position={Position.Bottom} id="bottom" />
    </div>
  );
};

export default memo(LifelineNode);
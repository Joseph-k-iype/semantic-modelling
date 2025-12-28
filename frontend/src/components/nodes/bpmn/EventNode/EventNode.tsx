// frontend/src/components/nodes/bpmn/EventNode/EventNode.tsx

import React, { memo, useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Play, Clock, Mail, AlertCircle, XCircle } from 'lucide-react';

export type EventType = 'start' | 'intermediate' | 'end';
export type EventTrigger = 'none' | 'message' | 'timer' | 'error' | 'signal' | 'terminate';

export interface EventNodeData {
  label: string;
  eventType: EventType;
  trigger: EventTrigger;
  color?: string;
  textColor?: string;
  zIndex?: number;
}

const EventNode: React.FC<NodeProps<EventNodeData>> = ({ data, selected, id }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [eventName, setEventName] = useState(data.label);

  const handleNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setEventName(e.target.value);
  }, []);

  const handleNameBlur = useCallback(() => {
    setIsEditing(false);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label: eventName });
    }
  }, [id, eventName]);

  const backgroundColor = data.color || '#ffffff';
  const textColor = data.textColor || '#000000';
  const eventType = data.eventType || 'start';
  const trigger = data.trigger || 'none';

  const getEventIcon = () => {
    switch (trigger) {
      case 'message':
        return <Mail size={20} color={textColor} />;
      case 'timer':
        return <Clock size={20} color={textColor} />;
      case 'error':
        return <AlertCircle size={20} color={textColor} />;
      case 'terminate':
        return <XCircle size={20} color={textColor} />;
      case 'signal':
        return <div style={{ 
          width: 0, 
          height: 0, 
          borderLeft: '10px solid transparent',
          borderRight: '10px solid transparent',
          borderBottom: `20px solid ${textColor}`
        }} />;
      default:
        return eventType === 'start' ? <Play size={16} color={textColor} /> : null;
    }
  };

  const getBorderStyle = () => {
    switch (eventType) {
      case 'start':
        return `2px solid ${textColor}`;
      case 'intermediate':
        return `3px double ${textColor}`;
      case 'end':
        return `3px solid ${textColor}`;
      default:
        return `2px solid ${textColor}`;
    }
  };

  return (
    <div style={{ position: 'relative', zIndex: data.zIndex || 1 }}>
      <div 
        className="event-node"
        style={{
          width: '60px',
          height: '60px',
          backgroundColor,
          border: getBorderStyle(),
          borderRadius: '50%',
          boxShadow: selected ? '0 0 0 2px #3b82f6' : '0 2px 4px rgba(0,0,0,0.1)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center'
        }}
      >
        <Handle type="target" position={Position.Top} id="top" />
        <Handle type="target" position={Position.Left} id="left" />
        <Handle type="target" position={Position.Right} id="right" />
        <Handle type="target" position={Position.Bottom} id="bottom" />
        
        <Handle type="source" position={Position.Top} id="top-source" />
        <Handle type="source" position={Position.Left} id="left-source" />
        <Handle type="source" position={Position.Right} id="right-source" />
        <Handle type="source" position={Position.Bottom} id="bottom-source" />

        {getEventIcon()}
      </div>

      {/* Event Label */}
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
            value={eventName}
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
            {eventName}
          </div>
        )}
      </div>
    </div>
  );
};

export default memo(EventNode);
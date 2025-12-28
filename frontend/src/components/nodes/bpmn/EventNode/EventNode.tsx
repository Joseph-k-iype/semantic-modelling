// frontend/src/components/nodes/bpmn/EventNode/EventNode.tsx

import React, { memo, useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Clock, Mail, AlertCircle, CheckCircle } from 'lucide-react';

export type EventType = 'start' | 'intermediate' | 'end';
export type EventTrigger = 'none' | 'message' | 'timer' | 'error' | 'conditional';

export interface EventNodeData {
  label: string;
  eventType: EventType;
  eventTrigger: EventTrigger;
  color?: string;
  textColor?: string;
  zIndex?: number;
}

const EventNode: React.FC<NodeProps<EventNodeData>> = memo(({ id, data, selected }) => {
  const [isEditingLabel, setIsEditingLabel] = useState(false);
  const [label, setLabel] = useState(data.label || 'Event');

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
      setLabel(data.label || 'Event');
    }
  }, [handleLabelBlur, data.label]);

  const getEventIcon = () => {
    switch (data.eventTrigger) {
      case 'message':
        return <Mail size={16} />;
      case 'timer':
        return <Clock size={16} />;
      case 'error':
        return <AlertCircle size={16} />;
      case 'conditional':
        return <CheckCircle size={16} />;
      default:
        return null;
    }
  };

  const getEventStyle = () => {
    const baseStyle = {
      width: '50px',
      height: '50px',
      borderRadius: '50%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: data.color || 'white',
      position: 'relative' as const,
      zIndex: data.zIndex || 1
    };

    switch (data.eventType) {
      case 'start':
        return {
          ...baseStyle,
          border: '3px solid #10b981',
          boxShadow: selected ? '0 0 0 3px rgba(16, 185, 129, 0.3)' : 'none'
        };
      case 'intermediate':
        return {
          ...baseStyle,
          border: '3px double #f59e0b',
          boxShadow: selected ? '0 0 0 3px rgba(245, 158, 11, 0.3)' : 'none'
        };
      case 'end':
        return {
          ...baseStyle,
          border: '3px solid #ef4444',
          boxShadow: selected ? '0 0 0 3px rgba(239, 68, 68, 0.3)' : 'none'
        };
      default:
        return baseStyle;
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      {/* Handles */}
      {data.eventType !== 'end' && (
        <Handle
          type="source"
          position={Position.Right}
          style={{
            background: '#6b7280',
            width: '8px',
            height: '8px',
            border: '2px solid white'
          }}
        />
      )}
      {data.eventType !== 'start' && (
        <Handle
          type="target"
          position={Position.Left}
          style={{
            background: '#6b7280',
            width: '8px',
            height: '8px',
            border: '2px solid white'
          }}
        />
      )}

      {/* Event Circle */}
      <div style={getEventStyle()}>
        <div style={{ color: data.textColor || '#374151' }}>
          {getEventIcon()}
        </div>
      </div>

      {/* Label */}
      <div
        style={{
          position: 'absolute',
          top: '60px',
          left: '50%',
          transform: 'translateX(-50%)',
          whiteSpace: 'nowrap',
          textAlign: 'center',
          minWidth: '80px'
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
              minWidth: '80px'
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

EventNode.displayName = 'EventNode';

export default EventNode;
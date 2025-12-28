// frontend/src/components/nodes/bpmn/TaskNode/TaskNode.tsx

import React, { memo, useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { User, Settings, FileText, Code } from 'lucide-react';

export type TaskType = 'task' | 'user' | 'service' | 'manual' | 'script';

export interface TaskNodeData {
  label: string;
  taskType: TaskType;
  color?: string;
  textColor?: string;
  zIndex?: number;
}

const TaskNode: React.FC<NodeProps<TaskNodeData>> = memo(({ id, data, selected }) => {
  const [isEditingLabel, setIsEditingLabel] = useState(false);
  const [label, setLabel] = useState(data.label || 'Task');

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
      setLabel(data.label || 'Task');
    }
  }, [handleLabelBlur, data.label]);

  const getTaskIcon = () => {
    switch (data.taskType) {
      case 'user':
        return <User size={14} />;
      case 'service':
        return <Settings size={14} />;
      case 'manual':
        return <FileText size={14} />;
      case 'script':
        return <Code size={14} />;
      default:
        return null;
    }
  };

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
          border: '2px solid white'
        }}
      />
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

      {/* Task Rectangle */}
      <div
        style={{
          width: '120px',
          minHeight: '60px',
          background: data.color || 'white',
          border: `3px solid ${selected ? '#3b82f6' : '#3b82f6'}`,
          borderRadius: '8px',
          padding: '8px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: selected ? '0 0 0 3px rgba(59, 130, 246, 0.3)' : '0 1px 3px rgba(0,0,0,0.1)',
          position: 'relative',
          zIndex: data.zIndex || 1
        }}
      >
        {/* Task Type Icon */}
        {data.taskType !== 'task' && (
          <div
            style={{
              position: 'absolute',
              top: '4px',
              left: '4px',
              padding: '2px',
              background: '#e0f2fe',
              borderRadius: '3px',
              color: '#0369a1'
            }}
          >
            {getTaskIcon()}
          </div>
        )}

        {/* Task Label */}
        <div
          style={{
            width: '100%',
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
                textAlign: 'center'
              }}
            />
          ) : (
            <div
              style={{
                fontSize: '12px',
                fontWeight: '500',
                cursor: 'text',
                color: data.textColor || '#374151',
                wordWrap: 'break-word'
              }}
            >
              {label}
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

TaskNode.displayName = 'TaskNode';

export default TaskNode;
// frontend/src/components/nodes/bpmn/TaskNode/TaskNode.tsx

import React, { memo, useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { User, Cog, Mail, FileText, Repeat } from 'lucide-react';

export type TaskType = 'task' | 'user' | 'service' | 'send' | 'receive' | 'manual' | 'script';

export interface TaskNodeData {
  label: string;
  taskType: TaskType;
  isLooping?: boolean;
  isMultiInstance?: boolean;
  color?: string;
  textColor?: string;
  zIndex?: number;
}

const TaskNode: React.FC<NodeProps<TaskNodeData>> = ({ data, selected, id }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [taskName, setTaskName] = useState(data.label);

  const handleNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setTaskName(e.target.value);
  }, []);

  const handleNameBlur = useCallback(() => {
    setIsEditing(false);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label: taskName });
    }
  }, [id, taskName]);

  const backgroundColor = data.color || '#ffffff';
  const textColor = data.textColor || '#000000';
  const taskType = data.taskType || 'task';

  const getTaskIcon = () => {
    switch (taskType) {
      case 'user':
        return <User size={16} color={textColor} strokeWidth={1.5} />;
      case 'service':
        return <Cog size={16} color={textColor} strokeWidth={1.5} />;
      case 'send':
        return <Mail size={16} color={textColor} strokeWidth={1.5} />;
      case 'receive':
        return <Mail size={16} color={textColor} strokeWidth={1.5} style={{ transform: 'rotate(180deg)' }} />;
      case 'manual':
        return <FileText size={16} color={textColor} strokeWidth={1.5} />;
      case 'script':
        return <FileText size={16} color={textColor} strokeWidth={1.5} />;
      default:
        return null;
    }
  };

  return (
    <div 
      className="task-node"
      style={{
        minWidth: '120px',
        minHeight: '80px',
        backgroundColor,
        border: `2px solid ${textColor}`,
        borderRadius: '8px',
        boxShadow: selected ? '0 0 0 2px #3b82f6' : '0 2px 4px rgba(0,0,0,0.1)',
        padding: '12px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        position: 'relative',
        zIndex: data.zIndex || 1
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

      {/* Task Type Icon */}
      {taskType !== 'task' && (
        <div style={{ 
          position: 'absolute', 
          top: '8px', 
          left: '8px',
          padding: '4px',
          backgroundColor: 'rgba(255,255,255,0.9)',
          borderRadius: '4px'
        }}>
          {getTaskIcon()}
        </div>
      )}

      {/* Loop/Multi-instance Marker */}
      {(data.isLooping || data.isMultiInstance) && (
        <div style={{ 
          position: 'absolute', 
          bottom: '8px', 
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          gap: '2px'
        }}>
          {data.isLooping && <Repeat size={14} color={textColor} />}
          {data.isMultiInstance && (
            <div style={{ display: 'flex', gap: '1px' }}>
              <div style={{ width: '2px', height: '12px', backgroundColor: textColor }} />
              <div style={{ width: '2px', height: '12px', backgroundColor: textColor }} />
              <div style={{ width: '2px', height: '12px', backgroundColor: textColor }} />
            </div>
          )}
        </div>
      )}

      {/* Task Name */}
      <div style={{ 
        textAlign: 'center', 
        fontSize: '12px', 
        color: textColor,
        fontWeight: '500',
        wordBreak: 'break-word',
        width: '100%'
      }}>
        {isEditing ? (
          <input
            type="text"
            value={taskName}
            onChange={handleNameChange}
            onBlur={handleNameBlur}
            autoFocus
            style={{
              width: '100%',
              border: 'none',
              background: 'transparent',
              color: textColor,
              fontSize: '12px',
              textAlign: 'center',
              outline: 'none'
            }}
          />
        ) : (
          <div 
            onDoubleClick={() => setIsEditing(true)}
            style={{ cursor: 'text' }}
          >
            {taskName}
          </div>
        )}
      </div>
    </div>
  );
};

export default memo(TaskNode);
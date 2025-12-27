// frontend/src/components/nodes/bpmn/TaskNode/TaskNode.tsx
import { memo, useState } from 'react';
import { NodeProps, Handle, Position } from 'reactflow';
import { BPMNNodeData } from '../../../../types/diagram.types';
import { User, Settings, Code, FileText, Edit2 } from 'lucide-react';
import clsx from 'clsx';

export const TaskNode = memo<NodeProps<BPMNNodeData>>(({ data, selected }) => {
  const [isHovered, setIsHovered] = useState(false);
  const task = data.task;

  if (!task) {
    return (
      <div className="px-8 py-4 bg-white border-2 border-gray-300 rounded-lg shadow-sm">
        <div className="text-sm text-gray-600">New Task</div>
      </div>
    );
  }

  // Get task icon based on type
  const getTaskIcon = () => {
    switch (task.type) {
      case 'userTask':
        return <User className="w-4 h-4" />;
      case 'serviceTask':
        return <Settings className="w-4 h-4" />;
      case 'scriptTask':
        return <Code className="w-4 h-4" />;
      case 'manualTask':
        return <FileText className="w-4 h-4" />;
      default:
        return null;
    }
  };

  // Get task color based on type
  const getTaskColor = () => {
    switch (task.type) {
      case 'userTask':
        return 'border-blue-500 bg-blue-50';
      case 'serviceTask':
        return 'border-green-500 bg-green-50';
      case 'scriptTask':
        return 'border-purple-500 bg-purple-50';
      case 'manualTask':
        return 'border-yellow-500 bg-yellow-50';
      default:
        return 'border-gray-400 bg-white';
    }
  };

  return (
    <div
      className={clsx(
        'relative transition-all duration-200',
        selected && 'ring-2 ring-blue-500 ring-offset-2'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-gray-400 border-2 border-white"
      />

      <div
        className={clsx(
          'px-6 py-4 border-2 rounded-lg shadow-sm min-w-[140px] max-w-[200px]',
          getTaskColor(),
          isHovered && 'shadow-md'
        )}
      >
        {/* Task Icon */}
        {task.type !== 'task' && (
          <div className="absolute top-1 left-1 p-1 bg-white rounded border border-gray-300">
            {getTaskIcon()}
          </div>
        )}

        {/* Task Name */}
        <div className="flex items-center gap-2">
          <div className="flex-1 text-sm font-medium text-gray-800 text-center break-words">
            {task.name || 'Unnamed Task'}
          </div>
          {isHovered && (
            <button className="p-1 hover:bg-white rounded transition-colors">
              <Edit2 className="w-3 h-3 text-gray-600" />
            </button>
          )}
        </div>

        {/* Assignee */}
        {task.assignee && (
          <div className="mt-2 text-xs text-gray-600 text-center">
            <User className="w-3 h-3 inline mr-1" />
            {task.assignee}
          </div>
        )}

        {/* Documentation indicator */}
        {task.documentation && (
          <div className="absolute bottom-1 right-1">
            <FileText className="w-3 h-3 text-gray-400" />
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-gray-400 border-2 border-white"
      />
    </div>
  );
});

TaskNode.displayName = 'TaskNode';
import React, { memo, useState } from 'react';
import { NodeProps } from 'reactflow';
import { BaseNode } from '../../base/BaseNode';
import { BPMNNodeData } from '../../../../types/diagram.types';
import { User, Settings, FileText, Code, Edit2 } from 'lucide-react';
import clsx from 'clsx';

export const TaskNode = memo<NodeProps<BPMNNodeData>>(({ id, data, selected }) => {
  const [isHovered, setIsHovered] = useState(false);
  const task = data.task;

  if (!task) {
    return (
      <BaseNode id={id} data={data} selected={selected}>
        <div className="px-4 py-2">
          <div className="font-bold text-gray-800">New Task</div>
        </div>
      </BaseNode>
    );
  }

  const getTaskIcon = () => {
    switch (task.type) {
      case 'userTask':
        return <User className="w-4 h-4" />;
      case 'serviceTask':
        return <Settings className="w-4 h-4" />;
      case 'manualTask':
        return <FileText className="w-4 h-4" />;
      case 'scriptTask':
        return <Code className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getTaskColor = () => {
    switch (task.type) {
      case 'userTask':
        return 'from-blue-400 to-blue-500';
      case 'serviceTask':
        return 'from-green-400 to-green-500';
      case 'manualTask':
        return 'from-orange-400 to-orange-500';
      case 'scriptTask':
        return 'from-purple-400 to-purple-500';
      default:
        return 'from-gray-400 to-gray-500';
    }
  };

  return (
    <BaseNode 
      id={id} 
      data={data} 
      selected={selected}
      className="min-w-[160px]"
    >
      <div
        className="relative"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className={clsx(
          'bg-gradient-to-br rounded px-4 py-3',
          getTaskColor()
        )}>
          <div className="flex items-start gap-2">
            {getTaskIcon() && (
              <div className="mt-0.5 text-white opacity-80">
                {getTaskIcon()}
              </div>
            )}
            <div className="flex-1">
              <div className="text-white font-semibold text-sm leading-tight">
                {task.name}
              </div>
              {task.assignee && (
                <div className="text-white text-xs opacity-80 mt-1">
                  👤 {task.assignee}
                </div>
              )}
            </div>
            {isHovered && (
              <button className="text-white opacity-80 hover:opacity-100 transition-opacity p-1">
                <Edit2 className="w-3 h-3" />
              </button>
            )}
          </div>
        </div>

        {/* Documentation indicator */}
        {task.documentation && (
          <div className="absolute -top-2 -right-2 w-5 h-5 bg-yellow-400 rounded-full flex items-center justify-center text-xs">
            📄
          </div>
        )}
      </div>
    </BaseNode>
  );
});

TaskNode.displayName = 'TaskNode';
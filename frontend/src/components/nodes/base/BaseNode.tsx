import { memo, ReactNode } from 'react';
import { Handle, Position } from 'reactflow';
import clsx from 'clsx';

export interface BaseNodeProps {
  id: string;
  data: any;
  selected?: boolean;
  children?: ReactNode;
  className?: string;
  showHandles?: boolean;
}

export const BaseNode = memo<BaseNodeProps>(({ 
  selected = false, 
  children, 
  className = '',
  showHandles = true 
}) => {
  return (
    <div
      className={clsx(
        'bg-white border-2 rounded shadow-md transition-all',
        selected ? 'border-blue-500 shadow-lg' : 'border-gray-300',
        'hover:shadow-lg',
        className
      )}
    >
      {/* Connection Handles */}
      {showHandles && (
        <>
          <Handle
            type="target"
            position={Position.Top}
            id="top"
            className="w-3 h-3 !bg-blue-500 border-2 border-white"
          />
          <Handle
            type="target"
            position={Position.Left}
            id="left"
            className="w-3 h-3 !bg-blue-500 border-2 border-white"
          />
          <Handle
            type="source"
            position={Position.Right}
            id="right"
            className="w-3 h-3 !bg-blue-500 border-2 border-white"
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="bottom"
            className="w-3 h-3 !bg-blue-500 border-2 border-white"
          />
        </>
      )}

      {/* Node Content */}
      {children}
    </div>
  );
});

BaseNode.displayName = 'BaseNode';
// frontend/src/components/nodes/bpmn/PoolNode/PoolNode.tsx
import { memo, useState } from 'react';
import { NodeProps } from 'reactflow';
import { BPMNNodeData } from '../../../../types/diagram.types';
import { Layers, Edit2 } from 'lucide-react';
import clsx from 'clsx';

export const PoolNode = memo<NodeProps<BPMNNodeData>>(({ id, data, selected }) => {
  const [isHovered, setIsHovered] = useState(false);
  const pool = data.pool;

  if (!pool) {
    return (
      <div className="min-w-[600px] min-h-[300px] border-2 border-gray-400 bg-white rounded">
        <div className="h-full flex items-center justify-center text-gray-400">
          <Layers className="w-8 h-8" />
        </div>
      </div>
    );
  }

  return (
    <div
      className={clsx(
        'relative transition-all duration-200',
        selected && 'ring-2 ring-blue-500 ring-offset-2'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="min-w-[600px] border-2 border-gray-600 bg-white rounded flex">
        {/* Pool Name (Vertical) */}
        <div className="w-8 bg-blue-100 border-r-2 border-gray-600 flex items-center justify-center rounded-l">
          <div className="transform -rotate-90 whitespace-nowrap text-sm font-semibold text-gray-800">
            {pool.name || 'Unnamed Pool'}
          </div>
        </div>

        {/* Lanes */}
        <div className="flex-1 flex flex-col">
          {pool.lanes && pool.lanes.length > 0 ? (
            pool.lanes.map((lane, index) => (
              <div
                key={lane.id}
                className={clsx(
                  'flex border-gray-300',
                  index > 0 && 'border-t-2'
                )}
                style={{ height: `${lane.height}px` }}
              >
                {/* Lane Name */}
                <div className="w-6 bg-blue-50 border-r border-gray-300 flex items-center justify-center">
                  <div className="transform -rotate-90 whitespace-nowrap text-xs font-medium text-gray-700">
                    {lane.name || `Lane ${index + 1}`}
                  </div>
                </div>

                {/* Lane Content Area */}
                <div className="flex-1 p-4 bg-white relative">
                  {/* This is the droppable area for tasks, events, etc. */}
                  <div className="h-full border border-dashed border-gray-200 rounded flex items-center justify-center text-gray-300 text-xs">
                    Drop elements here
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="flex-1 p-4 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <Layers className="w-12 h-12 mx-auto mb-2" />
                <div className="text-sm">No lanes defined</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Edit button */}
      {isHovered && (
        <button className="absolute top-2 right-2 p-2 bg-white rounded shadow-md hover:bg-gray-50 transition-colors">
          <Edit2 className="w-4 h-4 text-gray-600" />
        </button>
      )}
    </div>
  );
});

PoolNode.displayName = 'PoolNode';
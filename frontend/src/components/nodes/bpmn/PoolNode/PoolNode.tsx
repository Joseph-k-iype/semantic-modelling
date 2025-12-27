import React, { memo, useState } from 'react';
import { NodeProps } from 'reactflow';
import { BaseNode } from '../../base/BaseNode';
import { BPMNNodeData, BPMNLane } from '../../../../types/diagram.types';
import { Plus, Edit2, GripVertical } from 'lucide-react';
import clsx from 'clsx';

export const PoolNode = memo<NodeProps<BPMNNodeData>>(({ id, data, selected }) => {
  const [isHovered, setIsHovered] = useState(false);
  const pool = data.pool;

  if (!pool) {
    return (
      <BaseNode id={id} data={data} selected={selected}>
        <div className="px-4 py-2 min-w-[600px] min-h-[200px]">
          <div className="font-bold text-gray-800">New Pool</div>
        </div>
      </BaseNode>
    );
  }

  const totalHeight = pool.lanes.reduce((sum, lane) => sum + lane.height, 0);

  return (
    <BaseNode 
      id={id} 
      data={data} 
      selected={selected}
      className="!p-0 min-w-[700px]"
      showHandles={false}
    >
      <div
        className="flex h-full"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Pool Header */}
        <div className="bg-gradient-to-b from-blue-500 to-blue-600 text-white w-12 flex items-center justify-center relative rounded-l">
          <div className="transform -rotate-90 whitespace-nowrap font-bold tracking-wide">
            {pool.name}
          </div>
          {isHovered && (
            <button className="absolute top-2 left-1/2 transform -translate-x-1/2 p-1 hover:bg-blue-400 rounded transition-colors">
              <Edit2 className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Lanes */}
        <div className="flex-1 flex flex-col">
          {pool.lanes.map((lane, index) => (
            <div
              key={lane.id}
              className={clsx(
                'relative border-b-2 border-gray-300 bg-blue-50 hover:bg-blue-100 transition-colors',
                index === pool.lanes.length - 1 && 'border-b-0 rounded-br'
              )}
              style={{ height: `${lane.height}px`, minHeight: '100px' }}
            >
              {/* Lane Header */}
              <div className="absolute left-0 top-0 bottom-0 w-32 bg-blue-100 border-r-2 border-gray-300 flex items-center justify-center group">
                <div className="font-semibold text-gray-700 text-sm">
                  {lane.name}
                </div>
                {isHovered && (
                  <div className="absolute right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <GripVertical className="w-4 h-4 text-gray-400" />
                  </div>
                )}
              </div>

              {/* Lane Content Area */}
              <div className="ml-32 h-full p-4">
                {/* This area will contain tasks and other elements within the lane */}
                <div className="w-full h-full border-2 border-dashed border-gray-300 rounded flex items-center justify-center text-gray-400 text-sm">
                  Drop tasks here
                </div>
              </div>
            </div>
          ))}

          {/* Add Lane Button */}
          {isHovered && (
            <button className="w-full py-2 border-t-2 border-gray-300 bg-blue-50 hover:bg-blue-100 transition-colors flex items-center justify-center gap-2 text-blue-600 text-sm rounded-br">
              <Plus className="w-4 h-4" />
              <span>Add Lane</span>
            </button>
          )}
        </div>
      </div>
    </BaseNode>
  );
});

PoolNode.displayName = 'PoolNode';
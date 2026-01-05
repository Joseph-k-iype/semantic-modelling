// frontend/src/components/nodes/PackageNode.tsx
/**
 * Package Node Component - Folder style for grouping elements
 * Path: frontend/src/components/nodes/PackageNode.tsx
 * 
 * Packages act as containers/folders for other elements
 */

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Folder, FolderOpen } from 'lucide-react';
import { COLORS } from '../../../constants/colors';
import type { PackageNodeData } from '../../../types/diagram.types';

const PackageNode: React.FC<NodeProps<PackageNodeData>> = memo(({ data, selected }) => {
  const isExpanded = data.isExpanded ?? true;
  const childCount = data.childCount ?? 0;
  
  return (
    <div
      className="min-w-[200px] border-2 rounded-lg shadow-lg"
      style={{
        backgroundColor: COLORS.WHITE,
        borderColor: selected ? COLORS.PRIMARY : COLORS.BLACK,
        borderStyle: 'solid',
      }}
    >
      {/* Folder Tab */}
      <div
        className="flex items-center gap-2 px-3 py-2 rounded-t-lg border-b-2"
        style={{
          backgroundColor: COLORS.OFF_WHITE,
          borderColor: COLORS.BLACK,
        }}
      >
        {isExpanded ? (
          <FolderOpen 
            className="w-5 h-5" 
            style={{ color: COLORS.WARNING }}
          />
        ) : (
          <Folder 
            className="w-5 h-5" 
            style={{ color: COLORS.WARNING }}
          />
        )}
        <span 
          className="font-bold text-sm"
          style={{ color: COLORS.BLACK }}
        >
          {data.label || 'Package'}
        </span>
        {childCount > 0 && (
          <span 
            className="ml-auto text-xs px-2 py-0.5 rounded"
            style={{ 
              backgroundColor: COLORS.LIGHT_GREY,
              color: COLORS.BLACK
            }}
          >
            {childCount}
          </span>
        )}
      </div>

      {/* Package Body */}
      <div
        className="p-4 min-h-[100px]"
        style={{ 
          backgroundColor: COLORS.WHITE,
        }}
      >
        <div 
          className="text-center text-sm italic"
          style={{ color: COLORS.DARK_GREY }}
        >
          {childCount > 0 
            ? `Contains ${childCount} element${childCount !== 1 ? 's' : ''}`
            : 'Drop elements here'
          }
        </div>
      </div>

      {/* Connection Handles */}
      <Handle
        type="target"
        position={Position.Top}
        style={{ 
          background: COLORS.PRIMARY,
          width: '10px',
          height: '10px',
        }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ 
          background: COLORS.PRIMARY,
          width: '10px',
          height: '10px',
        }}
      />
    </div>
  );
});

PackageNode.displayName = 'PackageNode';

export default PackageNode;
// frontend/src/components/nodes/PackageNode.tsx
/**
 * Package Node Component - Folder style for grouping elements
 * Path: frontend/src/components/nodes/PackageNode.tsx
 * 
 * IMPROVEMENTS:
 * - Looks like a folder/container
 * - Resizable
 * - Shows child count
 * - Visual grouping indicator
 */

import React, { memo } from 'react';
import { Handle, Position, NodeProps, NodeResizer } from 'reactflow';
import { Folder, FolderOpen, Package } from 'lucide-react';
import { COLORS } from '../../../constants/colors';
import type { PackageNodeData } from '../../../types/diagram.types';

const PackageNode: React.FC<NodeProps<PackageNodeData>> = memo(({ data, selected }) => {
  const isExpanded = data.isExpanded ?? true;
  const childCount = data.childCount ?? 0;
  
  return (
    <>
      {/* Node Resizer - allows resizing the package */}
      <NodeResizer
        color={COLORS.PRIMARY}
        isVisible={selected}
        minWidth={250}
        minHeight={150}
      />
      
      <div
        className="w-full h-full border-2 rounded-lg shadow-lg overflow-hidden"
        style={{
          backgroundColor: COLORS.WHITE,
          borderColor: selected ? COLORS.PRIMARY : COLORS.DARK_GREY,
          borderStyle: 'dashed', // Dashed border to show it's a container
          borderWidth: selected ? '3px' : '2px',
        }}
      >
        {/* Folder Tab Header */}
        <div
          className="flex items-center gap-2 px-3 py-2 border-b-2"
          style={{
            backgroundColor: data.color || ELEMENT_COLORS.package,
            borderColor: COLORS.BLACK,
            borderTopLeftRadius: '6px',
            borderTopRightRadius: '6px',
          }}
        >
          <Package 
            className="w-5 h-5" 
            style={{ color: COLORS.BLACK }}
          />
          <span 
            className="font-bold text-sm flex-1"
            style={{ color: COLORS.BLACK }}
          >
            {data.label || 'Package'}
          </span>
          {childCount > 0 && (
            <span 
              className="text-xs px-2 py-0.5 rounded font-medium"
              style={{ 
                backgroundColor: COLORS.WHITE,
                color: COLORS.BLACK,
                border: `1px solid ${COLORS.BLACK}`,
              }}
            >
              {childCount} element{childCount !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Package Body - Drop Zone */}
        <div
          className="p-6 h-full flex items-center justify-center"
          style={{ 
            backgroundColor: `${COLORS.WHITE}99`,
            minHeight: '120px',
          }}
        >
          <div 
            className="text-center"
            style={{ color: COLORS.DARK_GREY }}
          >
            {childCount > 0 ? (
              <>
                <FolderOpen 
                  className="w-12 h-12 mx-auto mb-2" 
                  style={{ color: COLORS.DARK_GREY }}
                />
                <p className="text-sm font-medium">
                  Contains {childCount} element{childCount !== 1 ? 's' : ''}
                </p>
                <p className="text-xs mt-1">
                  Drag elements here to group
                </p>
              </>
            ) : (
              <>
                <Folder 
                  className="w-12 h-12 mx-auto mb-2" 
                  style={{ color: COLORS.LIGHT_GREY }}
                />
                <p className="text-sm italic">
                  Empty package
                </p>
                <p className="text-xs mt-1">
                  Drag elements here to organize
                </p>
              </>
            )}
          </div>
        </div>

        {/* Stereotype if present */}
        {data.stereotype && (
          <div
            className="absolute top-0 right-0 px-2 py-1 text-xs"
            style={{
              backgroundColor: COLORS.OFF_WHITE,
              border: `1px solid ${COLORS.LIGHT_GREY}`,
              borderTopRightRadius: '6px',
              color: COLORS.DARK_GREY,
            }}
          >
            &lt;&lt;{data.stereotype}&gt;&gt;
          </div>
        )}

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
        <Handle
          type="target"
          position={Position.Left}
          style={{ 
            background: COLORS.PRIMARY,
            width: '10px',
            height: '10px',
          }}
        />
        <Handle
          type="source"
          position={Position.Right}
          style={{ 
            background: COLORS.PRIMARY,
            width: '10px',
            height: '10px',
          }}
        />
      </div>
    </>
  );
});

PackageNode.displayName = 'PackageNode';

export default PackageNode;

// Need to import ELEMENT_COLORS
import { ELEMENT_COLORS } from '../../../constants/colors';
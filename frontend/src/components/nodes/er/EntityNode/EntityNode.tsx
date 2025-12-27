// frontend/src/components/nodes/er/EntityNode/EntityNode.tsx
import { memo, useState } from 'react';
import { NodeProps, Handle, Position } from 'reactflow';
import { ERNodeData, ERAttribute } from '../../../../types/diagram.types';
import { Key, Lock, Database, Plus, Edit2 } from 'lucide-react';
import clsx from 'clsx';

export const EntityNode = memo<NodeProps<ERNodeData>>(({ id, data, selected }) => {
  const [isHovered, setIsHovered] = useState(false);
  const entity = data.entity;

  if (!entity) {
    return (
      <div className="min-w-[250px] bg-white border-2 border-blue-500 rounded shadow-sm">
        <div className="bg-blue-500 text-white px-4 py-3 rounded-t flex items-center gap-2">
          <Database className="w-5 h-5" />
          <span className="font-bold">New Entity</span>
        </div>
        <div className="px-4 py-3 text-sm text-gray-400 italic">
          No attributes defined
        </div>
      </div>
    );
  }

  const renderAttribute = (attr: ERAttribute) => (
    <div
      key={attr.id}
      className={clsx(
        'px-3 py-2 text-sm flex items-center gap-2 hover:bg-gray-50 transition-colors group',
        attr.isPrimary && 'bg-yellow-50'
      )}
    >
      <Handle
        type="target"
        position={Position.Left}
        id={`${id}-attr-${attr.id}-target`}
        className="w-2 h-2 !bg-blue-400 border border-white opacity-0 group-hover:opacity-100 transition-opacity"
        style={{ left: -4 }}
      />
      
      {attr.isPrimary && <Key className="w-3 h-3 text-yellow-600 flex-shrink-0" />}
      {attr.isForeign && <Lock className="w-3 h-3 text-blue-600 flex-shrink-0" />}
      
      <span className={clsx(
        'flex-1 truncate',
        attr.isPrimary && 'font-semibold text-yellow-900'
      )}>
        {attr.name}
      </span>
      
      <span className="text-gray-500 text-xs">
        {attr.type}
      </span>
      
      {!attr.isNullable && (
        <span className="text-red-500 text-xs font-bold">*</span>
      )}
      
      {attr.isUnique && (
        <span className="text-purple-500 text-xs font-bold">U</span>
      )}

      <Handle
        type="source"
        position={Position.Right}
        id={`${id}-attr-${attr.id}-source`}
        className="w-2 h-2 !bg-blue-400 border border-white opacity-0 group-hover:opacity-100 transition-opacity"
        style={{ right: -4 }}
      />
    </div>
  );

  return (
    <div
      className={clsx(
        'relative transition-all duration-200',
        selected && 'ring-2 ring-blue-500 ring-offset-2 rounded'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Main entity connection handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-blue-500 border-2 border-white"
      />
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-blue-500 border-2 border-white"
      />

      <div className={clsx(
        'min-w-[280px] max-w-[400px] bg-white rounded shadow-md overflow-hidden',
        entity.isWeak && 'border-4 border-double border-blue-500',
        !entity.isWeak && 'border-2 border-blue-500'
      )}>
        {/* Header */}
        <div className={clsx(
          'bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-3 flex items-center gap-2',
          entity.isWeak && 'from-blue-400 to-blue-500'
        )}>
          <Database className="w-5 h-5 flex-shrink-0" />
          <span className="font-bold text-lg flex-1 truncate">
            {entity.name}
          </span>
          {isHovered && (
            <button className="p-1 hover:bg-blue-400 rounded transition-colors">
              <Edit2 className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Attributes Section */}
        <div className="border-t-2 border-gray-200">
          {entity.attributes.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {entity.attributes.map(renderAttribute)}
            </div>
          ) : (
            <div className="px-4 py-3 text-sm text-gray-400 italic text-center">
              No attributes defined
            </div>
          )}
        </div>

        {/* Footer - Add Attribute Button */}
        {isHovered && (
          <div className="border-t border-gray-200 px-3 py-2 bg-gray-50">
            <button className="w-full flex items-center justify-center gap-2 text-sm text-blue-600 hover:text-blue-700 transition-colors py-1">
              <Plus className="w-4 h-4" />
              <span>Add Attribute</span>
            </button>
          </div>
        )}
      </div>

      {/* Main entity connection handles */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-blue-500 border-2 border-white"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-blue-500 border-2 border-white"
      />
    </div>
  );
});

EntityNode.displayName = 'EntityNode';
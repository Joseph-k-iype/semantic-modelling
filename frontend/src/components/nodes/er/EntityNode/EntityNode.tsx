import React, { memo, useState } from 'react';
import { NodeProps } from 'reactflow';
import { BaseNode } from '../../base/BaseNode';
import { ERNodeData, ERAttribute } from '../../../../types/diagram.types';
import { Key, Lock, Database, Plus, Edit2, Trash2 } from 'lucide-react';
import clsx from 'clsx';

export const EntityNode = memo<NodeProps<ERNodeData>>(({ id, data, selected }) => {
  const [isHovered, setIsHovered] = useState(false);
  const entity = data.entity;

  if (!entity) {
    return (
      <BaseNode id={id} data={data} selected={selected}>
        <div className="px-4 py-2">
          <div className="font-bold text-gray-800">New Entity</div>
        </div>
      </BaseNode>
    );
  }

  const renderAttribute = (attr: ERAttribute) => (
    <div
      key={attr.id}
      className={clsx(
        'px-3 py-1.5 text-sm flex items-center gap-2 hover:bg-gray-50 transition-colors',
        attr.isPrimary && 'font-semibold'
      )}
    >
      {attr.isPrimary && <Key className="w-3 h-3 text-yellow-600" />}
      {attr.isForeign && <Lock className="w-3 h-3 text-blue-600" />}
      <span className={clsx(attr.isPrimary && 'text-yellow-700')}>
        {attr.name}
      </span>
      <span className="text-gray-500 text-xs ml-auto">{attr.type}</span>
      {!attr.isNullable && <span className="text-red-500 text-xs">*</span>}
    </div>
  );

  return (
    <BaseNode 
      id={id} 
      data={data} 
      selected={selected}
      className="min-w-[250px]"
    >
      <div
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-3 rounded-t flex items-center gap-2">
          <Database className="w-5 h-5" />
          <span className="font-bold text-lg flex-1">{entity.name}</span>
          {isHovered && (
            <button className="p-1 hover:bg-blue-400 rounded transition-colors">
              <Edit2 className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Attributes */}
        <div className="border-t-2 border-gray-200">
          {entity.attributes.length > 0 ? (
            entity.attributes.map(renderAttribute)
          ) : (
            <div className="px-4 py-3 text-sm text-gray-400 italic">
              No attributes defined
            </div>
          )}
        </div>

        {/* Footer - Add Attribute Button */}
        {isHovered && (
          <div className="border-t border-gray-200 px-3 py-2">
            <button className="w-full flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 transition-colors">
              <Plus className="w-4 h-4" />
              <span>Add Attribute</span>
            </button>
          </div>
        )}
      </div>
    </BaseNode>
  );
});

EntityNode.displayName = 'EntityNode';
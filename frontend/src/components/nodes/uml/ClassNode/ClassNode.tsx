import React, { memo, useState } from 'react';
import { NodeProps } from 'reactflow';
import { BaseNode } from '../../base/BaseNode';
import { UMLNodeData, UMLAttribute, UMLMethod } from '../../../../types/diagram.types';
import { Package, Plus, Edit2 } from 'lucide-react';
import clsx from 'clsx';

export const ClassNode = memo<NodeProps<UMLNodeData>>(({ id, data, selected }) => {
  const [isHovered, setIsHovered] = useState(false);
  const umlClass = data.class;

  if (!umlClass) {
    return (
      <BaseNode id={id} data={data} selected={selected}>
        <div className="px-4 py-2">
          <div className="font-bold text-gray-800">New Class</div>
        </div>
      </BaseNode>
    );
  }

  const getVisibilitySymbol = (visibility: string) => {
    switch (visibility) {
      case 'public': return '+';
      case 'private': return '-';
      case 'protected': return '#';
      case 'package': return '~';
      default: return '';
    }
  };

  const renderAttribute = (attr: UMLAttribute) => (
    <div
      key={attr.id}
      className="px-3 py-1 text-sm font-mono hover:bg-gray-50 transition-colors"
    >
      <span className="text-gray-600">{getVisibilitySymbol(attr.visibility)}</span>
      <span className={clsx(attr.isStatic && 'underline', 'ml-2')}>
        {attr.name}
      </span>
      <span className="text-gray-500">: {attr.type}</span>
    </div>
  );

  const renderMethod = (method: UMLMethod) => {
    const params = method.parameters
      .map(p => `${p.name}: ${p.type}`)
      .join(', ');

    return (
      <div
        key={method.id}
        className={clsx(
          'px-3 py-1 text-sm font-mono hover:bg-gray-50 transition-colors',
          method.isAbstract && 'italic'
        )}
      >
        <span className="text-gray-600">{getVisibilitySymbol(method.visibility)}</span>
        <span className={clsx(method.isStatic && 'underline', 'ml-2')}>
          {method.name}({params})
        </span>
        <span className="text-gray-500">: {method.returnType}</span>
      </div>
    );
  };

  return (
    <BaseNode 
      id={id} 
      data={data} 
      selected={selected}
      className="min-w-[280px]"
    >
      <div
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Class Name Section */}
        <div className={clsx(
          'bg-gradient-to-r from-purple-500 to-purple-600 text-white px-4 py-3 rounded-t',
          data.isAbstract && 'from-purple-400 to-purple-500'
        )}>
          {data.stereotype && (
            <div className="text-xs text-purple-100 mb-1">
              &#171;{data.stereotype}&#187;
            </div>
          )}
          <div className="flex items-center gap-2">
            <Package className="w-5 h-5" />
            <span className={clsx(
              'font-bold text-lg flex-1',
              data.isAbstract && 'italic'
            )}>
              {umlClass.name}
            </span>
            {isHovered && (
              <button className="p-1 hover:bg-purple-400 rounded transition-colors">
                <Edit2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Attributes Section */}
        <div className="border-t-2 border-gray-300">
          <div className="bg-gray-50 px-3 py-1.5 border-b border-gray-200">
            <span className="text-xs font-semibold text-gray-600 uppercase">Attributes</span>
          </div>
          {umlClass.attributes.length > 0 ? (
            umlClass.attributes.map(renderAttribute)
          ) : (
            <div className="px-4 py-2 text-sm text-gray-400 italic">
              No attributes
            </div>
          )}
        </div>

        {/* Methods Section */}
        <div className="border-t-2 border-gray-300">
          <div className="bg-gray-50 px-3 py-1.5 border-b border-gray-200">
            <span className="text-xs font-semibold text-gray-600 uppercase">Methods</span>
          </div>
          {umlClass.methods.length > 0 ? (
            umlClass.methods.map(renderMethod)
          ) : (
            <div className="px-4 py-2 text-sm text-gray-400 italic">
              No methods
            </div>
          )}
        </div>

        {/* Footer - Add Actions */}
        {isHovered && (
          <div className="border-t border-gray-200 px-3 py-2 flex gap-2">
            <button className="flex-1 flex items-center justify-center gap-2 text-xs text-purple-600 hover:text-purple-700 transition-colors py-1">
              <Plus className="w-3 h-3" />
              <span>Attribute</span>
            </button>
            <button className="flex-1 flex items-center justify-center gap-2 text-xs text-purple-600 hover:text-purple-700 transition-colors py-1">
              <Plus className="w-3 h-3" />
              <span>Method</span>
            </button>
          </div>
        )}
      </div>
    </BaseNode>
  );
});

ClassNode.displayName = 'ClassNode';
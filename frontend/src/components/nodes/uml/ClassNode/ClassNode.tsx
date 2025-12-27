// frontend/src/components/nodes/uml/ClassNode/ClassNode.tsx
import { memo, useState } from 'react';
import { NodeProps, Handle, Position } from 'reactflow';
import { UMLNodeData, UMLAttribute, UMLMethod } from '../../../../types/diagram.types';
import { Package, Plus, Edit2 } from 'lucide-react';
import clsx from 'clsx';

export const ClassNode = memo<NodeProps<UMLNodeData>>(({ id, data, selected }) => {
  const [isHovered, setIsHovered] = useState(false);
  const umlClass = data.class;

  if (!umlClass) {
    return (
      <div className="min-w-[250px] bg-white border-2 border-purple-500 rounded shadow-sm">
        <div className="bg-purple-500 text-white px-4 py-3 rounded-t flex items-center gap-2">
          <Package className="w-5 h-5" />
          <span className="font-bold">New Class</span>
        </div>
        <div className="px-4 py-3 text-sm text-gray-400 italic">
          No attributes or methods defined
        </div>
      </div>
    );
  }

  // Get visibility symbol
  const getVisibilitySymbol = (visibility: string) => {
    switch (visibility) {
      case 'public':
        return '+';
      case 'private':
        return '-';
      case 'protected':
        return '#';
      case 'package':
        return '~';
      default:
        return '';
    }
  };

  // Render attribute
  const renderAttribute = (attr: UMLAttribute) => (
    <div
      key={attr.id}
      className="px-3 py-1.5 text-sm flex items-start gap-2 hover:bg-gray-50 transition-colors font-mono group"
    >
      <Handle
        type="target"
        position={Position.Left}
        id={`${id}-attr-${attr.id}-target`}
        className="w-2 h-2 !bg-purple-400 border border-white opacity-0 group-hover:opacity-100 transition-opacity"
        style={{ left: -4 }}
      />
      
      <span className="text-purple-600 font-bold w-4 text-center flex-shrink-0">
        {getVisibilitySymbol(attr.visibility)}
      </span>
      <span className={clsx(
        'flex-1',
        attr.isStatic && 'underline',
        attr.isFinal && 'font-bold'
      )}>
        {attr.name}: {attr.type}
      </span>

      <Handle
        type="source"
        position={Position.Right}
        id={`${id}-attr-${attr.id}-source`}
        className="w-2 h-2 !bg-purple-400 border border-white opacity-0 group-hover:opacity-100 transition-opacity"
        style={{ right: -4 }}
      />
    </div>
  );

  // Render method
  const renderMethod = (method: UMLMethod) => {
    const params = method.parameters
      .map(p => `${p.name}: ${p.type}`)
      .join(', ');
    
    return (
      <div
        key={method.id}
        className="px-3 py-1.5 text-sm flex items-start gap-2 hover:bg-gray-50 transition-colors font-mono"
      >
        <span className="text-purple-600 font-bold w-4 text-center flex-shrink-0">
          {getVisibilitySymbol(method.visibility)}
        </span>
        <span className={clsx(
          'flex-1 break-all',
          method.isStatic && 'underline',
          method.isAbstract && 'italic'
        )}>
          {method.name}({params}): {method.returnType}
        </span>
      </div>
    );
  };

  return (
    <div
      className={clsx(
        'relative transition-all duration-200',
        selected && 'ring-2 ring-purple-500 ring-offset-2 rounded'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Main class connection handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-purple-500 border-2 border-white"
      />
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-purple-500 border-2 border-white"
      />

      <div className="min-w-[280px] max-w-[450px] bg-white border-2 border-purple-500 rounded shadow-md overflow-hidden">
        {/* Header */}
        <div className={clsx(
          'bg-gradient-to-r from-purple-500 to-purple-600 text-white px-4 py-3 rounded-t',
          data.isAbstract && 'from-purple-400 to-purple-500'
        )}>
          {data.stereotype && (
            <div className="text-xs text-purple-100 mb-1 text-center">
              &#171;{data.stereotype}&#187;
            </div>
          )}
          <div className="flex items-center gap-2">
            <Package className="w-5 h-5 flex-shrink-0" />
            <span className={clsx(
              'font-bold text-lg flex-1 truncate',
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
          <div className="bg-gray-50 px-3 py-1 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-600 uppercase">
                Attributes
              </span>
              {isHovered && (
                <button className="text-purple-600 hover:text-purple-700">
                  <Plus className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
          {umlClass.attributes.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {umlClass.attributes.map(renderAttribute)}
            </div>
          ) : (
            <div className="px-4 py-2 text-sm text-gray-400 italic text-center">
              No attributes
            </div>
          )}
        </div>

        {/* Methods Section */}
        <div className="border-t-2 border-gray-300">
          <div className="bg-gray-50 px-3 py-1 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-600 uppercase">
                Methods
              </span>
              {isHovered && (
                <button className="text-purple-600 hover:text-purple-700">
                  <Plus className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
          {umlClass.methods.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {umlClass.methods.map(renderMethod)}
            </div>
          ) : (
            <div className="px-4 py-2 text-sm text-gray-400 italic text-center">
              No methods
            </div>
          )}
        </div>

        {/* Footer */}
        {isHovered && (
          <div className="border-t border-gray-200 px-3 py-2 flex gap-2 bg-gray-50">
            <button className="flex-1 flex items-center justify-center gap-1 text-xs text-purple-600 hover:text-purple-700 transition-colors py-1">
              <Plus className="w-3 h-3" />
              <span>Attribute</span>
            </button>
            <button className="flex-1 flex items-center justify-center gap-1 text-xs text-purple-600 hover:text-purple-700 transition-colors py-1">
              <Plus className="w-3 h-3" />
              <span>Method</span>
            </button>
          </div>
        )}
      </div>

      {/* Main class connection handles */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-purple-500 border-2 border-white"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-purple-500 border-2 border-white"
      />
    </div>
  );
});

ClassNode.displayName = 'ClassNode';
// frontend/src/components/nodes/uml/ClassNode/ClassNode.tsx
import { memo, useState, useCallback, useRef, useEffect } from 'react';
import { NodeProps, Handle, Position } from 'reactflow';
import { UMLNodeData, UMLAttribute, UMLMethod } from '../../../../types/diagram.types';
import { Box, Plus, Edit2, Check, X, Lock, Eye, EyeOff } from 'lucide-react';
import clsx from 'clsx';
import { useDiagramStore } from '../../../../store/diagramStore';

export const ClassNode = memo<NodeProps<UMLNodeData>>(({ id, data, selected }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [editingClassName, setEditingClassName] = useState(false);
  const [editingAttrId, setEditingAttrId] = useState<string | null>(null);
  const [editingMethodId, setEditingMethodId] = useState<string | null>(null);
  const [tempClassName, setTempClassName] = useState('');
  const [tempAttrName, setTempAttrName] = useState('');
  const [tempAttrType, setTempAttrType] = useState('');
  const [tempMethodName, setTempMethodName] = useState('');
  const [tempMethodReturn, setTempMethodReturn] = useState('');
  
  const classNameInputRef = useRef<HTMLInputElement>(null);
  const attrNameInputRef = useRef<HTMLInputElement>(null);
  const methodNameInputRef = useRef<HTMLInputElement>(null);
  
  const { updateNode } = useDiagramStore();
  const umlClass = data.class;

  // Focus input when editing starts
  useEffect(() => {
    if (editingClassName && classNameInputRef.current) {
      classNameInputRef.current.focus();
      classNameInputRef.current.select();
    }
  }, [editingClassName]);

  useEffect(() => {
    if (editingAttrId && attrNameInputRef.current) {
      attrNameInputRef.current.focus();
      attrNameInputRef.current.select();
    }
  }, [editingAttrId]);

  useEffect(() => {
    if (editingMethodId && methodNameInputRef.current) {
      methodNameInputRef.current.focus();
      methodNameInputRef.current.select();
    }
  }, [editingMethodId]);

  const handleStartEditClassName = useCallback(() => {
    if (umlClass) {
      setTempClassName(umlClass.name);
      setEditingClassName(true);
    }
  }, [umlClass]);

  const handleSaveClassName = useCallback(() => {
    if (umlClass && tempClassName.trim()) {
      updateNode(id, {
        class: { ...umlClass, name: tempClassName.trim() },
        label: tempClassName.trim()
      });
    }
    setEditingClassName(false);
  }, [id, umlClass, tempClassName, updateNode]);

  const handleCancelEditClassName = useCallback(() => {
    setEditingClassName(false);
    setTempClassName('');
  }, []);

  const handleClassNameKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSaveClassName();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancelEditClassName();
    }
  }, [handleSaveClassName, handleCancelEditClassName]);

  const handleStartEditAttribute = useCallback((attr: UMLAttribute) => {
    setEditingAttrId(attr.id);
    setTempAttrName(attr.name);
    setTempAttrType(attr.type);
  }, []);

  const handleSaveAttribute = useCallback(() => {
    if (umlClass && editingAttrId && tempAttrName.trim()) {
      const updatedAttributes = umlClass.attributes.map(attr =>
        attr.id === editingAttrId
          ? { ...attr, name: tempAttrName.trim(), type: tempAttrType.trim() }
          : attr
      );
      updateNode(id, {
        class: { ...umlClass, attributes: updatedAttributes }
      });
    }
    setEditingAttrId(null);
    setTempAttrName('');
    setTempAttrType('');
  }, [id, umlClass, editingAttrId, tempAttrName, tempAttrType, updateNode]);

  const handleCancelEditAttribute = useCallback(() => {
    setEditingAttrId(null);
    setTempAttrName('');
    setTempAttrType('');
  }, []);

  const handleAttributeKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSaveAttribute();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancelEditAttribute();
    }
  }, [handleSaveAttribute, handleCancelEditAttribute]);

  const handleStartEditMethod = useCallback((method: UMLMethod) => {
    setEditingMethodId(method.id);
    setTempMethodName(method.name);
    setTempMethodReturn(method.returnType);
  }, []);

  const handleSaveMethod = useCallback(() => {
    if (umlClass && editingMethodId && tempMethodName.trim()) {
      const updatedMethods = umlClass.methods.map(method =>
        method.id === editingMethodId
          ? { ...method, name: tempMethodName.trim(), returnType: tempMethodReturn.trim() }
          : method
      );
      updateNode(id, {
        class: { ...umlClass, methods: updatedMethods }
      });
    }
    setEditingMethodId(null);
    setTempMethodName('');
    setTempMethodReturn('');
  }, [id, umlClass, editingMethodId, tempMethodName, tempMethodReturn, updateNode]);

  const handleCancelEditMethod = useCallback(() => {
    setEditingMethodId(null);
    setTempMethodName('');
    setTempMethodReturn('');
  }, []);

  const handleMethodKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSaveMethod();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancelEditMethod();
    }
  }, [handleSaveMethod, handleCancelEditMethod]);

  const handleToggleAttrVisibility = useCallback((attrId: string) => {
    if (!umlClass) return;
    const updatedAttributes = umlClass.attributes.map(attr => {
      if (attr.id === attrId) {
        const visibilityOrder = ['private', 'protected', 'public', 'package'];
        const currentIndex = visibilityOrder.indexOf(attr.visibility);
        const nextIndex = (currentIndex + 1) % visibilityOrder.length;
        return { ...attr, visibility: visibilityOrder[nextIndex] as any };
      }
      return attr;
    });
    updateNode(id, {
      class: { ...umlClass, attributes: updatedAttributes }
    });
  }, [id, umlClass, updateNode]);

  const handleToggleMethodVisibility = useCallback((methodId: string) => {
    if (!umlClass) return;
    const updatedMethods = umlClass.methods.map(method => {
      if (method.id === methodId) {
        const visibilityOrder = ['private', 'protected', 'public', 'package'];
        const currentIndex = visibilityOrder.indexOf(method.visibility);
        const nextIndex = (currentIndex + 1) % visibilityOrder.length;
        return { ...method, visibility: visibilityOrder[nextIndex] as any };
      }
      return method;
    });
    updateNode(id, {
      class: { ...umlClass, methods: updatedMethods }
    });
  }, [id, umlClass, updateNode]);

  const handleAddAttribute = useCallback(() => {
    if (!umlClass) return;
    const newAttribute: UMLAttribute = {
      id: `attr_${Date.now()}`,
      name: 'newAttribute',
      type: 'String',
      visibility: 'private',
    };
    updateNode(id, {
      class: {
        ...umlClass,
        attributes: [...umlClass.attributes, newAttribute]
      }
    });
    setTimeout(() => {
      setEditingAttrId(newAttribute.id);
      setTempAttrName(newAttribute.name);
      setTempAttrType(newAttribute.type);
    }, 10);
  }, [id, umlClass, updateNode]);

  const handleAddMethod = useCallback(() => {
    if (!umlClass) return;
    const newMethod: UMLMethod = {
      id: `method_${Date.now()}`,
      name: 'newMethod',
      returnType: 'void',
      parameters: [],
      visibility: 'public',
    };
    updateNode(id, {
      class: {
        ...umlClass,
        methods: [...umlClass.methods, newMethod]
      }
    });
    setTimeout(() => {
      setEditingMethodId(newMethod.id);
      setTempMethodName(newMethod.name);
      setTempMethodReturn(newMethod.returnType);
    }, 10);
  }, [id, umlClass, updateNode]);

  const getVisibilityIcon = (visibility: string) => {
    switch (visibility) {
      case 'private':
        return <Lock className="w-3 h-3 text-red-600" />;
      case 'protected':
        return <EyeOff className="w-3 h-3 text-yellow-600" />;
      case 'public':
        return <Eye className="w-3 h-3 text-green-600" />;
      default:
        return <Box className="w-3 h-3 text-gray-600" />;
    }
  };

  const getVisibilitySymbol = (visibility: string) => {
    switch (visibility) {
      case 'private':
        return '-';
      case 'protected':
        return '#';
      case 'public':
        return '+';
      default:
        return '~';
    }
  };

  if (!umlClass) {
    return (
      <div className="min-w-[250px] bg-white border-2 border-purple-500 rounded shadow-sm">
        <div className="bg-purple-500 text-white px-4 py-3 rounded-t flex items-center gap-2">
          <Box className="w-5 h-5" />
          <span className="font-bold">New Class</span>
        </div>
        <div className="px-4 py-3 text-sm text-gray-400 italic">
          No attributes or methods defined
        </div>
      </div>
    );
  }

  const renderAttribute = (attr: UMLAttribute) => {
    const isEditing = editingAttrId === attr.id;

    return (
      <div
        key={attr.id}
        className={clsx(
          'px-3 py-1.5 text-sm flex items-center gap-2 hover:bg-gray-50 transition-colors group',
          isEditing && 'bg-purple-50'
        )}
      >
        <button
          onClick={() => handleToggleAttrVisibility(attr.id)}
          className="flex-shrink-0 hover:scale-110 transition-transform"
          title={`Visibility: ${attr.visibility} (click to change)`}
        >
          {getVisibilityIcon(attr.visibility)}
        </button>
        
        {isEditing ? (
          <>
            <input
              ref={attrNameInputRef}
              type="text"
              value={tempAttrName}
              onChange={(e) => setTempAttrName(e.target.value)}
              onKeyDown={handleAttributeKeyDown}
              onClick={(e) => e.stopPropagation()}
              className="flex-1 px-1 py-0.5 text-sm border border-purple-400 rounded focus:outline-none focus:ring-1 focus:ring-purple-500"
              placeholder="Attribute name"
            />
            <span className="text-gray-400">:</span>
            <input
              type="text"
              value={tempAttrType}
              onChange={(e) => setTempAttrType(e.target.value)}
              onKeyDown={handleAttributeKeyDown}
              onClick={(e) => e.stopPropagation()}
              className="w-20 px-1 py-0.5 text-xs border border-purple-400 rounded focus:outline-none focus:ring-1 focus:ring-purple-500"
              placeholder="Type"
            />
            <div className="flex items-center gap-1">
              <button
                onClick={handleSaveAttribute}
                className="p-0.5 text-green-600 hover:bg-green-100 rounded"
              >
                <Check className="w-3 h-3" />
              </button>
              <button
                onClick={handleCancelEditAttribute}
                className="p-0.5 text-red-600 hover:bg-red-100 rounded"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          </>
        ) : (
          <>
            <span
              className="flex-1 truncate cursor-pointer font-mono"
              onDoubleClick={() => handleStartEditAttribute(attr)}
              title="Double-click to edit"
            >
              {getVisibilitySymbol(attr.visibility)} {attr.name}: {attr.type}
            </span>
            <button
              onClick={() => handleStartEditAttribute(attr)}
              className="opacity-0 group-hover:opacity-100 p-0.5 text-purple-600 hover:bg-purple-100 rounded transition-opacity"
            >
              <Edit2 className="w-3 h-3" />
            </button>
          </>
        )}
      </div>
    );
  };

  const renderMethod = (method: UMLMethod) => {
    const isEditing = editingMethodId === method.id;

    return (
      <div
        key={method.id}
        className={clsx(
          'px-3 py-1.5 text-sm flex items-center gap-2 hover:bg-gray-50 transition-colors group',
          isEditing && 'bg-purple-50'
        )}
      >
        <button
          onClick={() => handleToggleMethodVisibility(method.id)}
          className="flex-shrink-0 hover:scale-110 transition-transform"
          title={`Visibility: ${method.visibility} (click to change)`}
        >
          {getVisibilityIcon(method.visibility)}
        </button>
        
        {isEditing ? (
          <>
            <input
              ref={methodNameInputRef}
              type="text"
              value={tempMethodName}
              onChange={(e) => setTempMethodName(e.target.value)}
              onKeyDown={handleMethodKeyDown}
              onClick={(e) => e.stopPropagation()}
              className="flex-1 px-1 py-0.5 text-sm border border-purple-400 rounded focus:outline-none focus:ring-1 focus:ring-purple-500"
              placeholder="Method name"
            />
            <span className="text-gray-400">:</span>
            <input
              type="text"
              value={tempMethodReturn}
              onChange={(e) => setTempMethodReturn(e.target.value)}
              onKeyDown={handleMethodKeyDown}
              onClick={(e) => e.stopPropagation()}
              className="w-20 px-1 py-0.5 text-xs border border-purple-400 rounded focus:outline-none focus:ring-1 focus:ring-purple-500"
              placeholder="Return"
            />
            <div className="flex items-center gap-1">
              <button
                onClick={handleSaveMethod}
                className="p-0.5 text-green-600 hover:bg-green-100 rounded"
              >
                <Check className="w-3 h-3" />
              </button>
              <button
                onClick={handleCancelEditMethod}
                className="p-0.5 text-red-600 hover:bg-red-100 rounded"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          </>
        ) : (
          <>
            <span
              className="flex-1 truncate cursor-pointer font-mono"
              onDoubleClick={() => handleStartEditMethod(method)}
              title="Double-click to edit"
            >
              {getVisibilitySymbol(method.visibility)} {method.name}(): {method.returnType}
            </span>
            <button
              onClick={() => handleStartEditMethod(method)}
              className="opacity-0 group-hover:opacity-100 p-0.5 text-purple-600 hover:bg-purple-100 rounded transition-opacity"
            >
              <Edit2 className="w-3 h-3" />
            </button>
          </>
        )}
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

      <div className={clsx(
        'min-w-[280px] max-w-[400px] bg-white rounded shadow-md overflow-hidden border-2',
        data.isAbstract ? 'border-dashed border-purple-500' : 'border-purple-500'
      )}>
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white px-4 py-3">
          {data.stereotype && (
            <div className="text-xs text-purple-200 mb-1">
              «{data.stereotype}»
            </div>
          )}
          <div className="flex items-center gap-2">
            <Box className="w-5 h-5 flex-shrink-0" />
            
            {editingClassName ? (
              <div className="flex-1 flex items-center gap-2">
                <input
                  ref={classNameInputRef}
                  type="text"
                  value={tempClassName}
                  onChange={(e) => setTempClassName(e.target.value)}
                  onKeyDown={handleClassNameKeyDown}
                  onClick={(e) => e.stopPropagation()}
                  className="flex-1 px-2 py-1 text-sm text-gray-900 border border-white rounded focus:outline-none focus:ring-2 focus:ring-white"
                />
                <button
                  onClick={handleSaveClassName}
                  className="p-1 hover:bg-purple-400 rounded transition-colors"
                >
                  <Check className="w-4 h-4" />
                </button>
                <button
                  onClick={handleCancelEditClassName}
                  className="p-1 hover:bg-purple-400 rounded transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <>
                <span
                  className={clsx(
                    'font-bold text-lg flex-1 truncate cursor-pointer',
                    data.isAbstract && 'italic'
                  )}
                  onDoubleClick={handleStartEditClassName}
                  title="Double-click to edit"
                >
                  {umlClass.name}
                </span>
                {isHovered && (
                  <button
                    onClick={handleStartEditClassName}
                    className="p-1 hover:bg-purple-400 rounded transition-colors"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                )}
              </>
            )}
          </div>
        </div>

        {/* Attributes Section */}
        <div className="border-t-2 border-gray-200">
          {umlClass.attributes.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {umlClass.attributes.map(renderAttribute)}
            </div>
          ) : (
            <div className="px-4 py-2 text-xs text-gray-400 italic text-center">
              No attributes
            </div>
          )}
          <div className="border-t border-gray-200 px-3 py-1 bg-gray-50">
            <button
              onClick={handleAddAttribute}
              className="w-full flex items-center justify-center gap-1 text-xs text-purple-600 hover:text-purple-700 transition-colors"
            >
              <Plus className="w-3 h-3" />
              <span>Add Attribute</span>
            </button>
          </div>
        </div>

        {/* Methods Section */}
        <div className="border-t-2 border-gray-200">
          {umlClass.methods.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {umlClass.methods.map(renderMethod)}
            </div>
          ) : (
            <div className="px-4 py-2 text-xs text-gray-400 italic text-center">
              No methods
            </div>
          )}
          <div className="border-t border-gray-200 px-3 py-1 bg-gray-50">
            <button
              onClick={handleAddMethod}
              className="w-full flex items-center justify-center gap-1 text-xs text-purple-600 hover:text-purple-700 transition-colors"
            >
              <Plus className="w-3 h-3" />
              <span>Add Method</span>
            </button>
          </div>
        </div>
      </div>

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
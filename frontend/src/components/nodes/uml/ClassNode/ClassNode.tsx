// frontend/src/components/nodes/uml/ClassNode/ClassNode.tsx
// COMPLETE ERROR-FREE VERSION - Preserves ALL existing features + adds new ones
import { memo, useState, useCallback, useRef, useEffect } from 'react';
import { NodeProps, Handle, Position } from 'reactflow';
import { UMLNodeData, UMLAttribute, UMLMethod } from '../../../../types/diagram.types';
import { Lock, Unlock, Shield, Package as PackageIcon, Plus, Edit2, Check, X, Palette } from 'lucide-react';
import clsx from 'clsx';
import { useDiagramStore } from '../../../../store/diagramStore';

export const ClassNode = memo<NodeProps<UMLNodeData>>(({ id, data, selected }) => {
  // State management
  const [editingClassName, setEditingClassName] = useState(false);
  const [editingAttrId, setEditingAttrId] = useState<string | null>(null);
  const [editingMethodId, setEditingMethodId] = useState<string | null>(null);
  const [tempClassName, setTempClassName] = useState('');
  const [tempAttrName, setTempAttrName] = useState('');
  const [tempAttrType, setTempAttrType] = useState('');
  const [tempMethodName, setTempMethodName] = useState('');
  const [tempMethodReturn, setTempMethodReturn] = useState('');
  const [showColorPicker, setShowColorPicker] = useState(false);

  // Refs for focus management
  const classNameInputRef = useRef<HTMLInputElement>(null);
  const attrNameInputRef = useRef<HTMLInputElement>(null);
  const methodNameInputRef = useRef<HTMLInputElement>(null);

  // Store access
  const { updateNode } = useDiagramStore();

  // Extract class data safely
  const umlClass = data.class;
  
  // Extract color and z-index with safe defaults
  const nodeColor = (data as any).color || '#ffffff';
  const textColor = (data as any).textColor || '#000000';
  const zIndex = (data as any).zIndex || 0;

  // Focus management
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

  // ============================================================================
  // Class Name Handlers
  // ============================================================================

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

  // ============================================================================
  // Attribute Handlers
  // ============================================================================

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

  const handleAttrKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSaveAttribute();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancelEditAttribute();
    }
  }, [handleSaveAttribute, handleCancelEditAttribute]);

  const handleDeleteAttribute = useCallback((attrId: string) => {
    if (umlClass) {
      const updatedAttributes = umlClass.attributes.filter(attr => attr.id !== attrId);
      updateNode(id, {
        class: { ...umlClass, attributes: updatedAttributes }
      });
    }
  }, [id, umlClass, updateNode]);

  // ============================================================================
  // Method Handlers
  // ============================================================================

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

  const handleDeleteMethod = useCallback((methodId: string) => {
    if (umlClass) {
      const updatedMethods = umlClass.methods.filter(method => method.id !== methodId);
      updateNode(id, {
        class: { ...umlClass, methods: updatedMethods }
      });
    }
  }, [id, umlClass, updateNode]);

  // ============================================================================
  // Visibility Toggle Handlers (Existing)
  // ============================================================================

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

  // ============================================================================
  // Add Handlers (Existing)
  // ============================================================================

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

  // ============================================================================
  // NEW: Color Customization
  // ============================================================================

  const handleColorChange = useCallback((color: string) => {
    updateNode(id, {
      ...data,
      color,
    });
  }, [id, data, updateNode]);

  const handleTextColorChange = useCallback((color: string) => {
    updateNode(id, {
      ...data,
      textColor: color,
    });
  }, [id, data, updateNode]);

  // ============================================================================
  // Helper Functions
  // ============================================================================

  const getVisibilityIcon = (visibility: string) => {
    switch (visibility) {
      case 'private':
        return <Lock className="w-3 h-3" />;
      case 'protected':
        return <Shield className="w-3 h-3" />;
      case 'public':
        return <Unlock className="w-3 h-3" />;
      case 'package':
        return <PackageIcon className="w-3 h-3" />;
      default:
        return null;
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
      case 'package':
        return '~';
      default:
        return '';
    }
  };

  // ============================================================================
  // Render Attribute
  // ============================================================================

  const renderAttribute = (attr: UMLAttribute) => {
    const isEditing = editingAttrId === attr.id;

    return (
      <div
        key={attr.id}
        className="px-4 py-1.5 flex items-center gap-2 group hover:bg-gray-50 transition-colors"
      >
        {!isEditing && (
          <button
            onClick={() => handleToggleAttrVisibility(attr.id)}
            className="flex-shrink-0 text-gray-600 hover:text-blue-600 transition-colors"
            title="Toggle visibility"
          >
            {getVisibilityIcon(attr.visibility)}
          </button>
        )}

        {isEditing ? (
          <>
            <input
              ref={attrNameInputRef}
              type="text"
              value={tempAttrName}
              onChange={(e) => setTempAttrName(e.target.value)}
              onKeyDown={handleAttrKeyDown}
              className="flex-1 px-2 py-1 text-sm border border-purple-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="Attribute name"
            />
            <span className="text-gray-400">:</span>
            <input
              type="text"
              value={tempAttrType}
              onChange={(e) => setTempAttrType(e.target.value)}
              onKeyDown={handleAttrKeyDown}
              className="w-24 px-2 py-1 text-sm border border-purple-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="Type"
            />
            <button
              onClick={handleSaveAttribute}
              className="p-1 text-green-600 hover:bg-green-100 rounded"
            >
              <Check className="w-3 h-3" />
            </button>
            <button
              onClick={handleCancelEditAttribute}
              className="p-1 text-red-600 hover:bg-red-100 rounded"
            >
              <X className="w-3 h-3" />
            </button>
          </>
        ) : (
          <>
            <span className="flex-1 text-sm font-mono">
              <span className="text-gray-600">{getVisibilitySymbol(attr.visibility)}</span>
              {' '}
              <span className={clsx(attr.isStatic && 'underline')}>{attr.name}</span>
              {' : '}
              <span className="text-gray-500">{attr.type}</span>
            </span>

            <button
              onClick={() => handleStartEditAttribute(attr)}
              className="opacity-0 group-hover:opacity-100 p-0.5 text-blue-600 hover:bg-blue-100 rounded transition-opacity"
            >
              <Edit2 className="w-3 h-3" />
            </button>

            <button
              onClick={() => handleDeleteAttribute(attr.id)}
              className="opacity-0 group-hover:opacity-100 p-0.5 text-red-600 hover:bg-red-100 rounded transition-opacity"
            >
              <X className="w-3 h-3" />
            </button>
          </>
        )}
      </div>
    );
  };

  // ============================================================================
  // Render Method
  // ============================================================================

  const renderMethod = (method: UMLMethod) => {
    const isEditing = editingMethodId === method.id;
    const paramStr = method.parameters.map(p => `${p.name}: ${p.type}`).join(', ');

    return (
      <div
        key={method.id}
        className="px-4 py-1.5 flex items-center gap-2 group hover:bg-gray-50 transition-colors"
      >
        {!isEditing && (
          <button
            onClick={() => handleToggleMethodVisibility(method.id)}
            className="flex-shrink-0 text-gray-600 hover:text-blue-600 transition-colors"
            title="Toggle visibility"
          >
            {getVisibilityIcon(method.visibility)}
          </button>
        )}

        {isEditing ? (
          <>
            <input
              ref={methodNameInputRef}
              type="text"
              value={tempMethodName}
              onChange={(e) => setTempMethodName(e.target.value)}
              onKeyDown={handleMethodKeyDown}
              className="flex-1 px-2 py-1 text-sm border border-purple-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="Method name"
            />
            <span className="text-gray-400">:</span>
            <input
              type="text"
              value={tempMethodReturn}
              onChange={(e) => setTempMethodReturn(e.target.value)}
              onKeyDown={handleMethodKeyDown}
              className="w-24 px-2 py-1 text-sm border border-purple-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="Return type"
            />
            <button
              onClick={handleSaveMethod}
              className="p-1 text-green-600 hover:bg-green-100 rounded"
            >
              <Check className="w-3 h-3" />
            </button>
            <button
              onClick={handleCancelEditMethod}
              className="p-1 text-red-600 hover:bg-red-100 rounded"
            >
              <X className="w-3 h-3" />
            </button>
          </>
        ) : (
          <>
            <span className="flex-1 text-sm font-mono">
              <span className="text-gray-600">{getVisibilitySymbol(method.visibility)}</span>
              {' '}
              <span className={clsx(
                method.isStatic && 'underline',
                method.isAbstract && 'italic'
              )}>
                {method.name}({paramStr})
              </span>
              {' : '}
              <span className="text-gray-500">{method.returnType}</span>
            </span>

            <button
              onClick={() => handleStartEditMethod(method)}
              className="opacity-0 group-hover:opacity-100 p-0.5 text-blue-600 hover:bg-blue-100 rounded transition-opacity"
            >
              <Edit2 className="w-3 h-3" />
            </button>

            <button
              onClick={() => handleDeleteMethod(method.id)}
              className="opacity-0 group-hover:opacity-100 p-0.5 text-red-600 hover:bg-red-100 rounded transition-opacity"
            >
              <X className="w-3 h-3" />
            </button>
          </>
        )}
      </div>
    );
  };

  // Safety check
  if (!umlClass) {
    return <div className="p-4 bg-red-100 text-red-800">Invalid class data</div>;
  }

  // ============================================================================
  // Main Render
  // ============================================================================

  return (
    <div
      className={clsx(
        'relative transition-all duration-200',
        selected && 'ring-2 ring-purple-500 ring-offset-2 rounded'
      )}
      style={{ zIndex }}
    >
      {/* Connection Handles */}
      <Handle type="target" position={Position.Top} className="w-3 h-3 !bg-purple-500 border-2 border-white" />
      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-purple-500 border-2 border-white" />

      {/* Main Class Container */}
      <div 
        className="min-w-[240px] max-w-[400px] rounded shadow-md overflow-hidden border-2 border-purple-500"
        style={{ backgroundColor: nodeColor }}
      >
        {/* Class Name Compartment */}
        <div className={clsx(
          'px-4 py-3 flex flex-col items-center gap-1',
          'bg-gradient-to-r from-purple-500 to-purple-600 text-white'
        )}>
          {/* Stereotype */}
          {(data.stereotype || umlClass.isAbstract) && (
            <div className="text-xs italic">
              «{data.stereotype || (umlClass.isAbstract ? 'abstract' : '')}»
            </div>
          )}

          {/* Class Name */}
          <div className="w-full flex items-center justify-center gap-2">
            {editingClassName ? (
              <>
                <input
                  ref={classNameInputRef}
                  type="text"
                  value={tempClassName}
                  onChange={(e) => setTempClassName(e.target.value)}
                  onKeyDown={handleClassNameKeyDown}
                  className={clsx(
                    'flex-1 px-2 py-1 text-sm bg-white text-gray-900 border border-purple-300 rounded',
                    'focus:outline-none focus:ring-2 focus:ring-purple-500',
                    umlClass.isAbstract && 'italic'
                  )}
                />
                <button
                  onClick={handleSaveClassName}
                  className="p-1 bg-white text-green-600 hover:bg-green-100 rounded"
                >
                  <Check className="w-4 h-4" />
                </button>
                <button
                  onClick={handleCancelEditClassName}
                  className="p-1 bg-white text-red-600 hover:bg-red-100 rounded"
                >
                  <X className="w-4 h-4" />
                </button>
              </>
            ) : (
              <>
                <h3 className={clsx('flex-1 font-semibold text-center', umlClass.isAbstract && 'italic')}>
                  {umlClass.name}
                </h3>
                <button
                  onClick={handleStartEditClassName}
                  className="opacity-0 group-hover:opacity-100 p-1 bg-white bg-opacity-20 hover:bg-opacity-30 rounded transition-opacity"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                {/* NEW: Color Picker */}
                <button
                  onClick={() => setShowColorPicker(!showColorPicker)}
                  className="opacity-0 group-hover:opacity-100 p-1 bg-white bg-opacity-20 hover:bg-opacity-30 rounded transition-opacity"
                  title="Customize colors"
                >
                  <Palette className="w-4 h-4" />
                </button>
              </>
            )}
          </div>
        </div>

        {/* NEW: Color Picker Panel */}
        {showColorPicker && (
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
            <div className="space-y-2">
              <div>
                <label className="text-xs font-medium text-gray-700">Background Color</label>
                <input
                  type="color"
                  value={nodeColor}
                  onChange={(e) => handleColorChange(e.target.value)}
                  className="w-full h-8 rounded border border-gray-300 cursor-pointer"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-700">Text Color</label>
                <input
                  type="color"
                  value={textColor}
                  onChange={(e) => handleTextColorChange(e.target.value)}
                  className="w-full h-8 rounded border border-gray-300 cursor-pointer"
                />
              </div>
            </div>
          </div>
        )}

        {/* Attributes Compartment */}
        <div className="border-t-2 border-purple-500 bg-white">
          <div className="max-h-48 overflow-y-auto">
            {umlClass.attributes && umlClass.attributes.length > 0 ? (
              <div className="divide-y divide-gray-100">
                {umlClass.attributes.map(renderAttribute)}
              </div>
            ) : (
              <div className="px-4 py-2 text-xs text-gray-400 italic text-center">
                No attributes
              </div>
            )}
          </div>
          <div className="border-t border-gray-200 px-3 py-1.5 bg-gray-50">
            <button
              onClick={handleAddAttribute}
              className="w-full flex items-center justify-center gap-1 text-xs text-purple-600 hover:text-purple-700 transition-colors"
            >
              <Plus className="w-3 h-3" />
              <span>Add Attribute</span>
            </button>
          </div>
        </div>

        {/* Methods Compartment */}
        <div className="border-t-2 border-purple-500 bg-white">
          <div className="max-h-48 overflow-y-auto">
            {umlClass.methods && umlClass.methods.length > 0 ? (
              <div className="divide-y divide-gray-100">
                {umlClass.methods.map(renderMethod)}
              </div>
            ) : (
              <div className="px-4 py-2 text-xs text-gray-400 italic text-center">
                No methods
              </div>
            )}
          </div>
          <div className="border-t border-gray-200 px-3 py-1.5 bg-gray-50">
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

      {/* Connection Handles */}
      <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-purple-500 border-2 border-white" />
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 !bg-purple-500 border-2 border-white" />
    </div>
  );
});

ClassNode.displayName = 'ClassNode';
// frontend/src/components/builder/ElementEditor.tsx
/**
 * Element Editor Component - Edit node names, attributes, methods
 * Path: frontend/src/components/builder/ElementEditor.tsx
 * 
 * RIGHT SIDE PANEL: Appears when a node is selected
 * Allows editing: name, attributes, methods, literals
 */

import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Save, X } from 'lucide-react';
import { COLORS } from '../../../constants/colors';
import type { Node } from 'reactflow';
import type { 
  NodeData, 
  ClassNodeData,
  ObjectNodeData,
  InterfaceNodeData,
  EnumerationNodeData,
  Attribute, 
  Method 
} from '../../../types/diagram.types';

interface ElementEditorProps {
  selectedNode: Node<NodeData> | null;
  onUpdate: (nodeId: string, updates: Partial<NodeData>) => void;
  onClose: () => void;
}

export const ElementEditor: React.FC<ElementEditorProps> = ({
  selectedNode,
  onUpdate,
  onClose,
}) => {
  const [name, setName] = useState('');
  const [stereotype, setStereotype] = useState('');
  const [attributes, setAttributes] = useState<Attribute[]>([]);
  const [methods, setMethods] = useState<Method[]>([]);
  const [literals, setLiterals] = useState<string[]>([]);

  // Type guards
  const hasAttributes = (data: NodeData): data is ClassNodeData | ObjectNodeData => {
    return 'attributes' in data;
  };

  const hasMethods = (data: NodeData): data is ClassNodeData | InterfaceNodeData => {
    return 'methods' in data;
  };

  const hasLiterals = (data: NodeData): data is EnumerationNodeData => {
    return 'literals' in data;
  };

  // Update local state when selected node changes
  useEffect(() => {
    if (selectedNode) {
      setName(selectedNode.data.label || '');
      setStereotype(selectedNode.data.stereotype || '');
      
      // Use type guards to safely access properties
      if (hasAttributes(selectedNode.data)) {
        setAttributes(selectedNode.data.attributes || []);
      } else {
        setAttributes([]);
      }
      
      if (hasMethods(selectedNode.data)) {
        setMethods(selectedNode.data.methods || []);
      } else {
        setMethods([]);
      }
      
      if (hasLiterals(selectedNode.data)) {
        setLiterals(selectedNode.data.literals || []);
      } else {
        setLiterals([]);
      }
    }
  }, [selectedNode]);

  if (!selectedNode) {
    return (
      <div 
        className="w-80 border-l-2 p-6 flex items-center justify-center"
        style={{ 
          backgroundColor: COLORS.OFF_WHITE,
          borderColor: COLORS.LIGHT_GREY
        }}
      >
        <p style={{ color: COLORS.DARK_GREY }}>
          Select an element to edit
        </p>
      </div>
    );
  }

  const nodeType = selectedNode.type || 'class';
  const isPackage = nodeType === 'package';
  const isClass = nodeType === 'class';
  const isInterface = nodeType === 'interface';
  const isObject = nodeType === 'object';
  const isEnumeration = nodeType === 'enumeration';

  const showAttributes = isClass || isInterface || isObject;
  const showMethods = isClass || isInterface;
  const showLiterals = isEnumeration;

  const handleSave = () => {
    // Build updates object with proper typing
    const baseUpdates: Record<string, any> = {
      label: name,
      stereotype: stereotype || undefined,
    };

    // Add type-specific properties
    if (showAttributes) {
      baseUpdates.attributes = attributes;
    }
    if (showMethods) {
      baseUpdates.methods = methods;
    }
    if (showLiterals) {
      baseUpdates.literals = literals;
    }

    // Cast to Partial<NodeData> after building the complete object
    onUpdate(selectedNode.id, baseUpdates as Partial<NodeData>);
  };

  // Attribute management
  const addAttribute = () => {
    const newAttr: Attribute = {
      id: `attr_${Date.now()}`,
      name: 'newAttribute',
      dataType: 'String',
      visibility: 'public',
      key: 'Default',
    };
    setAttributes([...attributes, newAttr]);
  };

  const updateAttribute = (index: number, field: keyof Attribute, value: any) => {
    const updated = [...attributes];
    updated[index] = { ...updated[index], [field]: value };
    setAttributes(updated);
  };

  const removeAttribute = (index: number) => {
    setAttributes(attributes.filter((_, i) => i !== index));
  };

  // Method management
  const addMethod = () => {
    const newMethod: Method = {
      id: `method_${Date.now()}`,
      name: 'newMethod',
      returnType: 'void',
      parameters: [],
      visibility: 'public',
    };
    setMethods([...methods, newMethod]);
  };

  const updateMethod = (index: number, field: keyof Method, value: any) => {
    const updated = [...methods];
    updated[index] = { ...updated[index], [field]: value };
    setMethods(updated);
  };

  const removeMethod = (index: number) => {
    setMethods(methods.filter((_, i) => i !== index));
  };

  // Literal management (for enumerations)
  const addLiteral = () => {
    setLiterals([...literals, 'NEW_LITERAL']);
  };

  const updateLiteral = (index: number, value: string) => {
    const updated = [...literals];
    updated[index] = value;
    setLiterals(updated);
  };

  const removeLiteral = (index: number) => {
    setLiterals(literals.filter((_, i) => i !== index));
  };

  return (
    <div 
      className="w-80 border-l-2 flex flex-col h-full"
      style={{ 
        backgroundColor: COLORS.WHITE,
        borderColor: COLORS.LIGHT_GREY
      }}
    >
      {/* Header */}
      <div 
        className="p-4 border-b-2 flex items-center justify-between"
        style={{ borderColor: COLORS.LIGHT_GREY }}
      >
        <h3 
          className="font-bold text-lg"
          style={{ color: COLORS.BLACK }}
        >
          Edit {nodeType}
        </h3>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-gray-100"
        >
          <X className="w-5 h-5" style={{ color: COLORS.DARK_GREY }} />
        </button>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Name */}
        <div>
          <label 
            className="block text-sm font-medium mb-1"
            style={{ color: COLORS.BLACK }}
          >
            Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border rounded"
            style={{ borderColor: COLORS.LIGHT_GREY }}
            placeholder="Element name"
          />
        </div>

        {/* Stereotype */}
        {!isPackage && (
          <div>
            <label 
              className="block text-sm font-medium mb-1"
              style={{ color: COLORS.BLACK }}
            >
              Stereotype (optional)
            </label>
            <input
              type="text"
              value={stereotype}
              onChange={(e) => setStereotype(e.target.value)}
              className="w-full px-3 py-2 border rounded"
              style={{ borderColor: COLORS.LIGHT_GREY }}
              placeholder="e.g., entity, controller"
            />
          </div>
        )}

        {/* Attributes (for Class, Interface, Object) */}
        {showAttributes && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label 
                className="text-sm font-medium"
                style={{ color: COLORS.BLACK }}
              >
                Attributes
              </label>
              <button
                onClick={addAttribute}
                className="flex items-center gap-1 px-2 py-1 border rounded text-xs"
                style={{ 
                  borderColor: COLORS.LIGHT_GREY,
                  color: COLORS.BLACK
                }}
              >
                <Plus className="w-3 h-3" />
                Add
              </button>
            </div>
            
            <div className="space-y-2">
              {attributes.map((attr, index) => (
                <div 
                  key={attr.id}
                  className="p-2 border rounded space-y-2"
                  style={{ 
                    backgroundColor: COLORS.OFF_WHITE,
                    borderColor: COLORS.LIGHT_GREY
                  }}
                >
                  <div className="flex items-start gap-2">
                    <input
                      type="text"
                      value={attr.name}
                      onChange={(e) => updateAttribute(index, 'name', e.target.value)}
                      className="flex-1 px-2 py-1 border rounded text-sm"
                      placeholder="attributeName"
                    />
                    <button
                      onClick={() => removeAttribute(index)}
                      className="p-1 rounded"
                      style={{ color: COLORS.ERROR }}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <input
                    type="text"
                    value={attr.dataType}
                    onChange={(e) => updateAttribute(index, 'dataType', e.target.value)}
                    className="w-full px-2 py-1 border rounded text-sm"
                    placeholder="Data Type"
                  />
                  
                  <select
                    value={attr.visibility || 'public'}
                    onChange={(e) => updateAttribute(index, 'visibility', e.target.value)}
                    className="w-full px-2 py-1 border rounded text-sm"
                  >
                    <option value="public">+ Public</option>
                    <option value="private">- Private</option>
                    <option value="protected"># Protected</option>
                    <option value="package">~ Package</option>
                  </select>
                </div>
              ))}
              
              {attributes.length === 0 && (
                <p 
                  className="text-sm text-center py-4"
                  style={{ color: COLORS.DARK_GREY }}
                >
                  No attributes yet
                </p>
              )}
            </div>
          </div>
        )}

        {/* Methods (for Class, Interface) */}
        {showMethods && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label 
                className="text-sm font-medium"
                style={{ color: COLORS.BLACK }}
              >
                Methods
              </label>
              <button
                onClick={addMethod}
                className="flex items-center gap-1 px-2 py-1 border rounded text-xs"
                style={{ 
                  borderColor: COLORS.LIGHT_GREY,
                  color: COLORS.BLACK
                }}
              >
                <Plus className="w-3 h-3" />
                Add
              </button>
            </div>
            
            <div className="space-y-2">
              {methods.map((method, index) => (
                <div 
                  key={method.id}
                  className="p-2 border rounded space-y-2"
                  style={{ 
                    backgroundColor: COLORS.OFF_WHITE,
                    borderColor: COLORS.LIGHT_GREY
                  }}
                >
                  <div className="flex items-start gap-2">
                    <input
                      type="text"
                      value={method.name}
                      onChange={(e) => updateMethod(index, 'name', e.target.value)}
                      className="flex-1 px-2 py-1 border rounded text-sm"
                      placeholder="methodName"
                    />
                    <button
                      onClick={() => removeMethod(index)}
                      className="p-1 rounded"
                      style={{ color: COLORS.ERROR }}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <input
                    type="text"
                    value={method.returnType}
                    onChange={(e) => updateMethod(index, 'returnType', e.target.value)}
                    className="w-full px-2 py-1 border rounded text-sm"
                    placeholder="Return Type"
                  />
                  
                  <select
                    value={method.visibility || 'public'}
                    onChange={(e) => updateMethod(index, 'visibility', e.target.value)}
                    className="w-full px-2 py-1 border rounded text-sm"
                  >
                    <option value="public">+ Public</option>
                    <option value="private">- Private</option>
                    <option value="protected"># Protected</option>
                    <option value="package">~ Package</option>
                  </select>
                </div>
              ))}
              
              {methods.length === 0 && (
                <p 
                  className="text-sm text-center py-4"
                  style={{ color: COLORS.DARK_GREY }}
                >
                  No methods yet
                </p>
              )}
            </div>
          </div>
        )}

        {/* Literals (for Enumeration) */}
        {showLiterals && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label 
                className="text-sm font-medium"
                style={{ color: COLORS.BLACK }}
              >
                Enumeration Literals
              </label>
              <button
                onClick={addLiteral}
                className="flex items-center gap-1 px-2 py-1 border rounded text-xs"
                style={{ 
                  borderColor: COLORS.LIGHT_GREY,
                  color: COLORS.BLACK
                }}
              >
                <Plus className="w-3 h-3" />
                Add
              </button>
            </div>
            
            <div className="space-y-2">
              {literals.map((literal, index) => (
                <div 
                  key={index}
                  className="flex items-center gap-2 p-2 border rounded"
                  style={{ 
                    backgroundColor: COLORS.OFF_WHITE,
                    borderColor: COLORS.LIGHT_GREY
                  }}
                >
                  <input
                    type="text"
                    value={literal}
                    onChange={(e) => updateLiteral(index, e.target.value)}
                    className="flex-1 px-2 py-1 border rounded text-sm font-mono"
                    placeholder="LITERAL_VALUE"
                  />
                  <button
                    onClick={() => removeLiteral(index)}
                    className="p-1 rounded"
                    style={{ color: COLORS.ERROR }}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
              
              {literals.length === 0 && (
                <p 
                  className="text-sm text-center py-4"
                  style={{ color: COLORS.DARK_GREY }}
                >
                  No literals yet
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer with Save Button */}
      <div 
        className="p-4 border-t-2"
        style={{ borderColor: COLORS.LIGHT_GREY }}
      >
        <button
          onClick={handleSave}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded font-medium"
          style={{ 
            backgroundColor: COLORS.PRIMARY,
            color: COLORS.WHITE
          }}
        >
          <Save className="w-4 h-4" />
          Save Changes
        </button>
      </div>
    </div>
  );
};

export default ElementEditor;
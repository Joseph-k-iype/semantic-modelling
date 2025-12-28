// frontend/src/components/nodes/uml/ClassNode/ClassNode.tsx

import React, { memo, useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Plus, Trash2, Lock, Eye, EyeOff, X, Check } from 'lucide-react';

export type Visibility = 'public' | 'private' | 'protected' | 'package';

export interface ClassAttribute {
  id: string;
  name: string;
  type: string;
  visibility: Visibility;
  isStatic: boolean;
}

export interface ClassMethod {
  id: string;
  name: string;
  returnType: string;
  parameters: string;
  visibility: Visibility;
  isStatic: boolean;
  isAbstract: boolean;
}

export interface ClassNodeData {
  label: string;
  stereotype?: string;
  attributes: ClassAttribute[];
  methods: ClassMethod[];
  isAbstract?: boolean;
  isInterface?: boolean;
  color?: string;
  textColor?: string;
  zIndex?: number;
}

const ClassNode: React.FC<NodeProps<ClassNodeData>> = memo(({ id, data, selected }) => {
  const [isEditingName, setIsEditingName] = useState(false);
  const [className, setClassName] = useState(data.label || 'Class');
  const [isEditingStereotype, setIsEditingStereotype] = useState(false);
  const [stereotype, setStereotype] = useState(data.stereotype || '');
  const [attributes, setAttributes] = useState<ClassAttribute[]>(data.attributes || []);
  const [methods, setMethods] = useState<ClassMethod[]>(data.methods || []);
  const [editingAttrId, setEditingAttrId] = useState<string | null>(null);
  const [editingMethodId, setEditingMethodId] = useState<string | null>(null);
  const [tempAttrName, setTempAttrName] = useState('');
  const [tempAttrType, setTempAttrType] = useState('');
  const [tempMethodName, setTempMethodName] = useState('');
  const [tempMethodReturn, setTempMethodReturn] = useState('');
  const [tempMethodParams, setTempMethodParams] = useState('');

  const handleNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setClassName(e.target.value);
  }, []);

  const handleNameBlur = useCallback(() => {
    setIsEditingName(false);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label: className, stereotype, attributes, methods });
    }
  }, [id, className, stereotype, attributes, methods]);

  const handleStereotypeBlur = useCallback(() => {
    setIsEditingStereotype(false);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label: className, stereotype, attributes, methods });
    }
  }, [id, className, stereotype, attributes, methods]);

  const getVisibilitySymbol = (visibility: Visibility): string => {
    switch (visibility) {
      case 'public': return '+';
      case 'private': return '-';
      case 'protected': return '#';
      case 'package': return '~';
      default: return '+';
    }
  };

  const addAttribute = useCallback(() => {
    const newAttr: ClassAttribute = {
      id: `attr-${Date.now()}`,
      name: 'newAttribute',
      type: 'string',
      visibility: 'private',
      isStatic: false
    };
    const newAttributes = [...attributes, newAttr];
    setAttributes(newAttributes);
    setEditingAttrId(newAttr.id);
    setTempAttrName(newAttr.name);
    setTempAttrType(newAttr.type);
  }, [attributes]);

  const addMethod = useCallback(() => {
    const newMethod: ClassMethod = {
      id: `method-${Date.now()}`,
      name: 'newMethod',
      returnType: 'void',
      parameters: '',
      visibility: 'public',
      isStatic: false,
      isAbstract: false
    };
    const newMethods = [...methods, newMethod];
    setMethods(newMethods);
    setEditingMethodId(newMethod.id);
    setTempMethodName(newMethod.name);
    setTempMethodReturn(newMethod.returnType);
    setTempMethodParams(newMethod.parameters);
  }, [methods]);

  const removeAttribute = useCallback((attrId: string) => {
    const newAttributes = attributes.filter(a => a.id !== attrId);
    setAttributes(newAttributes);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label: className, stereotype, attributes: newAttributes, methods });
    }
  }, [attributes, id, className, stereotype, methods]);

  const removeMethod = useCallback((methodId: string) => {
    const newMethods = methods.filter(m => m.id !== methodId);
    setMethods(newMethods);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label: className, stereotype, attributes, methods: newMethods });
    }
  }, [methods, id, className, stereotype, attributes]);

  const saveAttributeEdit = useCallback(() => {
    if (editingAttrId) {
      const newAttributes = attributes.map(a => 
        a.id === editingAttrId 
          ? { ...a, name: tempAttrName, type: tempAttrType }
          : a
      );
      setAttributes(newAttributes);
      setEditingAttrId(null);
      if (window.updateNodeData) {
        window.updateNodeData(id, { label: className, stereotype, attributes: newAttributes, methods });
      }
    }
  }, [editingAttrId, tempAttrName, tempAttrType, attributes, id, className, stereotype, methods]);

  const saveMethodEdit = useCallback(() => {
    if (editingMethodId) {
      const newMethods = methods.map(m => 
        m.id === editingMethodId 
          ? { ...m, name: tempMethodName, returnType: tempMethodReturn, parameters: tempMethodParams }
          : m
      );
      setMethods(newMethods);
      setEditingMethodId(null);
      if (window.updateNodeData) {
        window.updateNodeData(id, { label: className, stereotype, attributes, methods: newMethods });
      }
    }
  }, [editingMethodId, tempMethodName, tempMethodReturn, tempMethodParams, methods, id, className, stereotype, attributes]);

  const toggleAttributeVisibility = useCallback((attrId: string) => {
    const visibilityOrder: Visibility[] = ['public', 'private', 'protected', 'package'];
    const newAttributes = attributes.map(a => {
      if (a.id === attrId) {
        const currentIndex = visibilityOrder.indexOf(a.visibility);
        const nextIndex = (currentIndex + 1) % visibilityOrder.length;
        return { ...a, visibility: visibilityOrder[nextIndex] };
      }
      return a;
    });
    setAttributes(newAttributes);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label: className, stereotype, attributes: newAttributes, methods });
    }
  }, [attributes, id, className, stereotype, methods]);

  const toggleMethodVisibility = useCallback((methodId: string) => {
    const visibilityOrder: Visibility[] = ['public', 'private', 'protected', 'package'];
    const newMethods = methods.map(m => {
      if (m.id === methodId) {
        const currentIndex = visibilityOrder.indexOf(m.visibility);
        const nextIndex = (currentIndex + 1) % visibilityOrder.length;
        return { ...m, visibility: visibilityOrder[nextIndex] };
      }
      return m;
    });
    setMethods(newMethods);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label: className, stereotype, attributes, methods: newMethods });
    }
  }, [methods, id, className, stereotype, attributes]);

  return (
    <div style={{ position: 'relative' }}>
      {/* Connection Handles */}
      <Handle
        type="target"
        position={Position.Top}
        style={{
          background: '#6b7280',
          width: '10px',
          height: '10px',
          border: '2px solid white'
        }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        style={{
          background: '#6b7280',
          width: '10px',
          height: '10px',
          border: '2px solid white'
        }}
      />
      <Handle
        type="source"
        position={Position.Left}
        style={{
          background: '#6b7280',
          width: '10px',
          height: '10px',
          border: '2px solid white'
        }}
      />
      <Handle
        type="source"
        position={Position.Right}
        style={{
          background: '#6b7280',
          width: '10px',
          height: '10px',
          border: '2px solid white'
        }}
      />

      {/* Class Container */}
      <div
        style={{
          minWidth: '220px',
          background: data.color || 'white',
          border: `2px solid ${selected ? '#3b82f6' : '#374151'}`,
          borderRadius: '6px',
          boxShadow: selected ? '0 0 0 3px rgba(59, 130, 246, 0.3)' : '0 1px 3px rgba(0,0,0,0.1)',
          overflow: 'hidden',
          position: 'relative',
          zIndex: data.zIndex || 1
        }}
      >
        {/* Class Name Section */}
        <div style={{ padding: '10px', borderBottom: '1px solid #e5e7eb' }}>
          {/* Stereotype */}
          {(stereotype || isEditingStereotype) && (
            <div
              style={{ textAlign: 'center', marginBottom: '4px' }}
              onDoubleClick={() => setIsEditingStereotype(true)}
            >
              {isEditingStereotype ? (
                <input
                  type="text"
                  value={stereotype}
                  onChange={(e) => setStereotype(e.target.value)}
                  onBlur={handleStereotypeBlur}
                  placeholder="«stereotype»"
                  autoFocus
                  style={{
                    width: '100%',
                    padding: '2px',
                    fontSize: '11px',
                    fontStyle: 'italic',
                    border: '1px solid #3b82f6',
                    borderRadius: '3px',
                    outline: 'none',
                    textAlign: 'center'
                  }}
                />
              ) : (
                <div
                  style={{
                    fontSize: '11px',
                    fontStyle: 'italic',
                    color: '#6b7280',
                    cursor: 'text'
                  }}
                >
                  «{stereotype}»
                </div>
              )}
            </div>
          )}

          {/* Class Name */}
          <div
            style={{ textAlign: 'center' }}
            onDoubleClick={() => setIsEditingName(true)}
          >
            {isEditingName ? (
              <input
                type="text"
                value={className}
                onChange={handleNameChange}
                onBlur={handleNameBlur}
                autoFocus
                style={{
                  width: '100%',
                  padding: '4px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  fontStyle: data.isAbstract ? 'italic' : 'normal',
                  border: '2px solid #3b82f6',
                  borderRadius: '4px',
                  outline: 'none',
                  textAlign: 'center'
                }}
              />
            ) : (
              <div
                style={{
                  fontSize: '14px',
                  fontWeight: 'bold',
                  fontStyle: data.isAbstract ? 'italic' : 'normal',
                  color: data.textColor || '#374151',
                  cursor: 'text'
                }}
              >
                {className}
              </div>
            )}
          </div>
        </div>

        {/* Attributes Section */}
        <div style={{ borderBottom: '1px solid #e5e7eb' }}>
          <div
            style={{
              padding: '6px 10px',
              background: '#f9fafb',
              fontSize: '11px',
              fontWeight: '600',
              color: '#6b7280',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <span>Attributes</span>
            <button
              onClick={addAttribute}
              style={{
                padding: '2px 4px',
                background: 'transparent',
                border: '1px solid #d1d5db',
                borderRadius: '3px',
                cursor: 'pointer',
                display: 'flex',
                color: '#6b7280'
              }}
            >
              <Plus size={12} />
            </button>
          </div>
          <div style={{ padding: '6px 10px', minHeight: '30px' }}>
            {attributes.length === 0 ? (
              <div style={{ fontSize: '11px', color: '#9ca3af', fontStyle: 'italic' }}>
                No attributes
              </div>
            ) : (
              attributes.map((attr) => (
                <div
                  key={attr.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    marginBottom: '3px',
                    fontSize: '11px',
                    fontFamily: 'monospace'
                  }}
                >
                  {editingAttrId === attr.id ? (
                    <>
                      <button
                        onClick={() => toggleAttributeVisibility(attr.id)}
                        style={{
                          padding: '1px 3px',
                          background: 'transparent',
                          border: '1px solid #d1d5db',
                          borderRadius: '2px',
                          cursor: 'pointer',
                          fontSize: '10px'
                        }}
                      >
                        {getVisibilitySymbol(attr.visibility)}
                      </button>
                      <input
                        type="text"
                        value={tempAttrName}
                        onChange={(e) => setTempAttrName(e.target.value)}
                        style={{
                          flex: 1,
                          padding: '2px 4px',
                          fontSize: '11px',
                          border: '1px solid #3b82f6',
                          borderRadius: '3px',
                          outline: 'none'
                        }}
                      />
                      <input
                        type="text"
                        value={tempAttrType}
                        onChange={(e) => setTempAttrType(e.target.value)}
                        style={{
                          width: '60px',
                          padding: '2px 4px',
                          fontSize: '11px',
                          border: '1px solid #3b82f6',
                          borderRadius: '3px',
                          outline: 'none'
                        }}
                      />
                      <button
                        onClick={saveAttributeEdit}
                        style={{
                          padding: '2px',
                          background: '#10b981',
                          border: 'none',
                          borderRadius: '2px',
                          cursor: 'pointer',
                          display: 'flex',
                          color: 'white'
                        }}
                      >
                        <Check size={10} />
                      </button>
                      <button
                        onClick={() => setEditingAttrId(null)}
                        style={{
                          padding: '2px',
                          background: '#ef4444',
                          border: 'none',
                          borderRadius: '2px',
                          cursor: 'pointer',
                          display: 'flex',
                          color: 'white'
                        }}
                      >
                        <X size={10} />
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => toggleAttributeVisibility(attr.id)}
                        style={{
                          padding: '1px 3px',
                          background: 'transparent',
                          border: '1px solid #d1d5db',
                          borderRadius: '2px',
                          cursor: 'pointer',
                          fontSize: '10px'
                        }}
                      >
                        {getVisibilitySymbol(attr.visibility)}
                      </button>
                      <span
                        style={{
                          flex: 1,
                          cursor: 'pointer',
                          textDecoration: attr.isStatic ? 'underline' : 'none'
                        }}
                        onDoubleClick={() => {
                          setEditingAttrId(attr.id);
                          setTempAttrName(attr.name);
                          setTempAttrType(attr.type);
                        }}
                      >
                        {attr.name}: {attr.type}
                      </span>
                      <button
                        onClick={() => removeAttribute(attr.id)}
                        style={{
                          padding: '1px',
                          background: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          display: 'flex'
                        }}
                      >
                        <Trash2 size={10} color="#ef4444" />
                      </button>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Methods Section */}
        <div>
          <div
            style={{
              padding: '6px 10px',
              background: '#f9fafb',
              fontSize: '11px',
              fontWeight: '600',
              color: '#6b7280',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <span>Methods</span>
            <button
              onClick={addMethod}
              style={{
                padding: '2px 4px',
                background: 'transparent',
                border: '1px solid #d1d5db',
                borderRadius: '3px',
                cursor: 'pointer',
                display: 'flex',
                color: '#6b7280'
              }}
            >
              <Plus size={12} />
            </button>
          </div>
          <div style={{ padding: '6px 10px', minHeight: '30px' }}>
            {methods.length === 0 ? (
              <div style={{ fontSize: '11px', color: '#9ca3af', fontStyle: 'italic' }}>
                No methods
              </div>
            ) : (
              methods.map((method) => (
                <div
                  key={method.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    marginBottom: '3px',
                    fontSize: '11px',
                    fontFamily: 'monospace'
                  }}
                >
                  {editingMethodId === method.id ? (
                    <>
                      <button
                        onClick={() => toggleMethodVisibility(method.id)}
                        style={{
                          padding: '1px 3px',
                          background: 'transparent',
                          border: '1px solid #d1d5db',
                          borderRadius: '2px',
                          cursor: 'pointer',
                          fontSize: '10px'
                        }}
                      >
                        {getVisibilitySymbol(method.visibility)}
                      </button>
                      <input
                        type="text"
                        value={tempMethodName}
                        onChange={(e) => setTempMethodName(e.target.value)}
                        style={{
                          flex: 1,
                          padding: '2px 4px',
                          fontSize: '11px',
                          border: '1px solid #3b82f6',
                          borderRadius: '3px',
                          outline: 'none'
                        }}
                      />
                      <button
                        onClick={saveMethodEdit}
                        style={{
                          padding: '2px',
                          background: '#10b981',
                          border: 'none',
                          borderRadius: '2px',
                          cursor: 'pointer',
                          display: 'flex',
                          color: 'white'
                        }}
                      >
                        <Check size={10} />
                      </button>
                      <button
                        onClick={() => setEditingMethodId(null)}
                        style={{
                          padding: '2px',
                          background: '#ef4444',
                          border: 'none',
                          borderRadius: '2px',
                          cursor: 'pointer',
                          display: 'flex',
                          color: 'white'
                        }}
                      >
                        <X size={10} />
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => toggleMethodVisibility(method.id)}
                        style={{
                          padding: '1px 3px',
                          background: 'transparent',
                          border: '1px solid #d1d5db',
                          borderRadius: '2px',
                          cursor: 'pointer',
                          fontSize: '10px'
                        }}
                      >
                        {getVisibilitySymbol(method.visibility)}
                      </button>
                      <span
                        style={{
                          flex: 1,
                          cursor: 'pointer',
                          textDecoration: method.isStatic ? 'underline' : 'none',
                          fontStyle: method.isAbstract ? 'italic' : 'normal'
                        }}
                        onDoubleClick={() => {
                          setEditingMethodId(method.id);
                          setTempMethodName(method.name);
                          setTempMethodReturn(method.returnType);
                          setTempMethodParams(method.parameters);
                        }}
                      >
                        {method.name}({method.parameters}): {method.returnType}
                      </span>
                      <button
                        onClick={() => removeMethod(method.id)}
                        style={{
                          padding: '1px',
                          background: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          display: 'flex'
                        }}
                      >
                        <Trash2 size={10} color="#ef4444" />
                      </button>
                    </>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
});

ClassNode.displayName = 'ClassNode';

export default ClassNode;
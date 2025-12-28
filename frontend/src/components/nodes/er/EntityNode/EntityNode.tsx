// frontend/src/components/nodes/er/EntityNode/EntityNode.tsx

import React, { memo, useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Plus, Trash2, Key, X, Check } from 'lucide-react';

export interface Attribute {
  id: string;
  name: string;
  type: string;
  isPrimaryKey: boolean;
  isForeignKey: boolean;
  isUnique: boolean;
  isNullable: boolean;
}

export interface EntityNodeData {
  label: string;
  attributes: Attribute[];
  primaryKeys: string[];
  foreignKeys: string[];
  color?: string;
  textColor?: string;
  zIndex?: number;
}

const EntityNode: React.FC<NodeProps<EntityNodeData>> = memo(({ id, data, selected }) => {
  const [isEditingName, setIsEditingName] = useState(false);
  const [entityName, setEntityName] = useState(data.label || 'Entity');
  const [attributes, setAttributes] = useState<Attribute[]>(data.attributes || []);
  const [editingAttrId, setEditingAttrId] = useState<string | null>(null);
  const [editingAttrName, setEditingAttrName] = useState('');
  const [editingAttrType, setEditingAttrType] = useState('');

  const handleNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setEntityName(e.target.value);
  }, []);

  const handleNameBlur = useCallback(() => {
    setIsEditingName(false);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label: entityName, attributes });
    }
  }, [id, entityName, attributes]);

  const handleNameKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleNameBlur();
    } else if (e.key === 'Escape') {
      setIsEditingName(false);
      setEntityName(data.label || 'Entity');
    }
  }, [handleNameBlur, data.label]);

  const addAttribute = useCallback(() => {
    const newAttr: Attribute = {
      id: `attr-${Date.now()}`,
      name: 'newAttribute',
      type: 'string',
      isPrimaryKey: false,
      isForeignKey: false,
      isUnique: false,
      isNullable: true
    };
    const newAttributes = [...attributes, newAttr];
    setAttributes(newAttributes);
    setEditingAttrId(newAttr.id);
    setEditingAttrName(newAttr.name);
    setEditingAttrType(newAttr.type);
  }, [attributes]);

  const removeAttribute = useCallback((attrId: string) => {
    const newAttributes = attributes.filter(a => a.id !== attrId);
    setAttributes(newAttributes);
    if (window.updateNodeData) {
      window.updateNodeData(id, { label: entityName, attributes: newAttributes });
    }
  }, [attributes, id, entityName]);

  const startEditAttribute = useCallback((attr: Attribute) => {
    setEditingAttrId(attr.id);
    setEditingAttrName(attr.name);
    setEditingAttrType(attr.type);
  }, []);

  const saveAttributeEdit = useCallback(() => {
    if (editingAttrId) {
      const newAttributes = attributes.map(a => 
        a.id === editingAttrId 
          ? { ...a, name: editingAttrName, type: editingAttrType }
          : a
      );
      setAttributes(newAttributes);
      setEditingAttrId(null);
      if (window.updateNodeData) {
        window.updateNodeData(id, { label: entityName, attributes: newAttributes });
      }
    }
  }, [editingAttrId, editingAttrName, editingAttrType, attributes, id, entityName]);

  const cancelAttributeEdit = useCallback(() => {
    setEditingAttrId(null);
    setEditingAttrName('');
    setEditingAttrType('');
  }, []);

  const togglePrimaryKey = useCallback((attrId: string) => {
    const newAttributes = attributes.map(a => 
      a.id === attrId ? { ...a, isPrimaryKey: !a.isPrimaryKey } : a
    );
    setAttributes(newAttributes);
    if (window.updateNodeData) {
      window.updateNodeData(id, { 
        label: entityName, 
        attributes: newAttributes,
        primaryKeys: newAttributes.filter(a => a.isPrimaryKey).map(a => a.id)
      });
    }
  }, [attributes, id, entityName]);

  const toggleForeignKey = useCallback((attrId: string) => {
    const newAttributes = attributes.map(a => 
      a.id === attrId ? { ...a, isForeignKey: !a.isForeignKey } : a
    );
    setAttributes(newAttributes);
    if (window.updateNodeData) {
      window.updateNodeData(id, { 
        label: entityName, 
        attributes: newAttributes,
        foreignKeys: newAttributes.filter(a => a.isForeignKey).map(a => a.id)
      });
    }
  }, [attributes, id, entityName]);

  return (
    <div style={{ position: 'relative' }}>
      {/* Connection Handles */}
      <Handle
        type="target"
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

      {/* Entity Container */}
      <div
        style={{
          minWidth: '200px',
          background: data.color || 'white',
          border: `2px solid ${selected ? '#3b82f6' : '#374151'}`,
          borderRadius: '8px',
          boxShadow: selected ? '0 0 0 3px rgba(59, 130, 246, 0.3)' : '0 1px 3px rgba(0,0,0,0.1)',
          overflow: 'hidden',
          position: 'relative',
          zIndex: data.zIndex || 1
        }}
      >
        {/* Entity Name Header */}
        <div
          style={{
            background: selected ? '#3b82f6' : '#374151',
            color: 'white',
            padding: '8px 12px',
            fontWeight: 'bold',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
          onDoubleClick={() => setIsEditingName(true)}
        >
          {isEditingName ? (
            <input
              type="text"
              value={entityName}
              onChange={handleNameChange}
              onBlur={handleNameBlur}
              onKeyDown={handleNameKeyDown}
              autoFocus
              style={{
                flex: 1,
                padding: '2px 6px',
                fontSize: '14px',
                fontWeight: 'bold',
                border: 'none',
                borderRadius: '3px',
                outline: 'none',
                color: '#111827'
              }}
            />
          ) : (
            <span>{entityName}</span>
          )}
          <button
            onClick={addAttribute}
            style={{
              padding: '2px 6px',
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              borderRadius: '3px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              color: 'white'
            }}
            title="Add Attribute"
          >
            <Plus size={14} />
          </button>
        </div>

        {/* Attributes List */}
        <div style={{ padding: '8px' }}>
          {attributes.length === 0 ? (
            <div
              style={{
                padding: '12px',
                textAlign: 'center',
                color: '#9ca3af',
                fontSize: '12px',
                fontStyle: 'italic'
              }}
            >
              No attributes. Click + to add.
            </div>
          ) : (
            attributes.map((attr) => (
              <div
                key={attr.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '4px',
                  marginBottom: '4px',
                  background: '#f9fafb',
                  borderRadius: '4px',
                  fontSize: '12px'
                }}
              >
                {/* Primary Key Icon */}
                <button
                  onClick={() => togglePrimaryKey(attr.id)}
                  style={{
                    padding: '2px',
                    background: attr.isPrimaryKey ? '#fbbf24' : 'transparent',
                    border: `1px solid ${attr.isPrimaryKey ? '#f59e0b' : '#d1d5db'}`,
                    borderRadius: '3px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                  title={attr.isPrimaryKey ? 'Primary Key' : 'Make Primary Key'}
                >
                  <Key size={12} color={attr.isPrimaryKey ? '#92400e' : '#6b7280'} />
                </button>

                {/* Foreign Key Badge */}
                {attr.isForeignKey && (
                  <span
                    style={{
                      padding: '1px 4px',
                      background: '#dbeafe',
                      border: '1px solid #3b82f6',
                      borderRadius: '3px',
                      fontSize: '9px',
                      fontWeight: 'bold',
                      color: '#1e40af'
                    }}
                  >
                    FK
                  </span>
                )}

                {/* Attribute Name and Type */}
                {editingAttrId === attr.id ? (
                  <>
                    <input
                      type="text"
                      value={editingAttrName}
                      onChange={(e) => setEditingAttrName(e.target.value)}
                      style={{
                        flex: 1,
                        padding: '2px 4px',
                        fontSize: '11px',
                        border: '1px solid #3b82f6',
                        borderRadius: '3px',
                        outline: 'none'
                      }}
                      placeholder="name"
                    />
                    <input
                      type="text"
                      value={editingAttrType}
                      onChange={(e) => setEditingAttrType(e.target.value)}
                      style={{
                        width: '60px',
                        padding: '2px 4px',
                        fontSize: '11px',
                        border: '1px solid #3b82f6',
                        borderRadius: '3px',
                        outline: 'none'
                      }}
                      placeholder="type"
                    />
                    <button
                      onClick={saveAttributeEdit}
                      style={{
                        padding: '2px',
                        background: '#10b981',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        display: 'flex',
                        color: 'white'
                      }}
                    >
                      <Check size={12} />
                    </button>
                    <button
                      onClick={cancelAttributeEdit}
                      style={{
                        padding: '2px',
                        background: '#ef4444',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        display: 'flex',
                        color: 'white'
                      }}
                    >
                      <X size={12} />
                    </button>
                  </>
                ) : (
                  <>
                    <span
                      style={{
                        flex: 1,
                        fontWeight: attr.isPrimaryKey ? 'bold' : 'normal',
                        color: data.textColor || '#374151',
                        cursor: 'pointer'
                      }}
                      onDoubleClick={() => startEditAttribute(attr)}
                    >
                      {attr.name}
                    </span>
                    <span
                      style={{
                        color: '#6b7280',
                        fontSize: '11px',
                        fontFamily: 'monospace'
                      }}
                    >
                      {attr.type}
                    </span>
                    <button
                      onClick={() => toggleForeignKey(attr.id)}
                      style={{
                        padding: '2px',
                        background: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '9px',
                        color: attr.isForeignKey ? '#3b82f6' : '#d1d5db'
                      }}
                      title="Toggle Foreign Key"
                    >
                      FK
                    </button>
                    <button
                      onClick={() => removeAttribute(attr.id)}
                      style={{
                        padding: '2px',
                        background: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        display: 'flex'
                      }}
                    >
                      <Trash2 size={12} color="#ef4444" />
                    </button>
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
});

EntityNode.displayName = 'EntityNode';

export default EntityNode;
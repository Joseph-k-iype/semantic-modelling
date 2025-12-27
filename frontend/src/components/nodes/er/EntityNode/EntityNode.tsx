// frontend/src/components/nodes/er/EntityNode/EntityNode.tsx
import { memo, useState, useCallback, useRef, useEffect } from 'react';
import { NodeProps, Handle, Position } from 'reactflow';
import { ERNodeData, ERAttribute } from '../../../../types/diagram.types';
import { Key, Lock, Database, Plus, Edit2, Check, X } from 'lucide-react';
import clsx from 'clsx';
import { useDiagramStore } from '../../../../store/diagramStore';

export const EntityNode = memo<NodeProps<ERNodeData>>(({ id, data, selected }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [editingEntityName, setEditingEntityName] = useState(false);
  const [editingAttrId, setEditingAttrId] = useState<string | null>(null);
  const [tempEntityName, setTempEntityName] = useState('');
  const [tempAttrName, setTempAttrName] = useState('');
  const [tempAttrType, setTempAttrType] = useState('');
  
  const entityNameInputRef = useRef<HTMLInputElement>(null);
  const attrNameInputRef = useRef<HTMLInputElement>(null);
  
  const { updateNode } = useDiagramStore();
  const entity = data.entity;

  // Focus input when editing starts
  useEffect(() => {
    if (editingEntityName && entityNameInputRef.current) {
      entityNameInputRef.current.focus();
      entityNameInputRef.current.select();
    }
  }, [editingEntityName]);

  useEffect(() => {
    if (editingAttrId && attrNameInputRef.current) {
      attrNameInputRef.current.focus();
      attrNameInputRef.current.select();
    }
  }, [editingAttrId]);

  const handleStartEditEntityName = useCallback(() => {
    if (entity) {
      setTempEntityName(entity.name);
      setEditingEntityName(true);
    }
  }, [entity]);

  const handleSaveEntityName = useCallback(() => {
    if (entity && tempEntityName.trim()) {
      updateNode(id, {
        entity: { ...entity, name: tempEntityName.trim() },
        label: tempEntityName.trim()
      });
    }
    setEditingEntityName(false);
  }, [id, entity, tempEntityName, updateNode]);

  const handleCancelEditEntityName = useCallback(() => {
    setEditingEntityName(false);
    setTempEntityName('');
  }, []);

  const handleEntityNameKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSaveEntityName();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancelEditEntityName();
    }
  }, [handleSaveEntityName, handleCancelEditEntityName]);

  const handleStartEditAttribute = useCallback((attr: ERAttribute) => {
    setEditingAttrId(attr.id);
    setTempAttrName(attr.name);
    setTempAttrType(attr.type);
  }, []);

  const handleSaveAttribute = useCallback(() => {
    if (entity && editingAttrId && tempAttrName.trim()) {
      const updatedAttributes = entity.attributes.map(attr =>
        attr.id === editingAttrId
          ? { ...attr, name: tempAttrName.trim(), type: tempAttrType.trim() }
          : attr
      );
      updateNode(id, {
        entity: { ...entity, attributes: updatedAttributes }
      });
    }
    setEditingAttrId(null);
    setTempAttrName('');
    setTempAttrType('');
  }, [id, entity, editingAttrId, tempAttrName, tempAttrType, updateNode]);

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

  const handleTogglePrimary = useCallback((attrId: string) => {
    if (!entity) return;
    const updatedAttributes = entity.attributes.map(attr =>
      attr.id === attrId ? { ...attr, isPrimary: !attr.isPrimary } : attr
    );
    updateNode(id, {
      entity: { ...entity, attributes: updatedAttributes }
    });
  }, [id, entity, updateNode]);

  const handleToggleForeign = useCallback((attrId: string) => {
    if (!entity) return;
    const updatedAttributes = entity.attributes.map(attr =>
      attr.id === attrId ? { ...attr, isForeign: !attr.isForeign } : attr
    );
    updateNode(id, {
      entity: { ...entity, attributes: updatedAttributes }
    });
  }, [id, entity, updateNode]);

  const handleToggleNullable = useCallback((attrId: string) => {
    if (!entity) return;
    const updatedAttributes = entity.attributes.map(attr =>
      attr.id === attrId ? { ...attr, isNullable: !attr.isNullable } : attr
    );
    updateNode(id, {
      entity: { ...entity, attributes: updatedAttributes }
    });
  }, [id, entity, updateNode]);

  const handleAddAttribute = useCallback(() => {
    if (!entity) return;
    const newAttribute: ERAttribute = {
      id: `attr_${Date.now()}`,
      name: 'newAttribute',
      type: 'VARCHAR(255)',
      isNullable: true,
    };
    updateNode(id, {
      entity: {
        ...entity,
        attributes: [...entity.attributes, newAttribute]
      }
    });
    // Start editing the new attribute
    setTimeout(() => {
      setEditingAttrId(newAttribute.id);
      setTempAttrName(newAttribute.name);
      setTempAttrType(newAttribute.type);
    }, 10);
  }, [id, entity, updateNode]);

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

  const renderAttribute = (attr: ERAttribute) => {
    const isEditing = editingAttrId === attr.id;

    return (
      <div
        key={attr.id}
        className={clsx(
          'px-3 py-2 text-sm flex items-center gap-2 hover:bg-gray-50 transition-colors group',
          attr.isPrimary && 'bg-yellow-50',
          isEditing && 'bg-blue-50'
        )}
      >
        <Handle
          type="target"
          position={Position.Left}
          id={`${id}-attr-${attr.id}-target`}
          className="w-2 h-2 !bg-blue-400 border border-white opacity-0 group-hover:opacity-100 transition-opacity"
          style={{ left: -4 }}
        />
        
        {/* Primary/Foreign Key indicators - clickable */}
        <button
          onClick={() => handleTogglePrimary(attr.id)}
          className={clsx(
            'w-3 h-3 flex-shrink-0 transition-opacity',
            attr.isPrimary ? 'opacity-100' : 'opacity-20 hover:opacity-60'
          )}
          title={attr.isPrimary ? 'Remove Primary Key' : 'Set as Primary Key'}
        >
          <Key className="w-3 h-3 text-yellow-600" />
        </button>
        
        <button
          onClick={() => handleToggleForeign(attr.id)}
          className={clsx(
            'w-3 h-3 flex-shrink-0 transition-opacity',
            attr.isForeign ? 'opacity-100' : 'opacity-20 hover:opacity-60'
          )}
          title={attr.isForeign ? 'Remove Foreign Key' : 'Set as Foreign Key'}
        >
          <Lock className="w-3 h-3 text-blue-600" />
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
              className="flex-1 px-1 py-0.5 text-sm border border-blue-400 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="Attribute name"
            />
            <input
              type="text"
              value={tempAttrType}
              onChange={(e) => setTempAttrType(e.target.value)}
              onKeyDown={handleAttributeKeyDown}
              onClick={(e) => e.stopPropagation()}
              className="w-24 px-1 py-0.5 text-xs border border-blue-400 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="Type"
            />
            <div className="flex items-center gap-1">
              <button
                onClick={handleSaveAttribute}
                className="p-0.5 text-green-600 hover:bg-green-100 rounded"
                title="Save"
              >
                <Check className="w-3 h-3" />
              </button>
              <button
                onClick={handleCancelEditAttribute}
                className="p-0.5 text-red-600 hover:bg-red-100 rounded"
                title="Cancel"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          </>
        ) : (
          <>
            <span
              className={clsx(
                'flex-1 truncate cursor-pointer',
                attr.isPrimary && 'font-semibold text-yellow-900'
              )}
              onDoubleClick={() => handleStartEditAttribute(attr)}
              title="Double-click to edit"
            >
              {attr.name}
            </span>
            
            <span className="text-gray-500 text-xs">
              {attr.type}
            </span>
            
            {/* Nullable indicator - clickable */}
            <button
              onClick={() => handleToggleNullable(attr.id)}
              className={clsx(
                'text-xs font-bold transition-opacity',
                attr.isNullable ? 'opacity-20 hover:opacity-60 text-gray-400' : 'opacity-100 text-red-500'
              )}
              title={attr.isNullable ? 'Set as NOT NULL' : 'Set as NULLABLE'}
            >
              {attr.isNullable ? 'N' : '*'}
            </button>
            
            {attr.isUnique && (
              <span className="text-purple-500 text-xs font-bold">U</span>
            )}

            <button
              onClick={() => handleStartEditAttribute(attr)}
              className="opacity-0 group-hover:opacity-100 p-0.5 text-blue-600 hover:bg-blue-100 rounded transition-opacity"
              title="Edit attribute"
            >
              <Edit2 className="w-3 h-3" />
            </button>
          </>
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
  };

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
          
          {editingEntityName ? (
            <div className="flex-1 flex items-center gap-2">
              <input
                ref={entityNameInputRef}
                type="text"
                value={tempEntityName}
                onChange={(e) => setTempEntityName(e.target.value)}
                onKeyDown={handleEntityNameKeyDown}
                onClick={(e) => e.stopPropagation()}
                className="flex-1 px-2 py-1 text-sm text-gray-900 border border-white rounded focus:outline-none focus:ring-2 focus:ring-white"
              />
              <button
                onClick={handleSaveEntityName}
                className="p-1 hover:bg-blue-400 rounded transition-colors"
                title="Save"
              >
                <Check className="w-4 h-4" />
              </button>
              <button
                onClick={handleCancelEditEntityName}
                className="p-1 hover:bg-blue-400 rounded transition-colors"
                title="Cancel"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <>
              <span
                className="font-bold text-lg flex-1 truncate cursor-pointer"
                onDoubleClick={handleStartEditEntityName}
                title="Double-click to edit"
              >
                {entity.name}
              </span>
              {isHovered && (
                <button
                  onClick={handleStartEditEntityName}
                  className="p-1 hover:bg-blue-400 rounded transition-colors"
                  title="Edit entity name"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
              )}
            </>
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
        <div className="border-t border-gray-200 px-3 py-2 bg-gray-50">
          <button
            onClick={handleAddAttribute}
            className="w-full flex items-center justify-center gap-2 text-sm text-blue-600 hover:text-blue-700 transition-colors py-1"
          >
            <Plus className="w-4 h-4" />
            <span>Add Attribute</span>
          </button>
        </div>
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
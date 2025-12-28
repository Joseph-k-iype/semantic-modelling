// frontend/src/components/nodes/er/EntityNode/EntityNode.tsx
// COMPLETE ERROR-FREE VERSION - Preserves ALL existing features + adds new ones
import { memo, useState, useCallback, useRef, useEffect } from 'react';
import { NodeProps, Handle, Position } from 'reactflow';
import { ERNodeData, ERAttribute } from '../../../../types/diagram.types';
import { Key, Lock, Database, Plus, Edit2, Check, X, Palette, Link as LinkIcon } from 'lucide-react';
import clsx from 'clsx';
import { useDiagramStore } from '../../../../store/diagramStore';

export const EntityNode = memo<NodeProps<ERNodeData>>(({ id, data, selected }) => {
  // State management
  const [isHovered, setIsHovered] = useState(false);
  const [editingEntityName, setEditingEntityName] = useState(false);
  const [editingAttrId, setEditingAttrId] = useState<string | null>(null);
  const [tempEntityName, setTempEntityName] = useState('');
  const [tempAttrName, setTempAttrName] = useState('');
  const [tempAttrType, setTempAttrType] = useState('');
  const [showColorPicker, setShowColorPicker] = useState(false);
  
  // Refs for focus management
  const entityNameInputRef = useRef<HTMLInputElement>(null);
  const attrNameInputRef = useRef<HTMLInputElement>(null);
  
  // Store access
  const { updateNode } = useDiagramStore();
  
  // Extract entity data safely
  const entity = data.entity;
  
  // Extract color and z-index with safe defaults
  const nodeColor = (data as any).color || '#ffffff';
  const textColor = (data as any).textColor || '#000000';
  const zIndex = (data as any).zIndex || 0;

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

  // ============================================================================
  // Entity Name Handlers
  // ============================================================================
  
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

  // ============================================================================
  // Attribute Edit Handlers
  // ============================================================================
  
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

  const handleAttrKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSaveAttribute();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancelEditAttribute();
    }
  }, [handleSaveAttribute, handleCancelEditAttribute]);

  // ============================================================================
  // Attribute CRUD Operations
  // ============================================================================
  
  const handleAddAttribute = useCallback(() => {
    if (entity) {
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
    }
  }, [id, entity, updateNode]);

  const handleDeleteAttribute = useCallback((attrId: string) => {
    if (entity) {
      const updatedAttributes = entity.attributes.filter(attr => attr.id !== attrId);
      updateNode(id, {
        entity: { ...entity, attributes: updatedAttributes }
      });
    }
  }, [id, entity, updateNode]);

  // ============================================================================
  // NEW: Primary/Foreign Key Toggles
  // ============================================================================
  
  const togglePrimaryKey = useCallback((attrId: string) => {
    if (entity) {
      const updatedAttributes = entity.attributes.map(attr =>
        attr.id === attrId
          ? { ...attr, isPrimaryKey: !(attr as any).isPrimaryKey }
          : attr
      );
      updateNode(id, {
        entity: { ...entity, attributes: updatedAttributes }
      });
    }
  }, [id, entity, updateNode]);

  const toggleForeignKey = useCallback((attrId: string) => {
    if (entity) {
      const updatedAttributes = entity.attributes.map(attr =>
        attr.id === attrId
          ? { ...attr, isForeignKey: !(attr as any).isForeignKey }
          : attr
      );
      updateNode(id, {
        entity: { ...entity, attributes: updatedAttributes }
      });
    }
  }, [id, entity, updateNode]);

  // ============================================================================
  // Existing: Nullable/Unique Toggles
  // ============================================================================
  
  const toggleNullable = useCallback((attrId: string) => {
    if (entity) {
      const updatedAttributes = entity.attributes.map(attr =>
        attr.id === attrId
          ? { ...attr, isNullable: !attr.isNullable }
          : attr
      );
      updateNode(id, {
        entity: { ...entity, attributes: updatedAttributes }
      });
    }
  }, [id, entity, updateNode]);

  const toggleUnique = useCallback((attrId: string) => {
    if (entity) {
      const updatedAttributes = entity.attributes.map(attr =>
        attr.id === attrId
          ? { ...attr, isUnique: !attr.isUnique }
          : attr
      );
      updateNode(id, {
        entity: { ...entity, attributes: updatedAttributes }
      });
    }
  }, [id, entity, updateNode]);

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
  // Render Attribute Row
  // ============================================================================
  
  const renderAttribute = (attr: ERAttribute) => {
    const isEditing = editingAttrId === attr.id;
    const attrWithKeys = attr as any; // Type cast for new properties

    return (
      <div
        key={attr.id}
        className={clsx(
          'px-4 py-2 flex items-center gap-2 group hover:bg-gray-50 transition-colors relative',
          attrWithKeys.isPrimaryKey && 'bg-yellow-50',
          attrWithKeys.isForeignKey && !attrWithKeys.isPrimaryKey && 'bg-blue-50'
        )}
      >
        {/* Primary Key Toggle */}
        <button
          onClick={() => togglePrimaryKey(attr.id)}
          className={clsx(
            'flex-shrink-0 transition-all',
            attrWithKeys.isPrimaryKey 
              ? 'opacity-100 text-yellow-600' 
              : 'opacity-20 hover:opacity-60 text-gray-400'
          )}
          title={attrWithKeys.isPrimaryKey ? 'Remove Primary Key' : 'Set as Primary Key'}
        >
          <Key className="w-4 h-4" />
        </button>

        {/* Foreign Key Toggle */}
        <button
          onClick={() => toggleForeignKey(attr.id)}
          className={clsx(
            'flex-shrink-0 transition-all',
            attrWithKeys.isForeignKey 
              ? 'opacity-100 text-blue-600' 
              : 'opacity-20 hover:opacity-60 text-gray-400'
          )}
          title={attrWithKeys.isForeignKey ? 'Remove Foreign Key' : 'Set as Foreign Key'}
        >
          <LinkIcon className="w-4 h-4" />
        </button>

        {isEditing ? (
          <>
            <input
              ref={attrNameInputRef}
              type="text"
              value={tempAttrName}
              onChange={(e) => setTempAttrName(e.target.value)}
              onKeyDown={handleAttrKeyDown}
              className="flex-1 px-2 py-1 text-sm border border-blue-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Attribute name"
            />
            <input
              type="text"
              value={tempAttrType}
              onChange={(e) => setTempAttrType(e.target.value)}
              onKeyDown={handleAttrKeyDown}
              className="w-32 px-2 py-1 text-sm border border-blue-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Type"
            />
            <button
              onClick={handleSaveAttribute}
              className="p-1 text-green-600 hover:bg-green-100 rounded transition-colors"
              title="Save"
            >
              <Check className="w-4 h-4" />
            </button>
            <button
              onClick={handleCancelEditAttribute}
              className="p-1 text-red-600 hover:bg-red-100 rounded transition-colors"
              title="Cancel"
            >
              <X className="w-4 h-4" />
            </button>
          </>
        ) : (
          <>
            <span className="flex-1 text-sm font-mono">
              {attr.name}
              <span className="text-gray-400 ml-2">{attr.type}</span>
            </span>

            {/* Nullable Indicator (Existing) */}
            <button
              onClick={() => toggleNullable(attr.id)}
              className={clsx(
                'flex-shrink-0 text-xs font-bold transition-all',
                attr.isNullable
                  ? 'opacity-20 hover:opacity-60 text-gray-400'
                  : 'opacity-100 text-red-500'
              )}
              title={attr.isNullable ? 'Set as NOT NULL' : 'Set as NULLABLE'}
            >
              {attr.isNullable ? 'N' : '*'}
            </button>
            
            {/* Unique Indicator (Existing) */}
            {attr.isUnique && (
              <span className="text-purple-500 text-xs font-bold">U</span>
            )}

            {/* Edit Button */}
            <button
              onClick={() => handleStartEditAttribute(attr)}
              className="opacity-0 group-hover:opacity-100 p-0.5 text-blue-600 hover:bg-blue-100 rounded transition-opacity"
              title="Edit attribute"
            >
              <Edit2 className="w-3 h-3" />
            </button>

            {/* Delete Button */}
            <button
              onClick={() => handleDeleteAttribute(attr.id)}
              className="opacity-0 group-hover:opacity-100 p-0.5 text-red-600 hover:bg-red-100 rounded transition-opacity"
              title="Delete attribute"
            >
              <X className="w-3 h-3" />
            </button>
          </>
        )}

        {/* Handle for attribute connections (Existing) */}
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

  // Safety check
  if (!entity) {
    return <div className="p-4 bg-red-100 text-red-800">Invalid entity data</div>;
  }

  // ============================================================================
  // Main Render
  // ============================================================================
  
  return (
    <div
      className={clsx(
        'relative transition-all duration-200',
        selected && 'ring-2 ring-blue-500 ring-offset-2 rounded'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{ zIndex }}
    >
      {/* Connection Handles - Top and Left */}
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

      {/* Main Entity Container - NEW: Support for weak entities (dotted border) */}
      <div className={clsx(
        'min-w-[280px] max-w-[400px] rounded shadow-md overflow-hidden',
        entity.isWeak 
          ? 'border-4 border-dashed border-blue-500' 
          : 'border-2 border-blue-500'
      )}
      style={{ backgroundColor: nodeColor }}
      >
        {/* Header */}
        <div 
          className={clsx(
            'px-4 py-3 flex items-center gap-2',
            entity.isWeak 
              ? 'bg-gradient-to-r from-blue-400 to-blue-500' 
              : 'bg-gradient-to-r from-blue-500 to-blue-600',
            'text-white'
          )}
        >
          <Database className="w-5 h-5 flex-shrink-0" />
          
          {editingEntityName ? (
            <>
              <input
                ref={entityNameInputRef}
                type="text"
                value={tempEntityName}
                onChange={(e) => setTempEntityName(e.target.value)}
                onKeyDown={handleEntityNameKeyDown}
                className="flex-1 px-2 py-1 text-sm bg-white text-gray-900 border border-blue-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleSaveEntityName}
                className="p-1 bg-white text-green-600 hover:bg-green-100 rounded transition-colors"
              >
                <Check className="w-4 h-4" />
              </button>
              <button
                onClick={handleCancelEditEntityName}
                className="p-1 bg-white text-red-600 hover:bg-red-100 rounded transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </>
          ) : (
            <>
              <h3 className="flex-1 font-semibold">{entity.name}</h3>
              <button
                onClick={handleStartEditEntityName}
                className="opacity-0 group-hover:opacity-100 p-1 bg-white bg-opacity-20 hover:bg-opacity-30 rounded transition-opacity"
              >
                <Edit2 className="w-4 h-4" />
              </button>
              {/* NEW: Color Picker Toggle */}
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

        {/* Attributes Section */}
        <div className="max-h-96 overflow-y-auto bg-white">
          {entity.attributes && entity.attributes.length > 0 ? (
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

      {/* Connection Handles - Right and Bottom */}
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
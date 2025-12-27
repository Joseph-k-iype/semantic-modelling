import { useState } from 'react';
import { useDiagramStore } from '../../../store/diagramStore';
import { X, Plus, Trash2, ChevronDown, ChevronRight } from 'lucide-react';
import clsx from 'clsx';
import { ERAttribute, ERNodeData, UMLAttribute, UMLMethod, UMLNodeData, BPMNNodeData } from '../../../types/diagram.types';

// Type guard functions
const isERNodeData = (data: any): data is ERNodeData => {
  return 'entity' in data && data.entity !== undefined;
};

const isUMLNodeData = (data: any): data is UMLNodeData => {
  return 'class' in data && data.class !== undefined;
};

const isBPMNNodeData = (data: any): data is BPMNNodeData => {
  return 'task' in data || 'event' in data || 'gateway' in data || 'pool' in data;
};

export const DiagramProperties: React.FC = () => {
  const { nodes, selectedNodeIds, updateNode, deleteNode } = useDiagramStore();
  const [activeTab, setActiveTab] = useState<'properties' | 'styles'>('properties');
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    general: true,
    attributes: true,
    methods: true,
  });

  const selectedNode = selectedNodeIds.length === 1 
    ? nodes.find(n => n.id === selectedNodeIds[0])
    : null;

  if (!selectedNode) {
    return (
      <div className="w-80 bg-white border-l border-gray-200 flex items-center justify-center text-gray-400">
        <div className="text-center p-8">
          <p className="text-sm">Select an element to view properties</p>
        </div>
      </div>
    );
  }

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // ER Entity specific handlers
  const handleEntityNameChange = (value: string) => {
    if (isERNodeData(selectedNode.data) && selectedNode.data.entity) {
      updateNode(selectedNode.id, {
        entity: { ...selectedNode.data.entity, name: value }
      });
    }
  };

  const addERAttribute = () => {
    if (isERNodeData(selectedNode.data) && selectedNode.data.entity) {
      const newAttribute: ERAttribute = {
        id: `attr_${Date.now()}`,
        name: 'newAttribute',
        type: 'VARCHAR(255)',
        isNullable: true,
      };
      
      updateNode(selectedNode.id, {
        entity: {
          ...selectedNode.data.entity,
          attributes: [...selectedNode.data.entity.attributes, newAttribute]
        }
      });
    }
  };

  const updateERAttribute = (attrId: string, updates: Partial<ERAttribute>) => {
    if (isERNodeData(selectedNode.data) && selectedNode.data.entity) {
      const updatedAttributes = selectedNode.data.entity.attributes.map(attr =>
        attr.id === attrId ? { ...attr, ...updates } : attr
      );
      
      updateNode(selectedNode.id, {
        entity: { ...selectedNode.data.entity, attributes: updatedAttributes }
      });
    }
  };

  const deleteERAttribute = (attrId: string) => {
    if (isERNodeData(selectedNode.data) && selectedNode.data.entity) {
      const updatedAttributes = selectedNode.data.entity.attributes.filter(
        attr => attr.id !== attrId
      );
      
      updateNode(selectedNode.id, {
        entity: { ...selectedNode.data.entity, attributes: updatedAttributes }
      });
    }
  };

  // UML Class specific handlers
  const handleClassNameChange = (value: string) => {
    if (isUMLNodeData(selectedNode.data) && selectedNode.data.class) {
      updateNode(selectedNode.id, {
        class: { ...selectedNode.data.class, name: value }
      });
    }
  };

  const addUMLAttribute = () => {
    if (isUMLNodeData(selectedNode.data) && selectedNode.data.class) {
      const newAttribute: UMLAttribute = {
        id: `attr_${Date.now()}`,
        name: 'newAttribute',
        type: 'String',
        visibility: 'private',
      };
      
      updateNode(selectedNode.id, {
        class: {
          ...selectedNode.data.class,
          attributes: [...selectedNode.data.class.attributes, newAttribute]
        }
      });
    }
  };

  const updateUMLAttribute = (attrId: string, updates: Partial<UMLAttribute>) => {
    if (isUMLNodeData(selectedNode.data) && selectedNode.data.class) {
      const updatedAttributes = selectedNode.data.class.attributes.map(attr =>
        attr.id === attrId ? { ...attr, ...updates } : attr
      );
      
      updateNode(selectedNode.id, {
        class: { ...selectedNode.data.class, attributes: updatedAttributes }
      });
    }
  };

  const deleteUMLAttribute = (attrId: string) => {
    if (isUMLNodeData(selectedNode.data) && selectedNode.data.class) {
      const updatedAttributes = selectedNode.data.class.attributes.filter(
        attr => attr.id !== attrId
      );
      
      updateNode(selectedNode.id, {
        class: { ...selectedNode.data.class, attributes: updatedAttributes }
      });
    }
  };

  const addUMLMethod = () => {
    if (isUMLNodeData(selectedNode.data) && selectedNode.data.class) {
      const newMethod: UMLMethod = {
        id: `method_${Date.now()}`,
        name: 'newMethod',
        returnType: 'void',
        parameters: [],
        visibility: 'public',
      };
      
      updateNode(selectedNode.id, {
        class: {
          ...selectedNode.data.class,
          methods: [...selectedNode.data.class.methods, newMethod]
        }
      });
    }
  };

  const updateUMLMethod = (methodId: string, updates: Partial<UMLMethod>) => {
    if (isUMLNodeData(selectedNode.data) && selectedNode.data.class) {
      const updatedMethods = selectedNode.data.class.methods.map(method =>
        method.id === methodId ? { ...method, ...updates } : method
      );
      
      updateNode(selectedNode.id, {
        class: { ...selectedNode.data.class, methods: updatedMethods }
      });
    }
  };

  const deleteUMLMethod = (methodId: string) => {
    if (isUMLNodeData(selectedNode.data) && selectedNode.data.class) {
      const updatedMethods = selectedNode.data.class.methods.filter(
        method => method.id !== methodId
      );
      
      updateNode(selectedNode.id, {
        class: { ...selectedNode.data.class, methods: updatedMethods }
      });
    }
  };

  return (
    <div className="w-80 bg-white border-l border-gray-200 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between bg-gray-50">
        <h3 className="font-semibold text-gray-800">Properties</h3>
        <button
          onClick={() => deleteNode(selectedNode.id)}
          className="p-1 hover:bg-red-100 rounded text-red-600 transition-colors"
          title="Delete element"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('properties')}
          className={clsx(
            'flex-1 px-4 py-2 text-sm font-medium transition-colors',
            activeTab === 'properties'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
              : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
          )}
        >
          Properties
        </button>
        <button
          onClick={() => setActiveTab('styles')}
          className={clsx(
            'flex-1 px-4 py-2 text-sm font-medium transition-colors',
            activeTab === 'styles'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
              : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
          )}
        >
          Styles
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'properties' && (
          <div className="p-4 space-y-4">
            {/* General Section */}
            <div className="border border-gray-200 rounded">
              <button
                onClick={() => toggleSection('general')}
                className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors"
              >
                <span className="font-medium text-sm text-gray-700">General</span>
                {expandedSections.general ? (
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-gray-500" />
                )}
              </button>
              
              {expandedSections.general && (
                <div className="p-3 space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Type
                    </label>
                    <input
                      type="text"
                      value={selectedNode.type || ''}
                      disabled
                      className="w-full px-3 py-2 text-sm border border-gray-300 rounded bg-gray-50 text-gray-600"
                    />
                  </div>

                  {isERNodeData(selectedNode.data) && selectedNode.data.entity && (
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Entity Name
                      </label>
                      <input
                        type="text"
                        value={selectedNode.data.entity.name}
                        onChange={(e) => handleEntityNameChange(e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  )}

                  {isUMLNodeData(selectedNode.data) && selectedNode.data.class && (
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Class Name
                      </label>
                      <input
                        type="text"
                        value={selectedNode.data.class.name}
                        onChange={(e) => handleClassNameChange(e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  )}

                  {(() => {
                    if (!isBPMNNodeData(selectedNode.data)) return null;
                    const bpmnData = selectedNode.data;
                    if (!bpmnData.task) return null;
                    const task = bpmnData.task;
                    
                    return (
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Task Name
                        </label>
                        <input
                          type="text"
                          value={task.name}
                          onChange={(e) => {
                            updateNode(selectedNode.id, {
                              task: { ...task, name: e.target.value }
                            });
                          }}
                          className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    );
                  })()}
                </div>
              )}
            </div>

            {/* ER Attributes Section */}
            {isERNodeData(selectedNode.data) && selectedNode.data.entity && (
              <div className="border border-gray-200 rounded">
                <button
                  onClick={() => toggleSection('attributes')}
                  className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors"
                >
                  <span className="font-medium text-sm text-gray-700">Attributes</span>
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                </button>
                
                <div className="p-3 space-y-2">
                  {selectedNode.data.entity.attributes.map((attr: ERAttribute) => (
                    <div key={attr.id} className="flex items-center gap-2 p-2 bg-gray-50 rounded border border-gray-200">
                      <input
                        type="text"
                        value={attr.name}
                        onChange={(e) => updateERAttribute(attr.id, { name: e.target.value })}
                        className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                        placeholder="Attribute name"
                      />
                      <button
                        onClick={() => deleteERAttribute(attr.id)}
                        className="p-1 text-red-600 hover:bg-red-100 rounded transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                  
                  <button
                    onClick={addERAttribute}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors border border-dashed border-blue-300"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Add Attribute</span>
                  </button>
                </div>
              </div>
            )}

            {/* UML Attributes Section */}
            {isUMLNodeData(selectedNode.data) && selectedNode.data.class && (
              <>
                <div className="border border-gray-200 rounded">
                  <button
                    onClick={() => toggleSection('attributes')}
                    className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    <span className="font-medium text-sm text-gray-700">Attributes</span>
                    <ChevronDown className="w-4 h-4 text-gray-500" />
                  </button>
                  
                  <div className="p-3 space-y-2">
                    {selectedNode.data.class.attributes.map((attr: UMLAttribute) => (
                      <div key={attr.id} className="space-y-2 p-2 bg-gray-50 rounded border border-gray-200">
                        <div className="flex items-center gap-2">
                          <select
                            value={attr.visibility}
                            onChange={(e) => updateUMLAttribute(attr.id, { visibility: e.target.value as any })}
                            className="px-2 py-1 text-sm border border-gray-300 rounded"
                          >
                            <option value="public">+</option>
                            <option value="private">-</option>
                            <option value="protected">#</option>
                            <option value="package">~</option>
                          </select>
                          <input
                            type="text"
                            value={attr.name}
                            onChange={(e) => updateUMLAttribute(attr.id, { name: e.target.value })}
                            className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                            placeholder="name"
                          />
                          <input
                            type="text"
                            value={attr.type}
                            onChange={(e) => updateUMLAttribute(attr.id, { type: e.target.value })}
                            className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                            placeholder="type"
                          />
                          <button
                            onClick={() => deleteUMLAttribute(attr.id)}
                            className="p-1 text-red-600 hover:bg-red-100 rounded transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                    
                    <button
                      onClick={addUMLAttribute}
                      className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors border border-dashed border-blue-300"
                    >
                      <Plus className="w-4 h-4" />
                      <span>Add Attribute</span>
                    </button>
                  </div>
                </div>

                {/* Methods Section */}
                <div className="border border-gray-200 rounded">
                  <button
                    onClick={() => toggleSection('methods')}
                    className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    <span className="font-medium text-sm text-gray-700">Methods</span>
                    <ChevronDown className="w-4 h-4 text-gray-500" />
                  </button>
                  
                  <div className="p-3 space-y-2">
                    {selectedNode.data.class.methods.map((method: UMLMethod) => (
                      <div key={method.id} className="space-y-2 p-2 bg-gray-50 rounded border border-gray-200">
                        <div className="flex items-center gap-2">
                          <select
                            value={method.visibility}
                            onChange={(e) => updateUMLMethod(method.id, { visibility: e.target.value as any })}
                            className="px-2 py-1 text-sm border border-gray-300 rounded"
                          >
                            <option value="public">+</option>
                            <option value="private">-</option>
                            <option value="protected">#</option>
                            <option value="package">~</option>
                          </select>
                          <input
                            type="text"
                            value={method.name}
                            onChange={(e) => updateUMLMethod(method.id, { name: e.target.value })}
                            className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                            placeholder="method name"
                          />
                          <button
                            onClick={() => deleteUMLMethod(method.id)}
                            className="p-1 text-red-600 hover:bg-red-100 rounded transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                    
                    <button
                      onClick={addUMLMethod}
                      className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors border border-dashed border-blue-300"
                    >
                      <Plus className="w-4 h-4" />
                      <span>Add Method</span>
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === 'styles' && (
          <div className="p-4 space-y-4">
            <div className="text-sm text-gray-500 text-center py-8">
              Style options coming soon...
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
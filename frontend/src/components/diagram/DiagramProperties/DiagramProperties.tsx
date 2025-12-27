import React, { useState } from 'react';
import { useDiagramStore } from '../../../store/diagramStore';
import { X, Plus, Trash2, ChevronDown, ChevronRight } from 'lucide-react';
import clsx from 'clsx';
import { ERAttribute, UMLAttribute, UMLMethod } from '../../../types/diagram.types';

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

  const handleLabelChange = (value: string) => {
    updateNode(selectedNode.id, { label: value });
  };

  // ER Entity specific handlers
  const handleEntityNameChange = (value: string) => {
    if (selectedNode.data.entity) {
      updateNode(selectedNode.id, {
        entity: { ...selectedNode.data.entity, name: value }
      });
    }
  };

  const addERAttribute = () => {
    if (selectedNode.data.entity) {
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
    if (selectedNode.data.entity) {
      const updatedAttributes = selectedNode.data.entity.attributes.map(attr =>
        attr.id === attrId ? { ...attr, ...updates } : attr
      );
      
      updateNode(selectedNode.id, {
        entity: { ...selectedNode.data.entity, attributes: updatedAttributes }
      });
    }
  };

  const deleteERAttribute = (attrId: string) => {
    if (selectedNode.data.entity) {
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
    if (selectedNode.data.class) {
      updateNode(selectedNode.id, {
        class: { ...selectedNode.data.class, name: value }
      });
    }
  };

  const addUMLAttribute = () => {
    if (selectedNode.data.class) {
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
    if (selectedNode.data.class) {
      const updatedAttributes = selectedNode.data.class.attributes.map(attr =>
        attr.id === attrId ? { ...attr, ...updates } : attr
      );
      
      updateNode(selectedNode.id, {
        class: { ...selectedNode.data.class, attributes: updatedAttributes }
      });
    }
  };

  const deleteUMLAttribute = (attrId: string) => {
    if (selectedNode.data.class) {
      const updatedAttributes = selectedNode.data.class.attributes.filter(
        attr => attr.id !== attrId
      );
      
      updateNode(selectedNode.id, {
        class: { ...selectedNode.data.class, attributes: updatedAttributes }
      });
    }
  };

  const addUMLMethod = () => {
    if (selectedNode.data.class) {
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
    if (selectedNode.data.class) {
      const updatedMethods = selectedNode.data.class.methods.map(method =>
        method.id === methodId ? { ...method, ...updates } : method
      );
      
      updateNode(selectedNode.id, {
        class: { ...selectedNode.data.class, methods: updatedMethods }
      });
    }
  };

  const deleteUMLMethod = (methodId: string) => {
    if (selectedNode.data.class) {
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
      <div className="bg-gray-50 border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <h3 className="font-semibold text-gray-800">Properties</h3>
        <button
          onClick={() => deleteNode(selectedNode.id)}
          className="text-gray-400 hover:text-red-600 transition-colors"
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
              ? 'bg-white text-blue-600 border-b-2 border-blue-600'
              : 'bg-gray-50 text-gray-600 hover:text-gray-800'
          )}
        >
          Properties
        </button>
        <button
          onClick={() => setActiveTab('styles')}
          className={clsx(
            'flex-1 px-4 py-2 text-sm font-medium transition-colors',
            activeTab === 'styles'
              ? 'bg-white text-blue-600 border-b-2 border-blue-600'
              : 'bg-gray-50 text-gray-600 hover:text-gray-800'
          )}
        >
          Styles
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'properties' && (
          <>
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

                  {selectedNode.data.entity && (
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

                  {selectedNode.data.class && (
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

                  {selectedNode.data.task && (
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Task Name
                      </label>
                      <input
                        type="text"
                        value={selectedNode.data.task.name}
                        onChange={(e) => updateNode(selectedNode.id, {
                          task: { ...selectedNode.data.task, name: e.target.value }
                        })}
                        className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* ER Attributes Section */}
            {selectedNode.data.entity && (
              <div className="border border-gray-200 rounded">
                <button
                  onClick={() => toggleSection('attributes')}
                  className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors"
                >
                  <span className="font-medium text-sm text-gray-700">Attributes</span>
                  {expandedSections.attributes ? (
                    <ChevronDown className="w-4 h-4 text-gray-500" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-500" />
                  )}
                </button>
                
                {expandedSections.attributes && (
                  <div className="p-3 space-y-2">
                    {selectedNode.data.entity.attributes.map((attr) => (
                      <div key={attr.id} className="border border-gray-200 rounded p-2 space-y-2">
                        <div className="flex items-center gap-2">
                          <input
                            type="text"
                            value={attr.name}
                            onChange={(e) => updateERAttribute(attr.id, { name: e.target.value })}
                            className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                            placeholder="Attribute name"
                          />
                          <button
                            onClick={() => deleteERAttribute(attr.id)}
                            className="text-red-500 hover:text-red-700"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                        
                        <input
                          type="text"
                          value={attr.type}
                          onChange={(e) => updateERAttribute(attr.id, { type: e.target.value })}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                          placeholder="Type"
                        />

                        <div className="flex gap-4 text-xs">
                          <label className="flex items-center gap-1">
                            <input
                              type="checkbox"
                              checked={attr.isPrimary || false}
                              onChange={(e) => updateERAttribute(attr.id, { isPrimary: e.target.checked })}
                            />
                            Primary Key
                          </label>
                          <label className="flex items-center gap-1">
                            <input
                              type="checkbox"
                              checked={!attr.isNullable}
                              onChange={(e) => updateERAttribute(attr.id, { isNullable: !e.target.checked })}
                            />
                            Required
                          </label>
                        </div>
                      </div>
                    ))}
                    
                    <button
                      onClick={addERAttribute}
                      className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-blue-600 border border-blue-300 rounded hover:bg-blue-50 transition-colors"
                    >
                      <Plus className="w-4 h-4" />
                      Add Attribute
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* UML Attributes and Methods Sections */}
            {selectedNode.data.class && (
              <>
                <div className="border border-gray-200 rounded">
                  <button
                    onClick={() => toggleSection('attributes')}
                    className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    <span className="font-medium text-sm text-gray-700">Attributes</span>
                    {expandedSections.attributes ? (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-500" />
                    )}
                  </button>
                  
                  {expandedSections.attributes && (
                    <div className="p-3 space-y-2">
                      {selectedNode.data.class.attributes.map((attr) => (
                        <div key={attr.id} className="border border-gray-200 rounded p-2 space-y-2">
                          <div className="flex items-center gap-2">
                            <select
                              value={attr.visibility}
                              onChange={(e) => updateUMLAttribute(attr.id, { 
                                visibility: e.target.value as any 
                              })}
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
                            <button
                              onClick={() => deleteUMLAttribute(attr.id)}
                              className="text-red-500 hover:text-red-700"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                          
                          <input
                            type="text"
                            value={attr.type}
                            onChange={(e) => updateUMLAttribute(attr.id, { type: e.target.value })}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                            placeholder="Type"
                          />
                        </div>
                      ))}
                      
                      <button
                        onClick={addUMLAttribute}
                        className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-blue-600 border border-blue-300 rounded hover:bg-blue-50 transition-colors"
                      >
                        <Plus className="w-4 h-4" />
                        Add Attribute
                      </button>
                    </div>
                  )}
                </div>

                <div className="border border-gray-200 rounded">
                  <button
                    onClick={() => toggleSection('methods')}
                    className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    <span className="font-medium text-sm text-gray-700">Methods</span>
                    {expandedSections.methods ? (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-500" />
                    )}
                  </button>
                  
                  {expandedSections.methods && (
                    <div className="p-3 space-y-2">
                      {selectedNode.data.class.methods.map((method) => (
                        <div key={method.id} className="border border-gray-200 rounded p-2 space-y-2">
                          <div className="flex items-center gap-2">
                            <select
                              value={method.visibility}
                              onChange={(e) => updateUMLMethod(method.id, { 
                                visibility: e.target.value as any 
                              })}
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
                              placeholder="methodName"
                            />
                            <button
                              onClick={() => deleteUMLMethod(method.id)}
                              className="text-red-500 hover:text-red-700"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                          
                          <input
                            type="text"
                            value={method.returnType}
                            onChange={(e) => updateUMLMethod(method.id, { returnType: e.target.value })}
                            className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                            placeholder="Return type"
                          />
                        </div>
                      ))}
                      
                      <button
                        onClick={addUMLMethod}
                        className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-blue-600 border border-blue-300 rounded hover:bg-blue-50 transition-colors"
                      >
                        <Plus className="w-4 h-4" />
                        Add Method
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}
          </>
        )}

        {activeTab === 'styles' && (
          <div className="text-sm text-gray-500">
            Styling options coming soon...
          </div>
        )}
      </div>
    </div>
  );
};
// frontend/src/pages/DiagramEditorPage/DiagramEditorPage.tsx

import React from 'react';
import { useParams } from 'react-router-dom';

const DiagramEditorPage: React.FC = () => {
  const { diagramId } = useParams<{ diagramId: string }>();

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-lg font-semibold text-gray-900">
            Diagram Editor
          </h1>
          <span className="text-sm text-gray-500">ID: {diagramId}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <button className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
            Save
          </button>
          <button className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
            Publish
          </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <aside className="w-16 bg-white border-r border-gray-200 flex flex-col items-center py-4 space-y-4">
          <button className="w-10 h-10 flex items-center justify-center text-gray-600 hover:bg-gray-100 rounded-md">
            <span>🔲</span>
          </button>
          <button className="w-10 h-10 flex items-center justify-center text-gray-600 hover:bg-gray-100 rounded-md">
            <span>⚡</span>
          </button>
          <button className="w-10 h-10 flex items-center justify-center text-gray-600 hover:bg-gray-100 rounded-md">
            <span>📝</span>
          </button>
        </aside>

        <main className="flex-1 bg-white overflow-hidden">
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">🎨</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Diagram Canvas
              </h3>
              <p className="text-gray-600">
                Start creating your diagram here
              </p>
            </div>
          </div>
        </main>

        <aside className="w-80 bg-white border-l border-gray-200 overflow-y-auto">
          <div className="p-4">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">
              Properties
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Diagram Type
                </label>
                <select className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option>ER Diagram</option>
                  <option>UML Class</option>
                  <option>UML Sequence</option>
                  <option>BPMN Process</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Layout
                </label>
                <select className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option>Manual</option>
                  <option>Layered</option>
                  <option>Force-Directed</option>
                  <option>Hierarchical</option>
                </select>
              </div>

              <div>
                <label className="flex items-center">
                  <input type="checkbox" className="mr-2" />
                  <span className="text-sm text-gray-700">Show Grid</span>
                </label>
              </div>

              <div>
                <label className="flex items-center">
                  <input type="checkbox" className="mr-2" />
                  <span className="text-sm text-gray-700">Snap to Grid</span>
                </label>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default DiagramEditorPage;
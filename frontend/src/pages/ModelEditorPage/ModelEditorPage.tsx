// frontend/src/pages/ModelEditorPage/ModelEditorPage.tsx

import React from 'react';

const ModelEditorPage: React.FC = () => {
  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-semibold text-gray-900">Model Editor</h1>
      </header>
      
      <div className="flex-1 flex overflow-hidden">
        <aside className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Model Structure</h2>
            <p className="text-sm text-gray-500">Model tree will appear here</p>
          </div>
        </aside>
        
        <main className="flex-1 overflow-hidden">
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Model Editor</h3>
              <p className="text-gray-600">Select or create a model to begin editing</p>
            </div>
          </div>
        </main>
        
        <aside className="w-80 bg-white border-l border-gray-200 overflow-y-auto">
          <div className="p-4">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Properties</h2>
            <p className="text-sm text-gray-500">Properties will appear here</p>
          </div>
        </aside>
      </div>
    </div>
  );
};

// DEFAULT EXPORT - This fixes the import error
export default ModelEditorPage;
// frontend/src/pages/WorkspacePage/WorkspacePage.tsx

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const WorkspacePage: React.FC = () => {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const navigate = useNavigate();

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">
              Workspace {workspaceId}
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Manage your models and diagrams
            </p>
          </div>
          <button
            onClick={() => navigate('/model/new')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
          >
            Create Model
          </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <aside className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Folders
            </h2>
            <nav className="space-y-1">
              <a
                href="#"
                className="flex items-center px-3 py-2 text-sm font-medium text-gray-900 rounded-md bg-gray-100"
              >
                📁 All Models
              </a>
              <a
                href="#"
                className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-100"
              >
                📁 ER Models
              </a>
              <a
                href="#"
                className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-100"
              >
                📁 UML Diagrams
              </a>
              <a
                href="#"
                className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-100"
              >
                📁 BPMN Processes
              </a>
            </nav>
          </div>
        </aside>

        <main className="flex-1 overflow-y-auto p-6">
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Recent Models
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-900">
                    Sample ER Model
                  </h3>
                  <span className="text-xs text-gray-500">ER</span>
                </div>
                <p className="text-xs text-gray-600 mb-3">
                  Created 2 days ago
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">3 diagrams</span>
                  <button
                    onClick={() => navigate('/model/sample-1')}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Open →
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Shared with Me
            </h2>
            <p className="text-sm text-gray-600">
              No models shared with you yet
            </p>
          </div>
        </main>
      </div>
    </div>
  );
};

export default WorkspacePage;
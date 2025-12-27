import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FolderOpen, Plus, Database, Package, Workflow } from 'lucide-react';

export const WorkspacePage: React.FC = () => {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const navigate = useNavigate();

  // TODO: Fetch workspace data from API
  const diagrams = [
    {
      id: '1',
      name: 'User Management ER',
      type: 'ER',
      updatedAt: '2024-01-15',
    },
    {
      id: '2',
      name: 'System Architecture',
      type: 'UML_CLASS',
      updatedAt: '2024-01-14',
    },
    {
      id: '3',
      name: 'Order Process',
      type: 'BPMN',
      updatedAt: '2024-01-13',
    },
  ];

  const getIcon = (type: string) => {
    if (type === 'ER') return <Database className="w-5 h-5 text-blue-600" />;
    if (type.startsWith('UML')) return <Package className="w-5 h-5 text-purple-600" />;
    if (type === 'BPMN') return <Workflow className="w-5 h-5 text-green-600" />;
    return <FolderOpen className="w-5 h-5 text-gray-600" />;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">My Workspace</h1>
              <p className="text-sm text-gray-600 mt-1">
                Workspace ID: {workspaceId}
              </p>
            </div>
            <button
              onClick={() => navigate('/diagram')}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              New Diagram
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Diagrams Grid */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Diagrams</h2>
          
          {diagrams.length === 0 ? (
            <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
              <FolderOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No diagrams yet</h3>
              <p className="text-gray-600 mb-4">
                Create your first diagram to get started
              </p>
              <button
                onClick={() => navigate('/diagram')}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-5 h-5" />
                Create Diagram
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {diagrams.map((diagram) => (
                <div
                  key={diagram.id}
                  onClick={() => navigate(`/diagram/${diagram.id}`)}
                  className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer group"
                >
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-gray-50 rounded-lg group-hover:bg-blue-50 transition-colors">
                      {getIcon(diagram.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-gray-900 mb-1 truncate">
                        {diagram.name}
                      </h3>
                      <p className="text-sm text-gray-600 mb-2">
                        {diagram.type.replace('_', ' ')}
                      </p>
                      <p className="text-xs text-gray-500">
                        Updated {diagram.updatedAt}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Start</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => navigate('/diagram')}
              className="flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
            >
              <Database className="w-8 h-8 text-blue-600" />
              <div>
                <div className="font-semibold text-gray-900">ER Diagram</div>
                <div className="text-sm text-gray-600">Database design</div>
              </div>
            </button>

            <button
              onClick={() => navigate('/diagram')}
              className="flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors text-left"
            >
              <Package className="w-8 h-8 text-purple-600" />
              <div>
                <div className="font-semibold text-gray-900">UML Class</div>
                <div className="text-sm text-gray-600">Object models</div>
              </div>
            </button>

            <button
              onClick={() => navigate('/diagram')}
              className="flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors text-left"
            >
              <Workflow className="w-8 h-8 text-green-600" />
              <div>
                <div className="font-semibold text-gray-900">BPMN Process</div>
                <div className="text-sm text-gray-600">Business flows</div>
              </div>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};
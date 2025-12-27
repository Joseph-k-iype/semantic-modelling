// frontend/src/pages/HomePage/HomePage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Database, Package, Activity, Plus, Folder, Users } from 'lucide-react';
import clsx from 'clsx';

interface DiagramType {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  features: string[];
}

const DIAGRAM_TYPES: DiagramType[] = [
  {
    id: 'ER',
    name: 'ER Diagram',
    description: 'Entity-Relationship modeling for databases',
    icon: <Database className="w-12 h-12" />,
    color: 'blue',
    features: [
      'Database schema design',
      'Entity and attribute modeling',
      'Relationship cardinality',
      'SQL export'
    ]
  },
  {
    id: 'UML_CLASS',
    name: 'UML Class Diagram',
    description: 'Object-oriented design and architecture',
    icon: <Package className="w-12 h-12" />,
    color: 'purple',
    features: [
      'Class hierarchy design',
      'Attributes and methods',
      'Inheritance and interfaces',
      'Code generation'
    ]
  },
  {
    id: 'BPMN',
    name: 'BPMN Process',
    description: 'Business process modeling and workflow',
    icon: <Activity className="w-12 h-12" />,
    color: 'green',
    features: [
      'Process flows and tasks',
      'Events and gateways',
      'Swimlanes and pools',
      'Process automation'
    ]
  }
];

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [modelName, setModelName] = useState('');
  const [workspaceName, setWorkspaceName] = useState('My Workspace');

  const handleCreateDiagram = () => {
    if (!selectedType || !modelName) return;

    // Navigate to diagram editor with type and model name
    navigate(`/diagram/new?type=${selectedType}&name=${encodeURIComponent(modelName)}`);
  };

  const getColorClasses = (color: string, selected: boolean) => {
    const colors = {
      blue: {
        border: selected ? 'border-blue-500' : 'border-blue-200',
        bg: 'bg-blue-50',
        hover: 'hover:border-blue-400',
        text: 'text-blue-600',
        button: 'bg-blue-600 hover:bg-blue-700'
      },
      purple: {
        border: selected ? 'border-purple-500' : 'border-purple-200',
        bg: 'bg-purple-50',
        hover: 'hover:border-purple-400',
        text: 'text-purple-600',
        button: 'bg-purple-600 hover:bg-purple-700'
      },
      green: {
        border: selected ? 'border-green-500' : 'border-green-200',
        bg: 'bg-green-50',
        hover: 'hover:border-green-400',
        text: 'text-green-600',
        button: 'bg-green-600 hover:bg-green-700'
      }
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Enterprise Modeling Platform</h1>
              <p className="text-sm text-gray-500 mt-1">Create professional diagrams with semantic modeling</p>
            </div>
            <div className="flex items-center gap-3">
              <button className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                <Users className="w-4 h-4" />
                Workspaces
              </button>
              <button className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
                <Folder className="w-4 h-4" />
                My Models
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {!showCreateDialog ? (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900">Choose Your Diagram Type</h2>
              <p className="mt-2 text-lg text-gray-600">
                Select a modeling notation to get started
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {DIAGRAM_TYPES.map((type) => {
                const isSelected = selectedType === type.id;
                const colors = getColorClasses(type.color, isSelected);

                return (
                  <div
                    key={type.id}
                    onClick={() => setSelectedType(type.id)}
                    className={clsx(
                      'relative cursor-pointer rounded-xl border-2 p-6 transition-all duration-200',
                      colors.border,
                      colors.bg,
                      colors.hover,
                      isSelected && 'ring-4 ring-opacity-50',
                      isSelected && `ring-${type.color}-200`,
                      'hover:shadow-lg'
                    )}
                  >
                    {isSelected && (
                      <div className="absolute top-4 right-4 w-6 h-6 bg-white rounded-full flex items-center justify-center shadow-md">
                        <div className={clsx('w-4 h-4 rounded-full', colors.button.split(' ')[0])} />
                      </div>
                    )}

                    <div className={clsx('mb-4', colors.text)}>
                      {type.icon}
                    </div>

                    <h3 className="text-xl font-bold text-gray-900 mb-2">{type.name}</h3>
                    <p className="text-sm text-gray-600 mb-4">{type.description}</p>

                    <div className="space-y-2">
                      <p className="text-xs font-semibold text-gray-700 uppercase">Features:</p>
                      <ul className="space-y-1">
                        {type.features.map((feature, idx) => (
                          <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                            <span className={clsx('mt-1 w-1.5 h-1.5 rounded-full flex-shrink-0', colors.button.split(' ')[0])} />
                            {feature}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                );
              })}
            </div>

            {selectedType && (
              <div className="flex justify-center">
                <button
                  onClick={() => setShowCreateDialog(true)}
                  className="flex items-center gap-2 px-8 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl"
                >
                  <Plus className="w-5 h-5" />
                  Create {DIAGRAM_TYPES.find(t => t.id === selectedType)?.name}
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Create New Diagram</h2>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Diagram Type
                  </label>
                  <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
                    {DIAGRAM_TYPES.find(t => t.id === selectedType)?.icon}
                    <div>
                      <div className="font-semibold text-gray-900">
                        {DIAGRAM_TYPES.find(t => t.id === selectedType)?.name}
                      </div>
                      <div className="text-sm text-gray-600">
                        {DIAGRAM_TYPES.find(t => t.id === selectedType)?.description}
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <label htmlFor="workspace" className="block text-sm font-medium text-gray-700 mb-2">
                    Workspace
                  </label>
                  <input
                    id="workspace"
                    type="text"
                    value={workspaceName}
                    onChange={(e) => setWorkspaceName(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter workspace name"
                  />
                </div>

                <div>
                  <label htmlFor="modelName" className="block text-sm font-medium text-gray-700 mb-2">
                    Model Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="modelName"
                    type="text"
                    value={modelName}
                    onChange={(e) => setModelName(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., Customer Database Schema"
                    autoFocus
                  />
                  <p className="mt-1 text-sm text-gray-500">
                    Give your diagram a descriptive name
                  </p>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => setShowCreateDialog(false)}
                    className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleCreateDiagram}
                    disabled={!modelName.trim()}
                    className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Create Diagram
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-auto py-8 border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            Enterprise Modeling Platform • Open Source • Built with React & FastAPI
          </p>
        </div>
      </footer>
    </div>
  );
};
// frontend/src/pages/HomePage/HomePage.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Database, Package, Activity, Folder, Users, LogIn } from 'lucide-react';
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
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Check authentication status
  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('access_token');
      setIsAuthenticated(!!token);
      setIsCheckingAuth(false);
    };

    checkAuth();
  }, []);

  const handleCreateDiagram = () => {
    // Check authentication before allowing diagram creation
    if (!isAuthenticated) {
      // Save the intended action and redirect to login
      sessionStorage.setItem('intended_action', JSON.stringify({
        type: 'create_diagram',
        diagramType: selectedType,
        modelName: modelName
      }));
      navigate('/login');
      return;
    }

    if (!selectedType || !modelName) return;

    // Navigate to diagram editor with type and model name
    navigate(`/diagram/new?type=${selectedType}&name=${encodeURIComponent(modelName)}`);
  };

  const handleLogin = () => {
    navigate('/login');
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

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Database className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Enterprise Modeling Platform
                </h1>
                <p className="text-sm text-gray-500">
                  Open-source alternative to Visual Paradigm
                </p>
              </div>
            </div>
            
            {!isAuthenticated && (
              <button
                onClick={handleLogin}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <LogIn className="w-4 h-4" />
                Sign In
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Authentication Warning Banner */}
      {!isAuthenticated && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm text-yellow-700">
                  <strong className="font-semibold">Authentication Required:</strong> Please sign in to create and save diagrams. Your work will be securely stored and synced across devices.
                </p>
              </div>
              <button
                onClick={handleLogin}
                className="flex-shrink-0 px-4 py-2 bg-yellow-400 text-yellow-900 rounded-lg hover:bg-yellow-500 transition-colors font-medium text-sm"
              >
                Sign In Now
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Create Professional Diagrams
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Build ER diagrams, UML models, and BPMN processes with our powerful, web-based modeling platform
          </p>
        </div>

        {/* Diagram Type Selection */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {DIAGRAM_TYPES.map((type) => {
            const colors = getColorClasses(type.color, selectedType === type.id);
            
            return (
              <button
                key={type.id}
                onClick={() => {
                  setSelectedType(type.id);
                  setShowCreateDialog(true);
                }}
                className={clsx(
                  'p-6 bg-white rounded-lg border-2 transition-all duration-200 text-left',
                  colors.border,
                  colors.hover,
                  selectedType === type.id && 'shadow-lg transform scale-105'
                )}
              >
                <div className={clsx('mb-4', colors.text)}>
                  {type.icon}
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  {type.name}
                </h3>
                <p className="text-gray-600 mb-4">
                  {type.description}
                </p>
                <ul className="space-y-1">
                  {type.features.map((feature, idx) => (
                    <li key={idx} className="text-sm text-gray-500 flex items-center gap-2">
                      <span className={clsx('w-1.5 h-1.5 rounded-full', `bg-${type.color}-500`)}></span>
                      {feature}
                    </li>
                  ))}
                </ul>
              </button>
            );
          })}
        </div>

        {/* Create Dialog */}
        {showCreateDialog && selectedType && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                Create New {DIAGRAM_TYPES.find(t => t.id === selectedType)?.name}
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Workspace
                  </label>
                  <input
                    type="text"
                    value={workspaceName}
                    onChange={(e) => setWorkspaceName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="My Workspace"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Model Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={modelName}
                    onChange={(e) => setModelName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter model name"
                    autoFocus
                  />
                </div>

                {!isAuthenticated && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    <p className="text-sm text-yellow-800">
                      <strong>Note:</strong> You need to sign in to create and save diagrams.
                    </p>
                  </div>
                )}
              </div>
              
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => {
                    setShowCreateDialog(false);
                    setModelName('');
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateDiagram}
                  disabled={!modelName.trim()}
                  className={clsx(
                    'flex-1 px-4 py-2 rounded text-white transition-colors',
                    modelName.trim()
                      ? getColorClasses(DIAGRAM_TYPES.find(t => t.id === selectedType)?.color || 'blue', false).button
                      : 'bg-gray-300 cursor-not-allowed'
                  )}
                >
                  {isAuthenticated ? 'Create' : 'Sign In to Create'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Database className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Graph-Native Storage
            </h3>
            <p className="text-gray-600">
              Semantic models stored in FalkorDB for powerful lineage and impact analysis
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Users className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Real-time Collaboration
            </h3>
            <p className="text-gray-600">
              Work together with your team in real-time with presence indicators
            </p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Folder className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Enterprise Governance
            </h3>
            <p className="text-gray-600">
              Publishing workflows, versioning, and audit trails for enterprise use
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};
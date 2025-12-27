import { useState } from 'react';
import { 
  Database, 
  Package, 
  Circle, 
  Square, 
  Diamond, 
  Layers,
  ChevronRight,
  ChevronDown,
  User,
  Settings,
  FileText,
  Code,
  Play,
  GitBranch,
  Workflow
} from 'lucide-react';
import { DiagramType } from '../../../types/diagram.types';
import { useDiagramStore } from '../../../store/diagramStore';

interface PaletteItem {
  type: string;
  label: string;
  icon: React.ReactNode;
  description?: string;
}

interface PaletteSection {
  title: string;
  items: PaletteItem[];
}

const erPalette: PaletteSection[] = [
  {
    title: 'Entities',
    items: [
      { type: 'ER_ENTITY', label: 'Entity', icon: <Database className="w-5 h-5" />, description: 'Database entity' },
      { type: 'ER_WEAK_ENTITY', label: 'Weak Entity', icon: <Database className="w-5 h-5" />, description: 'Dependent entity' },
    ],
  },
  {
    title: 'Attributes',
    items: [
      { type: 'ER_ATTRIBUTE', label: 'Attribute', icon: <Circle className="w-5 h-5" />, description: 'Entity attribute' },
      { type: 'ER_KEY_ATTRIBUTE', label: 'Key Attribute', icon: <Circle className="w-5 h-5" />, description: 'Primary key' },
    ],
  },
];

const umlPalette: PaletteSection[] = [
  {
    title: 'Classes',
    items: [
      { type: 'UML_CLASS', label: 'Class', icon: <Package className="w-5 h-5" />, description: 'Standard class' },
      { type: 'UML_ABSTRACT_CLASS', label: 'Abstract Class', icon: <Package className="w-5 h-5" />, description: 'Abstract class' },
      { type: 'UML_INTERFACE', label: 'Interface', icon: <Package className="w-5 h-5" />, description: 'Interface definition' },
    ],
  },
  {
    title: 'Components',
    items: [
      { type: 'UML_COMPONENT', label: 'Component', icon: <Layers className="w-5 h-5" />, description: 'System component' },
      { type: 'UML_PACKAGE', label: 'Package', icon: <Package className="w-5 h-5" />, description: 'Package/namespace' },
    ],
  },
  {
    title: 'Use Case',
    items: [
      { type: 'UML_ACTOR', label: 'Actor', icon: <User className="w-5 h-5" />, description: 'System actor' },
      { type: 'UML_USECASE', label: 'Use Case', icon: <Circle className="w-5 h-5" />, description: 'Use case' },
    ],
  },
];

const bpmnPalette: PaletteSection[] = [
  {
    title: 'Tasks',
    items: [
      { type: 'BPMN_TASK', label: 'Task', icon: <Square className="w-5 h-5" />, description: 'Generic task' },
      { type: 'BPMN_USER_TASK', label: 'User Task', icon: <User className="w-5 h-5" />, description: 'User interaction' },
      { type: 'BPMN_SERVICE_TASK', label: 'Service Task', icon: <Settings className="w-5 h-5" />, description: 'Automated service' },
      { type: 'BPMN_MANUAL_TASK', label: 'Manual Task', icon: <FileText className="w-5 h-5" />, description: 'Manual work' },
      { type: 'BPMN_SCRIPT_TASK', label: 'Script Task', icon: <Code className="w-5 h-5" />, description: 'Script execution' },
    ],
  },
  {
    title: 'Events',
    items: [
      { type: 'BPMN_START_EVENT', label: 'Start Event', icon: <Play className="w-5 h-5" />, description: 'Process start' },
      { type: 'BPMN_END_EVENT', label: 'End Event', icon: <Square className="w-5 h-5" />, description: 'Process end' },
      { type: 'BPMN_INTERMEDIATE_EVENT', label: 'Intermediate Event', icon: <Circle className="w-5 h-5" />, description: 'Mid-process event' },
    ],
  },
  {
    title: 'Gateways',
    items: [
      { type: 'BPMN_GATEWAY_EXCLUSIVE', label: 'Exclusive Gateway', icon: <Diamond className="w-5 h-5" />, description: 'XOR decision' },
      { type: 'BPMN_GATEWAY_PARALLEL', label: 'Parallel Gateway', icon: <GitBranch className="w-5 h-5" />, description: 'AND split/join' },
      { type: 'BPMN_GATEWAY_INCLUSIVE', label: 'Inclusive Gateway', icon: <Diamond className="w-5 h-5" />, description: 'OR decision' },
    ],
  },
  {
    title: 'Swimlanes',
    items: [
      { type: 'BPMN_POOL', label: 'Pool', icon: <Workflow className="w-5 h-5" />, description: 'Process participant' },
    ],
  },
];

const PaletteItemComponent: React.FC<{ item: PaletteItem }> = ({ item }) => {
  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, item.type)}
      className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded cursor-move hover:bg-blue-50 hover:border-blue-300 transition-colors group"
      title={item.description}
    >
      <div className="text-gray-600 group-hover:text-blue-600 transition-colors">
        {item.icon}
      </div>
      <span className="text-sm text-gray-700 group-hover:text-blue-700 transition-colors">
        {item.label}
      </span>
    </div>
  );
};

const PaletteSectionComponent: React.FC<{ section: PaletteSection }> = ({ section }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="mb-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-100 rounded transition-colors"
      >
        <span>{section.title}</span>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
      </button>
      
      {isExpanded && (
        <div className="mt-2 space-y-2">
          {section.items.map((item) => (
            <PaletteItemComponent key={item.type} item={item} />
          ))}
        </div>
      )}
    </div>
  );
};

export const DiagramToolbar: React.FC = () => {
  const diagramType = useDiagramStore((state) => state.diagramType);

  const getPalette = () => {
    if (diagramType === DiagramType.ER) {
      return erPalette;
    } else if (diagramType.startsWith('UML')) {
      return umlPalette;
    } else if (diagramType === DiagramType.BPMN) {
      return bpmnPalette;
    }
    return [];
  };

  const palette = getPalette();

  return (
    <div className="w-64 bg-gray-50 border-r border-gray-200 overflow-y-auto">
      <div className="p-4">
        <h2 className="text-lg font-bold text-gray-800 mb-4">Elements</h2>
        
        <div className="text-xs text-gray-500 mb-4 bg-blue-50 border border-blue-200 rounded p-2">
          💡 Drag elements onto the canvas to add them
        </div>

        {palette.map((section, index) => (
          <PaletteSectionComponent key={index} section={section} />
        ))}
      </div>
    </div>
  );
};
/**
 * Hierarchy View Component
 * Path: frontend/src/components/builder/HierarchyView/HierarchyView.tsx
 * 
 * Tree-structure view of diagram elements grouped by packages
 */

import React, { useMemo } from 'react';
import type { Node } from 'reactflow';
import { COLORS } from '../../../constants/colors';
import type { NodeData } from '../../../types/diagram.types';

interface HierarchyViewProps {
  nodes: Node<NodeData>[];
}

interface PackageGroup {
  packageNode: Node<NodeData>;
  children: Node<NodeData>[];
}

const getNodeIcon = (type: string): string => {
  const icons: Record<string, string> = {
    package: '📦',
    class: '🔷',
    interface: '🔹',
    object: '🔴',
    enumeration: '🟡',
  };
  return icons[type] || '•';
};

export const HierarchyView: React.FC<HierarchyViewProps> = ({ nodes }) => {
  const { packages, orphans } = useMemo(() => {
    const packageNodes = nodes.filter((n) => n.type === 'package');
    const nonPackageNodes = nodes.filter((n) => n.type !== 'package');

    const packages: PackageGroup[] = packageNodes.map((pkg) => ({
      packageNode: pkg,
      children: nonPackageNodes.filter((n) => n.data.parentId === pkg.id),
    }));

    const orphans = nonPackageNodes.filter((n) => !n.data.parentId);

    return { packages, orphans };
  }, [nodes]);

  if (nodes.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-sm" style={{ color: COLORS.DARK_GREY }}>
          No elements yet. Drag elements from the palette to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="font-mono text-sm" style={{ color: COLORS.BLACK }}>
      {/* Root orphans */}
      {orphans.length > 0 && (
        <div className="mb-4">
          <div className="font-bold mb-2" style={{ color: COLORS.DARK_GREY }}>
            / (root)
          </div>
          <div className="ml-4 space-y-1">
            {orphans.map((node) => (
              <div key={node.id} className="py-1">
                <span className="mr-2">{getNodeIcon(node.type || '')}</span>
                <span>{node.data.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Packages with children */}
      {packages.map((pkg) => (
        <div key={pkg.packageNode.id} className="mb-4">
          <div className="font-bold mb-2">
            <span className="mr-2">{getNodeIcon('package')}</span>
            <span>{pkg.packageNode.data.label}</span>
          </div>
          {pkg.children.length > 0 ? (
            <div
              className="ml-4 pl-3 border-l-2 space-y-1"
              style={{ borderColor: COLORS.LIGHT_GREY }}
            >
              {pkg.children.map((child) => (
                <div key={child.id} className="py-1">
                  <span className="mr-2">{getNodeIcon(child.type || '')}</span>
                  <span>{child.data.label}</span>
                  {child.data.stereotype && (
                    <span className="ml-2 text-xs" style={{ color: COLORS.DARK_GREY }}>
                      &lt;&lt;{child.data.stereotype}&gt;&gt;
                    </span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="ml-8 text-xs italic" style={{ color: COLORS.DARK_GREY }}>
              (empty)
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default HierarchyView;
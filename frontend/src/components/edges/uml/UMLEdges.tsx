import React, { memo } from 'react';
import { EdgeProps } from 'reactflow';
import { BaseEdge } from '../base/BaseEdge';

// Association Edge (simple line)
export const AssociationEdge = memo<EdgeProps>((props) => {
  return (
    <BaseEdge
      {...props}
      markerEnd="url(#arrow)"
      label={props.data?.label}
    />
  );
});
AssociationEdge.displayName = 'AssociationEdge';

// Generalization Edge (inheritance - hollow triangle)
export const GeneralizationEdge = memo<EdgeProps>((props) => {
  return (
    <BaseEdge
      {...props}
      markerEnd="url(#triangle)"
      label={props.data?.label}
    />
  );
});
GeneralizationEdge.displayName = 'GeneralizationEdge';

// Dependency Edge (dashed line with arrow)
export const DependencyEdge = memo<EdgeProps>((props) => {
  return (
    <BaseEdge
      {...props}
      strokeDasharray="5,5"
      markerEnd="url(#arrow)"
      label={props.data?.label}
    />
  );
});
DependencyEdge.displayName = 'DependencyEdge';

// Aggregation Edge (hollow diamond)
export const AggregationEdge = memo<EdgeProps>((props) => {
  return (
    <BaseEdge
      {...props}
      markerStart="url(#diamond-hollow)"
      label={props.data?.label}
    />
  );
});
AggregationEdge.displayName = 'AggregationEdge';

// Composition Edge (filled diamond)
export const CompositionEdge = memo<EdgeProps>((props) => {
  return (
    <BaseEdge
      {...props}
      markerStart="url(#diamond-filled)"
      label={props.data?.label}
    />
  );
});
CompositionEdge.displayName = 'CompositionEdge';

// Realization Edge (dashed line with hollow triangle)
export const RealizationEdge = memo<EdgeProps>((props) => {
  return (
    <BaseEdge
      {...props}
      strokeDasharray="5,5"
      markerEnd="url(#triangle)"
      label={props.data?.label}
    />
  );
});
RealizationEdge.displayName = 'RealizationEdge';

// Message Edge (for sequence diagrams)
export const MessageEdge = memo<EdgeProps>((props) => {
  return (
    <BaseEdge
      {...props}
      markerEnd="url(#arrow)"
      label={props.data?.label}
      strokeWidth={2}
    />
  );
});
MessageEdge.displayName = 'MessageEdge';

// Transition Edge (for state machines)
export const TransitionEdge = memo<EdgeProps>((props) => {
  return (
    <BaseEdge
      {...props}
      markerEnd="url(#arrow)"
      label={props.data?.label}
    />
  );
});
TransitionEdge.displayName = 'TransitionEdge';

// Edge Markers (SVG definitions)
export const EdgeMarkers = () => (
  <svg style={{ position: 'absolute', width: 0, height: 0 }}>
    <defs>
      {/* Arrow marker */}
      <marker
        id="arrow"
        viewBox="0 0 10 10"
        refX="9"
        refY="5"
        markerWidth="6"
        markerHeight="6"
        orient="auto-start-reverse"
      >
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280" />
      </marker>

      {/* Triangle marker (for inheritance) */}
      <marker
        id="triangle"
        viewBox="0 0 10 10"
        refX="9"
        refY="5"
        markerWidth="8"
        markerHeight="8"
        orient="auto-start-reverse"
      >
        <path d="M 0 0 L 10 5 L 0 10 z" fill="white" stroke="#6b7280" strokeWidth="1" />
      </marker>

      {/* Hollow diamond (for aggregation) */}
      <marker
        id="diamond-hollow"
        viewBox="0 0 10 10"
        refX="0"
        refY="5"
        markerWidth="8"
        markerHeight="8"
        orient="auto-start-reverse"
      >
        <path d="M 0 5 L 5 0 L 10 5 L 5 10 z" fill="white" stroke="#6b7280" strokeWidth="1" />
      </marker>

      {/* Filled diamond (for composition) */}
      <marker
        id="diamond-filled"
        viewBox="0 0 10 10"
        refX="0"
        refY="5"
        markerWidth="8"
        markerHeight="8"
        orient="auto-start-reverse"
      >
        <path d="M 0 5 L 5 0 L 10 5 L 5 10 z" fill="#6b7280" />
      </marker>
    </defs>
  </svg>
);
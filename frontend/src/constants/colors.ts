/**
 * Semantic Architect Color Palette
 * Path: frontend/src/constants/colors.ts
 * 
 * Strict adherence required per PRD Section 2.1
 * These are the ONLY colors allowed in the application
 */

export const COLORS = {
  // Primary/Action
  PRIMARY: '#0052ea',
  
  // Success/Valid
  SUCCESS: '#059669',
  
  // Error/Delete
  ERROR: '#c71100',
  
  // Warning/Secondary
  WARNING: '#eaa800',
  
  // Text/Borders
  BLACK: '#000000',
  DARK_GREY: '#8c8c8c',
  
  // Backgrounds
  WHITE: '#ffffff',
  OFF_WHITE: '#f7f7f7',
  LIGHT_GREY: '#cccccc',
} as const;

// Element-specific colors based on type
export const ELEMENT_COLORS = {
  package: COLORS.WHITE,
  class: COLORS.SUCCESS,      // #059669 Green
  object: COLORS.ERROR,        // #c71100 Red
  interface: COLORS.PRIMARY,   // #0052ea Blue
  enumeration: COLORS.WARNING, // #eaa800 Yellow
} as const;

// Relationship/Edge colors
export const EDGE_COLORS = {
  association: COLORS.BLACK,
  composition: COLORS.BLACK,
  aggregation: COLORS.BLACK,
  inheritance: COLORS.BLACK,
  dependency: COLORS.DARK_GREY,
  realization: COLORS.DARK_GREY,
} as const;

// Helper to get element color with fallback
export const getElementColor = (elementType: string): string => {
  return ELEMENT_COLORS[elementType as keyof typeof ELEMENT_COLORS] || COLORS.BLACK;
};

// Helper to get element border color (always black except package)
export const getElementBorderColor = (elementType: string): string => {
  return elementType === 'package' ? COLORS.BLACK : COLORS.BLACK;
};

// Helper to get text color (white for dark backgrounds, black for light)
export const getTextColor = (backgroundColor: string): string => {
  // For our palette, only package (white) needs black text
  // All others (green, red, blue, yellow) need white text for contrast
  return backgroundColor === COLORS.WHITE ? COLORS.BLACK : COLORS.WHITE;
};
/**
 * Tailwind CSS Configuration
 * Path: frontend/tailwind.config.js
 */

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Semantic Architect color palette
        'sa': {
          primary: '#0052ea',      // Blue - Primary/Action
          success: '#059669',      // Green - Success/Valid
          error: '#c71100',        // Red - Error/Delete
          warning: '#eaa800',      // Yellow - Warning/Secondary
          black: '#000000',        // Black - Text
          grey: '#8c8c8c',         // Dark Grey - Borders
          white: '#ffffff',        // White - Background
          'off-white': '#f7f7f7',  // Off-white - Alt Background
          'light-grey': '#cccccc', // Light Grey
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['Fira Code', 'Monaco', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
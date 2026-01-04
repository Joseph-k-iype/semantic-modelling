/**
 * Model Card Component
 * Path: frontend/src/components/cards/ModelCard/ModelCard.tsx
 * 
 * Displays a published model on the homepage with statistics
 */

import React from 'react';
import { COLORS } from '../../../constants/colors';

interface ModelCardProps {
  name: string;
  workspace?: string;
  author?: string;
  totalClasses: number;
  totalRelationships: number;
  onClick?: () => void;
  className?: string;
}

export const ModelCard: React.FC<ModelCardProps> = ({
  name,
  workspace,
  author,
  totalClasses,
  totalRelationships,
  onClick,
  className = '',
}) => {
  return (
    <div
      onClick={onClick}
      className={`rounded-lg shadow-sm border-2 transition-all cursor-pointer hover:shadow-md hover:border-opacity-80 ${className}`}
      style={{ 
        backgroundColor: COLORS.WHITE,
        borderColor: COLORS.LIGHT_GREY
      }}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && onClick) {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <div className="p-6">
        {/* Icon and Title */}
        <div className="flex items-start gap-4 mb-4">
          {/* Blue square icon */}
          <div
            className="w-12 h-12 rounded flex-shrink-0"
            style={{ backgroundColor: COLORS.PRIMARY }}
            aria-hidden="true"
          />
          <div className="flex-1 min-w-0">
            <h3 
              className="font-semibold text-lg truncate mb-1" 
              style={{ color: COLORS.BLACK }}
              title={name}
            >
              {name}
            </h3>
            {workspace && (
              <p 
                className="text-sm truncate" 
                style={{ color: COLORS.DARK_GREY }}
                title={workspace}
              >
                {workspace}
              </p>
            )}
            {author && (
              <p 
                className="text-xs truncate mt-1" 
                style={{ color: COLORS.DARK_GREY }}
                title={`Author: ${author}`}
              >
                by {author}
              </p>
            )}
          </div>
        </div>

        {/* Divider */}
        <hr 
          className="my-4" 
          style={{ borderColor: COLORS.LIGHT_GREY }} 
        />

        {/* Statistics */}
        <div 
          className="flex justify-between text-sm" 
          style={{ color: COLORS.DARK_GREY }}
        >
          <span>
            <strong style={{ color: COLORS.BLACK }}>{totalClasses}</strong> Classes
          </span>
          <span>
            <strong style={{ color: COLORS.BLACK }}>{totalRelationships}</strong> Relationships
          </span>
        </div>
      </div>
    </div>
  );
};

export default ModelCard;
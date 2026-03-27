import type { Tag } from '../types/tag';

interface TagChipProps {
  tag: Tag;
  onRemove?: () => void;
  showUsage?: boolean;
  usageCount?: number;
}

export const TagChip: React.FC<TagChipProps> = ({
  tag, onRemove, showUsage = false, usageCount = 0
}) => {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-50 text-purple-700 rounded-full text-xs">
      #{tag.name}
      {showUsage && <span className="text-purple-500">({usageCount})</span>}
      {onRemove && (
        <button onClick={onRemove} className="ml-1 text-purple-400 hover:text-purple-600">
          ×
        </button>
      )}
    </span>
  );
};
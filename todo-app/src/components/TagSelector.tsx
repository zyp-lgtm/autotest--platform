import { useState } from 'react';
import type { Tag } from '../types/tag';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { Button } from './ui/button';
import { useTranslation } from '../hooks/useTranslation';

interface TagSelectorProps {
  tags: Tag[];
  selectedIds: number[];
  onChange: (ids: number[]) => void;
}

export const TagSelector: React.FC<TagSelectorProps> = ({
  tags, selectedIds, onChange
}) => {
  const { getText } = useTranslation();
  const [open, setOpen] = useState(false);
  const selectedTags = tags.filter(t => selectedIds.includes(t.id));

  const toggleTag = (tagId: number) => {
    if (selectedIds.includes(tagId)) {
      onChange(selectedIds.filter(id => id !== tagId));
    } else {
      onChange([...selectedIds, tagId]);
    }
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button type="button" variant="outline" className="h-9 px-3 py-2 border-2 border-gray-200 rounded-lg text-sm min-w-[100px]">
          {selectedTags.length > 0 ? selectedTags.map(t => `#${t.name}`).join(' ') : getText('input', 'addTag')}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-3" align="start">
        <div className="space-y-2">
          <p className="text-sm font-medium">{getText('tag', 'title')}</p>
          {tags.length === 0 ? <p className="text-xs text-gray-500">暂无标签</p> : (
            <div className="space-y-1">
              {tags.map(tag => (
                <label key={tag.id} className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer">
                  <input type="checkbox" checked={selectedIds.includes(tag.id)} onChange={() => toggleTag(tag.id)} className="w-4 h-4 rounded border-gray-300" />
                  <span className="text-sm">#{tag.name}</span>
                </label>
              ))}
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
};
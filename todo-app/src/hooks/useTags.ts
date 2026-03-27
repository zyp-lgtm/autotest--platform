import { useState, useEffect } from 'react';
import type { Tag, CreateTagInput, UpdateTagInput } from '../types/tag';
import { tagStorage } from '../utils/storage-tags';

export const useTags = () => {
  const [tags, setTags] = useState<Tag[]>([]);

  useEffect(() => {
    const loaded = tagStorage.getTags();
    setTags(loaded);
  }, []);

  useEffect(() => {
    tagStorage.saveTags(tags);
  }, [tags]);

  const addTag = (input: CreateTagInput) => {
    const newTag: Tag = {
      id: Date.now(),
      ...input,
      createdAt: new Date().toISOString()
    };
    setTags(prev => [...prev, newTag]);
  };

  const updateTag = (id: number, input: UpdateTagInput) => {
    setTags(prev =>
      prev.map(tag =>
        tag.id === id ? { ...tag, ...input } : tag
      )
    );
  };

  const deleteTag = (id: number) => {
    setTags(prev => prev.filter(tag => tag.id !== id));
  };

  const getTag = (id: number): Tag | undefined => {
    return tags.find(t => t.id === id);
  };

  const getTagsByIds = (ids: number[]): Tag[] => {
    return ids.map(id => tags.find(t => t.id === id)).filter((t): t is Tag => t !== undefined);
  };

  const getTagUsageCount = (tagId: number, tasks: { tagIds: number[] }[]): number => {
    return tasks.filter(task => task.tagIds.includes(tagId)).length;
  };

  return {
    tags,
    addTag,
    updateTag,
    deleteTag,
    getTag,
    getTagsByIds,
    getTagUsageCount
  };
};
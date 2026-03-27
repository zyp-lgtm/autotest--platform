import type { Tag } from '../types/tag';

const TAGS_STORAGE_KEY = 'todo-tags';

export const tagStorage = {
  // 获取所有标签
  getTags: (): Tag[] => {
    try {
      const stored = localStorage.getItem(TAGS_STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  },

  // 保存标签列表
  saveTags: (tags: Tag[]): void => {
    localStorage.setItem(TAGS_STORAGE_KEY, JSON.stringify(tags));
  }
};
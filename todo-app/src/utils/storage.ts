import type { Task } from '../types/task';
import { STORAGE_KEY } from '../constants/priorities';

export const storage = {
  getTasks: (): Task[] => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  },

  saveTasks: (tasks: Task[]): void => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
  }
};

// 导出项目和标签存储
export { projectStorage, DEFAULT_PROJECT } from './storage-projects';
export { tagStorage } from './storage-tags';

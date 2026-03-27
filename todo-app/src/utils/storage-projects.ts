import type { Project } from '../types/project';

const PROJECTS_STORAGE_KEY = 'todo-projects';

// 默认项目
export const DEFAULT_PROJECT: Project = {
  id: 1,
  name: '未分类',
  icon: '📁',
  description: '默认项目，未分配项目的任务',
  createdAt: new Date().toISOString()
};

export const projectStorage = {
  // 获取所有项目
  getProjects: (): Project[] => {
    try {
      const stored = localStorage.getItem(PROJECTS_STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
      // 如果没有存储，初始化默认项目
      const projects = [DEFAULT_PROJECT];
      projectStorage.saveProjects(projects);
      return projects;
    } catch {
      // 发生错误时返回默认项目
      return [DEFAULT_PROJECT];
    }
  },

  // 保存项目列表
  saveProjects: (projects: Project[]): void => {
    localStorage.setItem(PROJECTS_STORAGE_KEY, JSON.stringify(projects));
  },

  // 获取默认项目 ID
  getDefaultProjectId: (): number => {
    return DEFAULT_PROJECT.id;
  },

  // 检查是否为默认项目
  isDefaultProject: (projectId: number): boolean => {
    return projectId === DEFAULT_PROJECT.id;
  }
};
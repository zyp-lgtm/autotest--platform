export type Priority = 'high' | 'medium' | 'low';

export interface Task {
  id: number;
  text: string;
  completed: boolean;
  priority: Priority;
  dueDate: string | null;
  projectId: number;        // 新增
  tagIds: number[];         // 新增
  createdAt: string;
}

export interface PriorityConfig {
  label: string;
  emoji: string;
  value: number;
  color: string;
}

export type FilterType = 'all' | 'active' | 'completed';
export type SortType = 'created' | 'priority' | 'dueDate';

// 新增：项目筛选类型
export type ProjectFilterType = number | 'all';
// 新增：标签筛选类型（支持多选）
export type TagFilterType = number[] | 'all';

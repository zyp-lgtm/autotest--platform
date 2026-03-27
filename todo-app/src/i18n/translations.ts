export type Language = 'zh' | 'en';

export interface Translations {
  app: {
    title: string;
  };
  input: {
    placeholder: string;
    priority: string;
    dueDate: string;
    add: string;
    priorityHigh: string;
    priorityMedium: string;
    priorityLow: string;
    project: string;
    selectProject: string;
    addTag: string;
  };
  filters: {
    all: string;
    active: string;
    completed: string;
    allProjects: string;
    allTags: string;
  };
  sort: {
    label: string;
    byCreated: string;
    byPriority: string;
    byDueDate: string;
  };
  stats: {
    activeTasks: string;
    overdueTasks: string;
    clearCompleted: string;
    expired: string;
  };
  project: {
    title: string;
    unclassified: string;
    taskCount: string;
  };
  tag: {
    title: string;
    usageCount: string;
  };
  management: {
    title: string;
    projectsTab: string;
    tagsTab: string;
  };
}

export const translations: Record<Language, Translations> = {
  zh: {
    app: {
      title: '📝 待办事项'
    },
    input: {
      placeholder: '添加新任务...',
      priority: '优先级:',
      dueDate: '截止日期:',
      add: '添加',
      priorityHigh: '🔴 高',
      priorityMedium: '🟡 中',
      priorityLow: '🟢 低',
      project: '项目:',
      selectProject: '请选择项目',
      addTag: '+ 标签'
    },
    filters: {
      all: '全部',
      active: '进行中',
      completed: '已完成',
      allProjects: '📋 所有项目',
      allTags: '# 所有标签'
    },
    sort: {
      label: '排序:',
      byCreated: '创建时间',
      byPriority: '优先级',
      byDueDate: '截止日期'
    },
    stats: {
      activeTasks: '个待完成任务',
      overdueTasks: '个已过期',
      clearCompleted: '清除已完成',
      expired: '已过期'
    },
    project: {
      title: '项目',
      unclassified: '未分类',
      taskCount: '{count} 个任务'
    },
    tag: {
      title: '标签',
      usageCount: '{count} 次使用'
    },
    management: {
      title: '管理',
      projectsTab: '项目管理',
      tagsTab: '标签管理'
    }
  },
  en: {
    app: {
      title: '📝 Todo List'
    },
    input: {
      placeholder: 'Add new task...',
      priority: 'Priority:',
      dueDate: 'Due Date:',
      add: 'Add',
      priorityHigh: '🔴 High',
      priorityMedium: '🟡 Medium',
      priorityLow: '🟢 Low',
      project: 'Project:',
      selectProject: 'Select project',
      addTag: '+ Tags'
    },
    filters: {
      all: 'All',
      active: 'Active',
      completed: 'Completed',
      allProjects: '📋 All Projects',
      allTags: '# All Tags'
    },
    sort: {
      label: 'Sort:',
      byCreated: 'Created',
      byPriority: 'Priority',
      byDueDate: 'Due Date'
    },
    stats: {
      activeTasks: 'active tasks',
      overdueTasks: 'overdue',
      clearCompleted: 'Clear Completed',
      expired: 'Expired'
    },
    project: {
      title: 'Project',
      unclassified: 'Uncategorized',
      taskCount: '{count} tasks'
    },
    tag: {
      title: 'Tag',
      usageCount: '{count} uses'
    },
    management: {
      title: 'Manage',
      projectsTab: 'Projects',
      tagsTab: 'Tags'
    }
  }
};

const LANGUAGE_STORAGE_KEY = 'todo-language';

export const getSavedLanguage = (): Language => {
  const saved = localStorage.getItem(LANGUAGE_STORAGE_KEY);
  if (saved === 'zh' || saved === 'en') {
    return saved;
  }
  return 'zh'; // 默认中文
};

export const saveLanguage = (language: Language) => {
  localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
};
